const sarFormatter = new Intl.NumberFormat("en-SA", {
  style: "currency",
  currency: "SAR",
  maximumFractionDigits: 0,
});
const commercialAmountFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 3,
  maximumFractionDigits: 3,
});

export function formatCurrency(value: number) {
  return sarFormatter.format(value);
}

export function formatCompactCurrency(value: number) {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M SAR`;
  }

  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K SAR`;
  }

  return `${value} SAR`;
}

export function formatDate(isoDate?: string) {
  if (!isoDate) {
    return "Pending";
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(isoDate));
}

export function formatDateTime(isoDateTime?: string) {
  if (!isoDateTime) {
    return "Pending";
  }

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(isoDateTime));
}

export function formatPercent(value: number) {
  return `${Math.round(value)}%`;
}

export function formatCommercialAmount(
  value: number | string | null | undefined,
) {
  if (value === null || value === undefined || value === "") {
    return "";
  }

  const numericValue =
    typeof value === "number" ? value : Number(String(value).replace(/,/g, "").trim());

  if (!Number.isFinite(numericValue)) {
    return String(value);
  }

  return commercialAmountFormatter.format(numericValue);
}

export function formatCommercialAmountWithCurrency(
  value: number | string | null | undefined,
  currencyCode?: string | null,
) {
  const formattedAmount = formatCommercialAmount(value);
  if (!formattedAmount) {
    return "";
  }

  return `${(currencyCode ?? "SAR").trim() || "SAR"} ${formattedAmount}`;
}
