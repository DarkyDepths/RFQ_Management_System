import { RFQDetailScreen } from "@/components/rfq/RFQDetailScreen";

export default async function RfqDetailPage({
  params,
}: {
  params: Promise<{ rfqId: string }>;
}) {
  const { rfqId } = await params;
  return <RFQDetailScreen rfqId={rfqId} />;
}
