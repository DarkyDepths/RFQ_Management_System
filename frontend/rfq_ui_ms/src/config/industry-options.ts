export const OTHER_INDUSTRY_OPTION = "Other";
export const DEFAULT_INDUSTRY_OPTION = "Industrial Systems";

export const industryOptions = [
  "Oil & Gas",
  "Petrochemical",
  "Power",
  "Water",
  "Industrial Systems",
  "Mining & Metals",
  "Marine / Offshore",
  "Infrastructure",
  "Manufacturing",
  OTHER_INDUSTRY_OPTION,
] as const;

export type IndustryOption = (typeof industryOptions)[number];

export interface IndustrySelectionState {
  customValue: string;
  selectedOption: IndustryOption;
}

export function resolveIndustrySelection(
  value?: string | null,
  fallbackOption: IndustryOption = DEFAULT_INDUSTRY_OPTION,
): IndustrySelectionState {
  const normalizedValue = value?.trim() ?? "";

  if (!normalizedValue) {
    return {
      customValue: "",
      selectedOption: fallbackOption,
    };
  }

  const matchingOption = industryOptions.find(
    (option) => option.toLowerCase() === normalizedValue.toLowerCase(),
  );

  if (matchingOption && matchingOption !== OTHER_INDUSTRY_OPTION) {
    return {
      customValue: "",
      selectedOption: matchingOption,
    };
  }

  return {
    customValue: normalizedValue,
    selectedOption: OTHER_INDUSTRY_OPTION,
  };
}

export function resolveIndustryValue(
  selectedOption: IndustryOption,
  customValue: string,
): string {
  return selectedOption === OTHER_INDUSTRY_OPTION
    ? customValue.trim()
    : selectedOption;
}
