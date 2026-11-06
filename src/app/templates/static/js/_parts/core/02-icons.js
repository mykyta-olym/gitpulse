/* ============================================
   Icons for JS-rendered markup
   ============================================
   ONE registry: GP.icons, in icons.js, bundled ahead of this file - 122
   Pajamas glyphs generated from components/icons.html. This file used to keep
   a second table of its own, which is how it drifted: six entries, still the
   24x24 stroked Feather set the app moved off, and missing four of the names
   its own callers asked for - and a missing name answers with '', which is an
   empty, padded icon box where a mark should be.

   iconSvg is the size-token front door onto that registry (`icon icon-sm` and
   friends, the same classes the Jinja macro emits), so JS-rendered and
   server-rendered icons are the same glyph at the same size. An unknown name
   still answers '' here rather than GP.icons' question-mark fallback: callers
   place it in markup where a wrong icon is worse than none.
*/
const _ICON_PX = { xs: 12, sm: 16, md: 20, lg: 24, xl: 32 };
GP.iconSvg = function (name, size) {
  if (!GP.icons.has(name)) return '';
  return GP.icons.get(name, _ICON_PX[size] || 20, 'icon' + (size ? ' icon-' + size : ''));
};
