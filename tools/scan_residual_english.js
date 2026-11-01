/* Residual-English scan. Paste into the browser console on a page loaded with
 * ?lang=vi, or run it through a browser-driving tool.
 *
 * It walks every rendered text node and reports the ones that contain an
 * English function word while containing no Vietnamese diacritic -- i.e. copy
 * that the i18n pass did not reach. Anything in tools/residual_english.json is
 * exempt, with that file recording why.
 *
 * It is a HEURISTIC and reports suspects, not verdicts: a Vietnamese sentence
 * with no diacritics would be missed, and a proper name not yet listed shows
 * up as a false positive. Read every line it prints before accepting a zero.
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
    if (VI_DIACRITIC.test(text)) continue;
    if (EN.test(text)) {
      suspects.push({
        at: parent.id || (parent.tagName + '.' + (parent.className || '-')),
        text: text.slice(0, 120),
      });
    }
  }
  return { nodes: total, suspects: suspects.length, list: suspects };
}
if (typeof module !== 'undefined') module.exports = { scanResidualEnglish: scanResidualEnglish };
