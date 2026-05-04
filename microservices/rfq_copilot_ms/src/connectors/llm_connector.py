"""LLM connector — Azure OpenAI GPT-4o client.

Sync wrapper around the official `openai` package's AzureOpenAI client.
``complete(messages, max_tokens, response_format, temperature)``
returns the assistant text content as a string. Token usage is logged
but never returned through the API surface (the rest of the service
shouldn't depend on counts).

``response_format``: optional. When passed (typically a JSON-schema
dict shaped like Azure's ``{"type": "json_schema", "json_schema": {...}}``)
the model is constrained to emit JSON matching that schema. Used by
the Planner / Compose / Judge stages to remove an entire class of
"model dropped a required field" failures (Batch 9.1 fix).

``temperature``: optional. When passed, propagated to Azure. Stages
with strict-format requirements (Planner) pass 0.0 to maximize
determinism. Without this parameter the model used the Azure default
(~1.0), which contributed to schema-mismatch flakiness.

Failure mapping:
- openai.APIError (incl. AuthenticationError, APIConnectionError,
  APITimeoutError, NotFoundError) -> LlmUnreachable
- empty response content                                  -> LlmUnreachable
- any other exception during the call                     -> LlmUnreachable

Sensitive values (API key, endpoint) are NEVER logged or included in
error messages. Errors surface only the failure class and a generic
hint, never the credential.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from openai import APIError, AzureOpenAI

from src.config.settings import settings
from src.utils.errors import LlmUnreachable


logger = logging.getLogger(__name__)


class LlmConnector:
    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        api_version: str | None = None,
        deployment: str | None = None,
        timeout_seconds: float | None = None,
    ):
        # Explicit `None` falls back to settings; explicit `""` is kept (and will fail validation below).
        self._api_key = api_key if api_key is not None else settings.AZURE_OPENAI_API_KEY
        self._endpoint = endpoint if endpoint is not None else settings.AZURE_OPENAI_ENDPOINT
        self._api_version = api_version if api_version is not None else settings.AZURE_OPENAI_API_VERSION
        self._deployment = deployment if deployment is not None else settings.AZURE_OPENAI_CHAT_DEPLOYMENT
        self._timeout = timeout_seconds if timeout_seconds is not None else settings.AZURE_OPENAI_TIMEOUT_SECONDS

        if not self._api_key or not self._endpoint or not self._deployment:
            raise LlmUnreachable(
                "Azure OpenAI configuration is incomplete (missing endpoint, "
                "API key, or chat deployment)."
            )

        self._client = AzureOpenAI(
            api_key=self._api_key,
            azure_endpoint=self._endpoint,
            api_version=self._api_version,
        )

    def complete(
        self,
        messages: Iterable[dict[str, str]],
        max_tokens: int = 500,
        *,
        response_format: dict[str, Any] | None = None,
        temperature: float | None = None,
    ) -> str:
        """Issue one chat-completion call.

        ``response_format`` (Batch 9.1) — when non-None, passed through
        to Azure to enforce a JSON shape on the response. Stages that
        require strict JSON (Planner / Compose / Judge) pass their
        registered schema; free-form callers (v1 grounded reply
        services) leave it None.

        ``temperature`` (Batch 9.1) — when non-None, passed through to
        Azure. The Planner uses 0.0 (deterministic classification);
        Compose uses ~0.3 (mild creativity); Judge uses 0.0 (strict
        verdict). When None, Azure's default (~1.0) is used.
        """
        kwargs: dict[str, Any] = {
            "model": self._deployment,
            "messages": list(messages),
            "max_tokens": max_tokens,
            "timeout": self._timeout,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        if temperature is not None:
            kwargs["temperature"] = temperature

        try:
            response = self._client.chat.completions.create(**kwargs)
        except APIError as exc:
            # Log the exception MESSAGE (not just the class name) so an
            # operator can tell apart "deployment not found" from
            # "auth rejected" from "model doesn't support response_format".
            # Azure error bodies don't contain credentials.
            logger.warning(
                "Azure OpenAI request failed: %s: %s",
                exc.__class__.__name__,
                str(exc)[:500],
            )
            raise LlmUnreachable(
                f"Azure OpenAI request failed ({exc.__class__.__name__})."
            ) from exc
        except Exception as exc:
            logger.warning(
                "Unexpected Azure OpenAI failure: %s: %s",
                exc.__class__.__name__,
                str(exc)[:500],
            )
            raise LlmUnreachable(
                f"Unexpected Azure OpenAI failure ({exc.__class__.__name__})."
            ) from exc

        if not response.choices or not response.choices[0].message.content:
            raise LlmUnreachable("Azure OpenAI returned an empty response.")

        usage = getattr(response, "usage", None)
        if usage is not None:
            logger.info(
                "llm.complete deployment=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
                self._deployment,
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )

        return response.choices[0].message.content.strip()
