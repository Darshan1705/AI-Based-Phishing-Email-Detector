/**
 * highlighter.js
 * Three-tier highlight engine.
 *
 * Takes the raw email text and the explanation object from the API:
 *   { spam_keywords: [], urgency_phrases: [], suspicious_links: [] }
 *
 * Returns an HTML string with:
 *   <mark class="hl-spam">   → yellow  (spam keywords)
 *   <mark class="hl-urgency"> → orange  (urgency phrases)
 *   <mark class="hl-link">   → red     (suspicious links)
 */

const Highlighter = (() => {

  /** Escape special regex characters in a string. */
  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * Apply a single highlight pass over an HTML string.
   * Matches are wrapped with <mark class="${cls}">…</mark>.
   * Skips text that is already inside an existing <mark> tag.
   *
   * @param {string}   html      - current HTML (may already contain marks)
   * @param {string[]} terms     - word/phrase list to highlight
   * @param {string}   cls       - CSS class to apply
   * @returns {string}            updated HTML string
   */
  function applyHighlights(html, terms, cls) {
    if (!terms || terms.length === 0) return html;

    // Sort longest first so multi-word phrases match before sub-words
    const sorted = [...terms].sort((a, b) => b.length - a.length);

    for (const term of sorted) {
      const pattern = new RegExp(
        `(?<!<[^>]*)\\b(${escapeRegex(term)})\\b(?![^<]*>)`,
        'gi'
      );
      // Replace only in text nodes (outside of existing tags)
      html = html.replace(pattern, `<mark class="${cls}">$1</mark>`);
    }

    return html;
  }

  /**
   * Highlight suspicious links as complete URL tokens.
   * Links can't use a simple word-boundary approach.
   */
  function applyLinkHighlights(html, links, cls) {
    if (!links || links.length === 0) return html;

    for (const link of links) {
      const escaped = escapeRegex(link);
      const pattern = new RegExp(`(?<!<[^>]*)${escaped}(?![^<]*>)`, 'g');
      html = html.replace(pattern, `<mark class="${cls}">$&</mark>`);
    }

    return html;
  }

  /**
   * Main entry point — converts raw text + explanation → highlighted HTML.
   *
   * @param {string} rawText     - plain email text from textarea or parsed file
   * @param {Object} explanation - { spam_keywords, urgency_phrases, suspicious_links }
   * @returns {string}             HTML string safe for innerHTML
   */
  function highlight(rawText, explanation) {
    // 1. Escape HTML special chars in the raw text first
    let html = rawText
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');

    // 2. Preserve line breaks
    html = html.replace(/\n/g, '<br>');

    const { spam_keywords = [], urgency_phrases = [], suspicious_links = [] } = explanation || {};

    // 3. Apply in order: links → urgency → spam keywords
    //    (most specific first to avoid double-wrapping)
    html = applyLinkHighlights(html, suspicious_links, 'hl-link');
    html = applyHighlights(html, urgency_phrases, 'hl-urgency');
    html = applyHighlights(html, spam_keywords, 'hl-spam');

    return html;
  }

  return { highlight };
})();
