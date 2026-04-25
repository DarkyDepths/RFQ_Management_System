import { Suspense } from "react";

import { RFQListScreen } from "@/components/rfq/RFQListScreen";

export default function RfqsPage() {
  return (
    <Suspense fallback={null}>
      <RFQListScreen />
    </Suspense>
  );
}
