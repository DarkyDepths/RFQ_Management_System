export function getRfqBusinessIdentity(
  rfq: {
    rfqCode?: string;
    title?: string;
  },
  fallback = "RFQ Detail",
) {
  const code = rfq.rfqCode?.trim();
  if (code) {
    return code;
  }

  const title = rfq.title?.trim();
  if (title) {
    return title;
  }

  return fallback;
}
