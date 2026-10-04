import type { Schema } from '../api/client';
export interface TextPart { text: string; highlighted: boolean }
/** Backend offsets count Unicode code points. JS string.slice counts UTF-16 units. */
export function highlightParts(text: string, corrections: Schema<'CorrectionOut'>[]): TextPart[] {
  const chars = Array.from(text);
  const ranges = corrections.filter(c => c.status === 'active' && c.highlight_start != null && c.highlight_end != null)
    .sort((a, b) => a.highlight_start! - b.highlight_start!);
  const result: TextPart[] = [];
  let cursor = 0;
  for (const c of ranges) {
    const start = c.highlight_start!, end = c.highlight_end!;
    if (start < cursor || start < 0 || end > chars.length || end <= start || chars.slice(start, end).join('') !== c.original) continue;
    if (start > cursor) result.push({ text: chars.slice(cursor, start).join(''), highlighted: false });
    result.push({ text: chars.slice(start, end).join(''), highlighted: true }); cursor = end;
  }
  if (cursor < chars.length) result.push({ text: chars.slice(cursor).join(''), highlighted: false });
  return result;
}
