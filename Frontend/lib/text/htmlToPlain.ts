/** Strip HTML / chat markup for editable plain-text fields. */
export function htmlToPlainText(html: string): string {
  if (!html) return "";

  let text = String(html)
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>\s*/gi, "\n\n")
    .replace(/<p[^>]*>/gi, "")
    .replace(/<li[^>]*>/gi, "\n• ")
    .replace(/<\/li>/gi, "\n")
    .replace(/<\/[ou]l>/gi, "\n")
    .replace(/<\/?[a-z][^>]*>/gi, "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/^#{1,3}\s+/gm, "");

  return text
    .split("\n")
    .map((line) => line.replace(/\s+$/g, "").trimEnd())
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Convert stored string or string[] fields to editable plain lines. */
export function plainLinesFromField(value: string | string[] | null | undefined): string {
  if (!value) return "";
  if (Array.isArray(value)) {
    return value.map((item) => htmlToPlainText(String(item))).filter(Boolean).join("\n");
  }
  return htmlToPlainText(String(value));
}

/** Light markdown → HTML for read-only previews. */
export function plainToPreviewHtml(text: string): string {
  if (!text) return "";
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return escaped
    .replace(/^### (.+)$/gm, "<h4 class='font-semibold text-white mt-4 mb-1'>$1</h4>")
    .replace(/^## (.+)$/gm, "<h4 class='font-semibold text-white mt-4 mb-1'>$1</h4>")
    .replace(/\*\*(.+?)\*\*/g, "<strong class='text-white/90'>$1</strong>")
    .replace(/\n/g, "<br/>");
}
