import { RFQDetailScreen } from "@/components/rfq/RFQDetailScreen";

export default function RfqDetailPage({
  params,
}: {
  params: {
    rfqId: string;
  };
}) {
  return <RFQDetailScreen rfqId={params.rfqId} />;
}
