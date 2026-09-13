export type ChatType = "general_query" | "new_report" | "update_report";

export type PaymentCategory = {
  id: string;
  label: string;
};

export const PAYMENT_CATEGORIES: PaymentCategory[] = [
  { id: "UPI", label: "UPI / BHIM" },
  { id: "IMPS", label: "IMPS" },
  { id: "NEFT_RTGS", label: "NEFT / RTGS" },
  { id: "CTS", label: "CTS / Cheques" },
  { id: "AEPS", label: "AEPS" },
  { id: "EKYC", label: "e-KYC" },
  { id: "NFS", label: "NFS / ATM" },
  { id: "NPCI", label: "RuPay / NACH" },
  { id: "RBI_MD", label: "RBI master directions" },
  { id: "CRYPTO_VA", label: "Crypto / VDA" },
  { id: "FX_FEMA", label: "FX / FEMA" },
  { id: "GENERAL", label: "General payments" },
];

export type ChatSessionConfig = {
  chatType: ChatType;
  selectedCategories: string[];
  shapEnabled: boolean;
  semanticMlEnabled: boolean;
  categoryMode: "selected" | "unsure" | "none";
};

export const DEFAULT_CHAT_CONFIG: ChatSessionConfig = {
  chatType: "general_query",
  selectedCategories: [],
  shapEnabled: false,
  semanticMlEnabled: false,
  categoryMode: "unsure",
};

export function defaultSemanticMlForChatType(chatType: ChatType): boolean {
  return chatType === "new_report" || chatType === "update_report";
}

export function defaultShapForChatType(chatType: ChatType): boolean {
  return chatType === "new_report" || chatType === "update_report";
}
