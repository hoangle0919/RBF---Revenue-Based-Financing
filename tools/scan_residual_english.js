/* Residual-English scan. Paste into the browser console on a page loaded with
 * ?lang=vi, or run it through a browser-driving tool.
 *
 * It walks every rendered text node and reports the ones that contain an
 * English function word while containing no Vietnamese diacritic -- i.e. copy
 * that the i18n pass did not reach. Anything in tools/residual_english.json is
 * exempt, with that file recording why.
 *
 * It is a HEURISTIC and reports suspects, not verdicts. Known limits:
 *   - a Vietnamese sentence with no diacritics is missed;
 *   - a proper name not yet listed shows up as a false positive;
 *   - text inside <noscript> is inert and cannot be reached by any runtime.
 *
 * MIXED-LANGUAGE BLINDNESS, and the partial fix. The node-level diacritic test
 * below skips an ENTIRE text node as soon as it contains one Vietnamese
 * character. A Vietnamese wrapper around a whole English paragraph therefore
 * produced a FALSE NEGATIVE -- which is exactly how an untranslated pricing
 * explanation survived a "0 suspects" result. scanResidualEnglish now also
 * splits each node into sentences and tests them individually, so an English
 * sentence sitting beside Vietnamese ones is reported.
 *
 * A "0 suspects" result is a SCANNER result, not a proof of translation
 * completeness. Read every line it prints before accepting a zero.
 *
 * Usage: scanResidualEnglish()           -> the current scenario / page state
 *        scanResidualEnglish({openAll:1}) -> opens every <details> first
 */
function scanResidualEnglish(opts) {
  opts = opts || {};
  if (opts.openAll) document.querySelectorAll('details').forEach(function (d) { d.open = true; });

  var ALLOW = new RegExp('^(' + [
    'RBF', 'VND', 'USD', 'GMV', 'APR', 'IRR', 'SHA-?256',
    'Shopee', 'Lazada', 'TikTok Shop', 'Vietnam', 'FastAPI', 'SQLite',
    'scikit-learn', 'Python', 'GitHub', 'Railway', 'MIT', 'arXiv', 'SSRN',
    'LinkedIn', 'Monte Carlo', 'Le Huu Hoang', 'Huu Hoang Le',
    'RBF-EQ', 'RBF-ILL', 'FIX-A', 'FIX-B', 'f\\*',
    '[A-Z]-\\d+', 'P\\d', 'S-\\d+', 'D-\\d+',
    'baseline[\\w]*_canonical\\.json', 'validation_[\\w.]+',
    'temp_closure', 'closure_m\\d+', '[0-9a-f]{12,}',
    'METHODOLOGY_SPEC\\.md.*', '[\\w.]+\\.(md|json|py|pdf|html)',
    'RESEARCH(<br>)?\\s*2026', 'RESEARCH',
  ].join('|') + ')$');

  var EN = /\b(the|and|of|for|is|are|not|this|that|with|from|which|was|were|has|have|been|only|each|within|where|when|every|their|than|then|does|its|per|by|on|in|to|at|as|an|it|be|but|or|if|no|all|more|less|paths?|months?|rate|revenue|payment|cap|factor|advance|loan|contract|mean|share|window|duration|recovery|burden|scenario|findings?|source|measured|computed|illustrative|observed|simulated|survivor|default|complete|incomplete)\b/i;
  var VI_DIACRITIC = /[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]/i;

  var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  var node, total = 0, suspects = [];
  while ((node = walker.nextNode())) {
    var text = (node.nodeValue || '').trim();
    if (!text || text.length < 3) continue;
    var parent = node.parentElement;
    if (!parent || parent.closest('script,style')) continue;
    total++;
    if (ALLOW.test(text)) continue;
    if (parent.closest('[aria-hidden="true"]')) continue;   // decorative

    // Sentence-level, not node-level. A node that mixes languages is the case
    // the node-level diacritic test was blind to.
    var sentences = text.split(/(?<=[.!?:])\s+/).filter(function (x) {
      return x.trim().length >= 25;           // ignore fragments and labels
    });
    var units = sentences.length > 1 ? sentences : [text];

    for (var u = 0; u < units.length; u++) {
      var unit = units[u].trim();
      if (!unit || ALLOW.test(unit)) continue;
      if (VI_DIACRITIC.test(unit)) continue;
      if (EN.test(unit)) {
        suspects.push({
          at: parent.id || (parent.tagName + '.' + (parent.className || '-')),
          text: unit.slice(0, 120),
          mixedNode: units.length > 1 && VI_DIACRITIC.test(text),
        });
        break;                                 // one report per node is enough
      }
    }
  }
  return { nodes: total, suspects: suspects.length, list: suspects };
}
if (typeof module !== 'undefined') module.exports = { scanResidualEnglish: scanResidualEnglish };
