"use client";

import { useEffect, useState } from "react";

import { getRfqDetail } from "@/connectors/manager/rfqs";
import type { RfqDetailModel } from "@/models/manager/rfq";

interface DetailState {
  error: string | null;
  loading: boolean;
  rfq: RfqDetailModel | null;
}

export function useRfqDetail(rfqId: string) {
  const [reloadKey, setReloadKey] = useState(0);
  const [state, setState] = useState<DetailState>({
    error: null,
    loading: true,
    rfq: null,
  });

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const rfq = await getRfqDetail(rfqId);

        if (!active) {
          return;
        }

        setState({
          error: rfq ? null : "The requested RFQ was not found.",
          loading: false,
          rfq,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          error:
            error instanceof Error
              ? error.message
              : "RFQ detail could not be loaded.",
          loading: false,
          rfq: null,
        });
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [reloadKey, rfqId]);

  return {
    ...state,
    refresh: () => setReloadKey((value) => value + 1),
  };
}
