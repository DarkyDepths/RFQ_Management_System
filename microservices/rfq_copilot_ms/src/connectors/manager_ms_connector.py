"""rfq_manager_ms HTTP connector — operational truth.

Sync httpx client (matches the rest of the service's sync pattern).
Sends X-Debug-* headers carrying the copilot's Actor so manager attributes
the request to the actual user instead of its own bypass actor. (Note:
manager honors these headers ONLY when ``AUTH_BYPASS_ENABLED=true`` AND
``AUTH_BYPASS_DEBUG_HEADERS_ENABLED=true``; see SLICE_1_APP_TESTING.md.)

Lookup methods come in pairs:

* ``get_rfq_detail(rfq_id, actor)`` — by UUID, hits ``/rfqs/{uuid}``.
  Used by /v1 (frontend always sends UUIDs) and any caller that
  already resolved a UUID upstream.
* ``get_rfq_detail_by_code(rfq_code, actor)`` — by human-readable code
  (e.g. ``IF-0001``), hits ``/rfqs/by-code/{code}``. Used by the v2
  Path 4 chain when the planner extracted a code from the user message.
  Same DTO returned. (Batch 9.1 — manager-side endpoint shipped in PR-A.)

Same pairing for ``get_rfq_stages`` / ``get_rfq_stages_by_code``.

Failure mapping (Batch 9.1 refines the auth distinctions):

- network / timeout         -> ManagerUnreachable
- 404                       -> RfqNotFound
- 401 (auth misconfigured)  -> ManagerAuthFailed (distinct so the
                               orchestrator can route to a clearer
                               operator-facing template than "source
                               is down". Treated as a deployment bug
                               worth its own reason_code.)
- 403 (lacks permission)    -> RfqAccessDenied (routed to Path 8.4
                               by the access stage; not 8.5 — this
                               is "you can't see this RFQ", not
                               "the RFQ source is down")
- other non-2xx             -> ManagerUnreachable (with status code)
- 2xx but unparseable       -> ManagerUnreachable
"""

from __future__ import annotations

import logging

import httpx

from src.config.settings import settings
from src.models.actor import Actor
from src.models.manager_dto import (
    ManagerPortfolioStatsDto,
    ManagerRfqDetailDto,
    ManagerRfqListItemDto,
    ManagerRfqStageDto,
)
from src.utils.errors import (
    ManagerAuthFailed,
    ManagerUnreachable,
    RfqAccessDenied,
    RfqNotFound,
)


logger = logging.getLogger(__name__)

_MANAGER_API_PATH = "/rfq-manager/v1"


class ManagerConnector:
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 5.0):
        self._base_url = (base_url or settings.MANAGER_BASE_URL).rstrip("/")
        self._timeout = timeout_seconds

    # ── By-UUID endpoints (existing, unchanged callers) ─────────────────────

    def get_rfq_detail(self, rfq_id: str, actor: Actor) -> ManagerRfqDetailDto:
        url = self._url(f"/rfqs/{rfq_id}")
        response = self._get(url, actor)
        if response.status_code == 404:
            raise RfqNotFound(f"RFQ '{rfq_id}' not found in manager")
        self._raise_for_unexpected(response, context=f"GET {url}")
        try:
            return ManagerRfqDetailDto.model_validate(response.json())
        except Exception as exc:
            raise ManagerUnreachable(
                f"Manager returned an unparseable RFQ detail payload: {exc}"
            ) from exc

    def get_rfq_stages(self, rfq_id: str, actor: Actor) -> list[ManagerRfqStageDto]:
        url = self._url(f"/rfqs/{rfq_id}/stages")
        response = self._get(url, actor)
        if response.status_code == 404:
            raise RfqNotFound(f"RFQ '{rfq_id}' not found in manager (stages)")
        self._raise_for_unexpected(response, context=f"GET {url}")
        try:
            payload = response.json()
            data = payload.get("data", []) if isinstance(payload, dict) else []
            return [ManagerRfqStageDto.model_validate(item) for item in data]
        except Exception as exc:
            raise ManagerUnreachable(
                f"Manager returned an unparseable stages payload: {exc}"
            ) from exc

    # ── By-code endpoints (Batch 9.1 — manager PR-A ships these) ────────────

    def get_rfq_detail_by_code(
        self, rfq_code: str, actor: Actor,
    ) -> ManagerRfqDetailDto:
        """Fetch RFQ detail by human-readable code (e.g. ``IF-0001``).

        Same DTO + same failure mapping as ``get_rfq_detail``. Used by
        the Path 4 access stage when the planner extracted a code
        rather than a UUID — avoids a 422 from the by-id route's
        UUID coercion.
        """
        url = self._url(f"/rfqs/by-code/{rfq_code}")
        response = self._get(url, actor)
        if response.status_code == 404:
            raise RfqNotFound(f"RFQ with code '{rfq_code}' not found in manager")
        self._raise_for_unexpected(response, context=f"GET {url}")
        try:
            return ManagerRfqDetailDto.model_validate(response.json())
        except Exception as exc:
            raise ManagerUnreachable(
                f"Manager returned an unparseable RFQ detail payload: {exc}"
            ) from exc

    def get_rfq_stages_by_code(
        self, rfq_code: str, actor: Actor,
    ) -> list[ManagerRfqStageDto]:
        """Fetch stages for an RFQ by its code. Same shape + mapping as
        ``get_rfq_stages``."""
        url = self._url(f"/rfqs/by-code/{rfq_code}/stages")
        response = self._get(url, actor)
        if response.status_code == 404:
            raise RfqNotFound(
                f"RFQ with code '{rfq_code}' not found in manager (stages)"
            )
        self._raise_for_unexpected(response, context=f"GET {url}")
        try:
            payload = response.json()
            data = payload.get("data", []) if isinstance(payload, dict) else []
            return [ManagerRfqStageDto.model_validate(item) for item in data]
        except Exception as exc:
            raise ManagerUnreachable(
                f"Manager returned an unparseable stages payload: {exc}"
            ) from exc

    # ── General-mode (portfolio) endpoints ──────────────────────────────────

    def get_portfolio_stats(self, actor: Actor) -> ManagerPortfolioStatsDto:
        url = self._url("/rfqs/stats")
        response = self._get(url, actor)
        self._raise_for_unexpected(response, context=f"GET {url}")
        try:
            return ManagerPortfolioStatsDto.model_validate(response.json())
        except Exception as exc:
            raise ManagerUnreachable(
                f"Manager returned an unparseable stats payload: {exc}"
            ) from exc

    def list_rfqs(
        self,
        actor: Actor,
        size: int = 20,
        sort: str = "deadline",
        statuses: list[str] | None = None,
    ) -> list[ManagerRfqListItemDto]:
        # Bound size defensively (manager caps at 100 anyway).
        bounded_size = max(1, min(size, 100))
        url = self._url("/rfqs")
        params: dict[str, object] = {"size": bounded_size, "sort": sort}
        if statuses:
            params["status"] = statuses  # httpx renders list as repeated query param
        response = self._get(url, actor, params=params)
        self._raise_for_unexpected(response, context=f"GET {url}")
        try:
            payload = response.json()
            data = payload.get("data", []) if isinstance(payload, dict) else []
            return [ManagerRfqListItemDto.model_validate(item) for item in data]
        except Exception as exc:
            raise ManagerUnreachable(
                f"Manager returned an unparseable rfqs list payload: {exc}"
            ) from exc

    # ── Internals ───────────────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self._base_url}{_MANAGER_API_PATH}{path}"

    def _get(
        self,
        url: str,
        actor: Actor,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        try:
            return httpx.get(
                url,
                params=params,
                headers=self._actor_headers(actor),
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise ManagerUnreachable(
                f"Manager request timed out after {self._timeout}s"
            ) from exc
        except httpx.RequestError as exc:
            raise ManagerUnreachable(
                f"Could not reach manager service: {exc}"
            ) from exc

    @staticmethod
    def _actor_headers(actor: Actor) -> dict[str, str]:
        # X-Debug-* headers are honored by manager when AUTH_BYPASS_DEBUG_HEADERS_ENABLED=true.
        # If manager has them disabled, it silently falls back to its own bypass actor —
        # safe either way. No real auth in Batch 4.
        return {
            "X-Debug-User-Id": actor.user_id,
            "X-Debug-User-Name": actor.display_name,
        }

    @staticmethod
    def _raise_for_unexpected(response: httpx.Response, context: str) -> None:
        """Map non-2xx (and non-explicit-404) responses to typed errors.

        Per Batch 9.1 audit:
        * 401 -> ``ManagerAuthFailed``: copilot's bearer/auth-bypass
          headers aren't accepted. This is a deployment-config issue,
          NOT "the data source is down". Distinct so the orchestrator
          can route to a clearer Path 8.5 reason_code.
        * 403 -> ``RfqAccessDenied``: the actor authenticated but
          isn't permitted to read this RFQ. Routed to Path 8.4 by
          the access stage — never Path 8.5.
        * Other non-2xx -> ``ManagerUnreachable`` (existing behavior).

        404 is handled by callers BEFORE invoking this helper, since
        the not-found semantics differ between detail/stages/list
        endpoints.
        """
        if 200 <= response.status_code < 300:
            return
        if response.status_code == 401:
            raise ManagerAuthFailed(
                f"Manager rejected the copilot's auth (HTTP 401) for {context}. "
                f"This is a deployment misconfiguration — verify the manager's "
                f"AUTH_BYPASS settings or the copilot's service token."
            )
        if response.status_code == 403:
            raise RfqAccessDenied(
                f"Manager forbade access (HTTP 403) for {context}"
            )
        raise ManagerUnreachable(
            f"Manager returned HTTP {response.status_code} for {context}"
        )
