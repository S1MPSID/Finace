import { htmlToPlainText, plainToPreviewHtml } from "@/lib/text/htmlToPlain";

export function isHtmlContent(value: string): boolean {
  return /<[a-z][\s\S]*>/i.test(value);
}

/** Render AI explanation / clause text without showing raw tags. */
export function toDisplayHtml(value: string): string {
  if (!value) return "";
  if (isHtmlContent(value)) return value;
  return plainToPreviewHtml(value);
}

export function toDisplayText(value: string): string {
  return htmlToPlainText(value);
}
