#!/usr/bin/env python3
"""Build shopify/malone-lp.liquid.html from index.html + assets/style.css + assets/script.js.

The Shopify file is GENERATED so the standalone preview and the paste-ready version never drift.
  - markup  : <body> content wrapped in #pp-malone-lp
  - css     : every selector scoped under #pp-malone-lp (":root"/"body" -> wrapper, html rules dropped)
  - sticky  : moved OUT of the wrapper into #pp-malone-sticky with literal-valued, self-contained CSS
              (Shopify theme transforms trap position:fixed; the JS reparents it to <body>)
  - assets  : absolute GitHub Pages URLs (swap ASSET_BASE for the Shopify Files CDN path on go-live)
Run:  python3 shopify/build_shopify.py
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_BASE = "https://ksimmons0420.github.io/postandporch-malone-lp/"
SCOPE = "#pp-malone-lp"
STICKY = "#pp-malone-sticky"

html = open(f"{ROOT}/index.html", encoding="utf-8").read()
css = open(f"{ROOT}/assets/style.css", encoding="utf-8").read()
js = open(f"{ROOT}/assets/script.js", encoding="utf-8").read()

# ---------------------------------------------------------------- CSS scoping
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def blocks(text):
    """Yield (prelude, body) for top-level rules."""
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        j = text.index("{", i)
        prelude = text[i:j].strip()
        depth, k = 1, j + 1
        while depth:
            c = text[k]
            depth += (c == "{") - (c == "}")
            k += 1
        yield prelude, text[j + 1:k - 1]
        i = k


def map_sel(sel):
    sel = sel.strip()
    if sel.startswith(".sticky-cta") or sel == "html":
        return None
    if sel in (":root", "body"):
        return SCOPE
    if sel == "*":
        return f"{SCOPE} *"
    m = re.match(r"^\.js\s+(.*)$", sel)
    if m:
        return f".js {SCOPE} {m.group(1)}"
    return f"{SCOPE} {sel}"


def scope(text):
    out = []
    for prelude, body in blocks(text):
        if prelude.startswith("@font-face"):
            out.append(f"{prelude}{{{body.strip()}}}")
        elif prelude.startswith(("@media", "@supports")):
            inner = scope(body)
            if inner.strip():
                out.append(f"{prelude}{{\n{inner}\n}}")
        else:
            sels = [s for s in (map_sel(x) for x in prelude.split(",")) if s]
            if sels:
                out.append(f"{', '.join(sels)} {{{body.strip()}}}")
    return "\n".join(out)


scoped = scope(css)
# fonts: relative url('fonts/..') -> absolute
scoped = scoped.replace("url('fonts/", f"url('{ASSET_BASE}assets/fonts/")

BASE_RESET = f"""
/* ---- Shopify-theme hardening: the theme's global element styles must not leak in ---- */
{SCOPE} {{ position: relative; display: block; width: 100%; max-width: none; margin: 0; padding: 0; text-align: left; }}
{SCOPE} :is(h1, h2, h3) {{ text-transform: none; letter-spacing: normal; line-height: inherit; }}
{SCOPE} :is(ul, ol) {{ margin: 1em 0; padding: 0; }}  /* = browser default block margins, so it matches the standalone page */
{SCOPE} li {{ margin: 0; padding: 0; }}
{SCOPE} :is(p, li, blockquote, summary, td, th, address, figcaption, cite) {{ line-height: inherit; font-size: inherit; }}
{SCOPE} :is(button, summary, input, select, textarea) {{ font-family: inherit; }}
{SCOPE} :is(blockquote, figure, address, details, table) {{ margin: 0; }}
{SCOPE} table {{ border: 0; }}
{SCOPE} :is(blockquote, details) {{ padding: 0; border: 0; quotes: none; }}
{SCOPE} :is(th, td) {{ border-top: 0; border-left: 0; border-right: 0; background: none; text-transform: none; letter-spacing: normal; }}
{SCOPE} :is(a, a:hover) {{ text-decoration: none; }}
{SCOPE} a.colorway-tile, {SCOPE} .btn {{ text-decoration: none; }}
{SCOPE} summary {{ outline-offset: 3px; }}
{SCOPE} img {{ border: 0; }}
"""

# re-assert underlines the standalone CSS asks for (they come AFTER the reset in source order but
# the reset above is emitted first, and these rules have higher/equal specificity + later position)
STICKY_CSS = f"""
/* ---- Sticky mobile CTA: lives on <body> (reparented by JS) so it is fully self-styled: LITERAL values + own box-sizing.
        Do NOT "clean up" these hex values into var(): custom properties don't follow a reparented element. ---- */
{STICKY}, {STICKY} * {{ box-sizing: border-box; }}
{STICKY} {{ position: fixed; left: 0; right: 0; bottom: 0; z-index: 9000; background: rgba(255,255,255,0.92);
  -webkit-backdrop-filter: blur(14px) saturate(160%); backdrop-filter: blur(14px) saturate(160%);
  border-top: 1px solid #E3DACB; padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  font-family: 'Switzer', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif; color: #434341; line-height: 1.6; text-align: left; }}
{STICKY} .sticky-cta__price {{ font-family: 'Crimson Pro', Georgia, serif; font-size: 18px; font-weight: 400; color: #434341; line-height: 1.3; }}
{STICKY} .sticky-cta__price span {{ display: block; font-family: 'Switzer', -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 12px; color: #5E5C5A; text-transform: uppercase; letter-spacing: .06em; }}
{STICKY} .btn {{ display: inline-flex; align-items: center; justify-content: center; flex: 0 0 auto; min-height: 48px; padding: 12px 22px;
  border: 0; border-radius: 999px; background: #434341; color: #FFFFFF; font-family: 'Switzer', -apple-system, 'Helvetica Neue', Arial, sans-serif;
  font-size: 16px; font-weight: 600; letter-spacing: .01em; text-decoration: none; box-shadow: 0 6px 18px rgba(67,67,65,0.22); touch-action: manipulation; }}
{STICKY} .btn:active {{ transform: scale(.97); }}
{STICKY} a:focus-visible {{ outline: 3px solid #57656E; outline-offset: 3px; }}
@media (min-width: 900px) {{ {STICKY} {{ display: none; }} }}
"""

UNDERLINES = f"""
{SCOPE} .compat-note a, {SCOPE} .site-footer__nap a {{ text-decoration: underline; text-underline-offset: 3px; }}
"""

# ---------------------------------------------------------------- markup
body = html.split("<body>", 1)[1].rsplit("</body>", 1)[0]
body = re.sub(r"<script[^>]*src=[^>]*></script>\s*", "", body)  # script.js is inlined below

m = re.search(r'<!-- =+ STICKY MOBILE CTA =+ -->\s*(<div class="sticky-cta">.*?</a>\s*</div>)', body, re.S)
assert m, "sticky block not found"
sticky = m.group(1).replace('<div class="sticky-cta">', f'<div id="pp-malone-sticky" class="sticky-cta">', 1)
body = body.replace(m.group(0), "")

body = body.replace('<main id="main">', '<div id="pp-main">').replace("</main>", "</div>").replace('href="#main"', 'href="#pp-main"')


def absolutize(txt):
    return re.sub(r"""(["'(])assets/""", lambda mm: f"{mm.group(1)}{ASSET_BASE}assets/", txt)


body = absolutize(body)
sticky = absolutize(sticky)

# head-level things that are legal in <body>: preloads + JSON-LD
head = html.split("<head>", 1)[1].split("</head>", 1)[0]
preloads = "\n".join(absolutize(x) for x in re.findall(r"<link rel=\"preload\"[^>]*>", head))
jsonld = re.search(r'<script type="application/ld\+json">.*?</script>', head, re.S).group(0)

# ---------------------------------------------------------------- JS
BOOTSTRAP = r"""
/* ===== Shopify page bootstrap: chrome hide + fixed-element reparent + overlay suppression =====
   Everything here runs ONLY on the page that contains #pp-malone-lp, so it never touches other store pages.
   Tune CFG after inspecting the live theme in DevTools (selectors below are best-guesses for OS2.0 themes). */
(function () {
  var CFG = {
    hideThemeChrome: true,
    // theme header / announcement bar / footer / auto page title (hidden via inline styles = survives the page-editor sanitizer)
    chromeSelectors: ['.shopify-section-group-header-group', '.shopify-section-group-footer-group', '.shopify-section-group-overlay-group',
      '#shopify-section-header', '#shopify-section-announcement-bar', '#shopify-section-footer', '.announcement-bar',
      '.main-page-title', '.page-title', '.page__title'],
    suppressCookieSheet: true,   // Shopify customer-privacy banner. NOTE: hiding it is a compliance call - confirm with the client.
    cookieSelectors: ['#shopify-pc__banner', '[id^="shopify-pc__"]', '.shopify-pc__banner__dialog'],
    suppressPopups: true,        // email/timer popups (e.g. the "Alia" app) - exact selectors TBD from the live store
    popupSelectors: ['[id*="alia" i]', '[class*="alia-" i]', '[class*="klaviyo-form" i][role="dialog"]', '[id*="privy" i]', '[class*="popup" i][class*="modal" i]']
  };
  var lp = document.getElementById('pp-malone-lp');
  if (!lp) return;
  var sticky = document.getElementById('pp-malone-sticky');

  function hide(el) { if (el && !lp.contains(el) && !(sticky && sticky.contains(el))) { el.style.setProperty('display', 'none', 'important'); } }
  function hideAll(list) { list.forEach(function (sel) { try { document.querySelectorAll(sel).forEach(hide); } catch (e) {} }); }

  function stripWidthLimits() {
    var section = lp.closest('.shopify-section');
    if (section && section.parentNode) {
      Array.prototype.forEach.call(section.parentNode.children, function (s) {
        if (s !== section && s.classList.contains('shopify-section') && CFG.hideThemeChrome) { s.style.display = 'none'; }
      });
    }
    var p = lp.parentNode;
    while (p && p !== document.body) {
      var c = p.classList;
      if (c && (c.contains('page-width') || c.contains('page-width--narrow') || c.contains('rte') || c.contains('page') || c.contains('container'))) {
        p.style.maxWidth = 'none'; p.style.padding = '0'; p.style.margin = '0'; p.style.width = '100%';
      }
      p = p.parentNode;
    }
    var main = document.querySelector('main');
    if (main) { main.style.padding = '0'; main.style.margin = '0'; main.style.maxWidth = 'none'; }
  }

  // position:fixed inside a transformed ancestor (theme slide-in animations) pins to that ancestor, not the viewport.
  // Reparent to <body>; the sticky bar's CSS is fully self-contained (literal values) for exactly this reason.
  function reparent() { if (sticky && sticky.parentNode !== document.body) { document.body.appendChild(sticky); } }

  function overlays() {
    if (!(CFG.suppressCookieSheet || CFG.suppressPopups)) return;
    if (CFG.suppressCookieSheet) hideAll(CFG.cookieSelectors);
    if (CFG.suppressPopups) hideAll(CFG.popupSelectors);
    // heuristic sweep: fixed, high z-index, big full-width bottom sheet (cookie) or large centered modal (popup) that is not ours
    var vw = window.innerWidth, vh = window.innerHeight;
    document.querySelectorAll('body > *, body > * > *').forEach(function (el) {
      if (lp.contains(el) || el.contains(lp) || el === sticky) return;
      var cs = getComputedStyle(el);
      if (cs.position !== 'fixed') return;
      var r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
      var z = parseInt(cs.zIndex, 10) || 0;
      var bottomSheet = CFG.suppressCookieSheet && r.width >= vw * 0.6 && r.height <= vh * 0.4 && (vh - r.bottom) <= 8 && r.bottom >= vh - 2;
      var bigModal = CFG.suppressPopups && z >= 1000 && r.width * r.height >= vw * vh * 0.25;
      if (bottomSheet || bigModal) hide(el);
    });
  }

  function liftChatWidget() {  // keep third-party chat bubbles above the sticky bar (mobile only)
    if (window.innerWidth >= 900 || !sticky) return;
    var h = sticky.offsetHeight || 76;
    document.querySelectorAll('iframe, div, button').forEach(function (el) {
      if (el === sticky || sticky.contains(el) || lp.contains(el) || el.getAttribute('data-pp-lifted')) return;
      var cs = getComputedStyle(el); if (cs.position !== 'fixed') return;
      var r = el.getBoundingClientRect();
      if (!r.width || r.width > 240 || r.height > 240) return;
      if (window.innerHeight - r.bottom > 100 || window.innerWidth - r.right > 100) return;
      el.style.setProperty('bottom', ((parseInt(cs.bottom, 10) || 0) + h) + 'px', 'important');
      el.setAttribute('data-pp-lifted', '1');
    });
  }

  function run() {
    if (CFG.hideThemeChrome) { hideAll(CFG.chromeSelectors); }
    stripWidthLimits(); reparent(); overlays(); liftChatWidget();
  }
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', run); } else { run(); }
  window.addEventListener('load', run);
  [800, 2000, 4500, 9000].forEach(function (t) { setTimeout(function () { overlays(); liftChatWidget(); }, t); });
  if (window.MutationObserver) {  // late-mounting popups / widgets, for 30s
    var t, mo = new MutationObserver(function () { clearTimeout(t); t = setTimeout(function () { overlays(); liftChatWidget(); }, 250); });
    mo.observe(document.body, { childList: true, subtree: true });
    setTimeout(function () { mo.disconnect(); }, 30000);
  }
})();
"""

stamp = "<!-- POST & PORCH - THE MALONE LP (Shopify paste build) - generated by shopify/build_shopify.py from index.html - build v1.1 -->"
out = f"""{stamp}
<!-- PASTE: Shopify admin > Online Store > Pages > (page) > <> Show HTML. Set the page SEO title/description + canonical/OG in the page's
     "Search engine listing" + theme settings (head tags can't live in the page body). ASSET_BASE is GitHub Pages for now;
     on go-live upload /assets to Shopify Files and run this builder with the CDN base. -->
{preloads}
{jsonld}
<style>
{scoped}
{BASE_RESET}
{UNDERLINES}
{STICKY_CSS}
</style>
<div id="pp-malone-lp">
<script>document.documentElement.classList.add('js');</script>
{body.strip()}
</div>
{sticky}
<script>
{js.strip()}
</script>
<script>
{BOOTSTRAP.strip()}
</script>
"""

# guard rails
assert "{{" not in out and "{%" not in out, "Liquid delimiters present - wrap in {% raw %}"
non_ascii = sum(ord(c) > 127 for c in out)
assert non_ascii == 0, f"{non_ascii} non-ascii chars"
rel = re.findall(r"""(?:src|href|srcset|poster)=["'](?!https?:|#|mailto:|tel:)([^"']+)""", out)
assert not rel, f"relative URLs left: {rel[:5]}"
dest = f"{ROOT}/shopify/malone-lp.liquid.html"
open(dest, "w", encoding="utf-8").write(out)
print(f"wrote {dest}  ({len(out):,} bytes, scoped css {len(scoped):,} chars)")
