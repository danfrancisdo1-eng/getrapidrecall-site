#!/usr/bin/env python3
"""Build getrapidrecall.com.

    python3 build.py              -> dist/     production site for GitHub Pages
    python3 build.py --preview    -> preview/  review copy (launch mode, relative links, no analytics)

Production refuses to build while any class="tbd" placeholder remains (items Dan must confirm).
Pass --allow-tbd to override.

Launch switch: set APP_STORE_ID once Apple approves the app. While it is empty the site runs in
"coming soon" mode (no App Store badge, no Smart App Banner, signup is the main call to action).
"""
import html, json, re, shutil, sys
from pathlib import Path

# ---------------- Config ----------------
SITE = "https://getrapidrecall.com"
DOMAIN = "getrapidrecall.com"
APP_STORE_ID = ""                 # e.g. "6740000000" from App Store Connect > App Information > Apple ID
TESTFLIGHT_URL = "https://testflight.apple.com/join/1Rx2KdWn"               # public beta link, e.g. "https://testflight.apple.com/join/AbCd1234"
SUPPORT_EMAIL = "support@getrapidrecall.com"
BUTTONDOWN_USER = "rapidrecall"   # Buttondown newsletter username
PLAUSIBLE = True                  # cookieless analytics (prod only)
YEAR = "2026"
# ----------------------------------------

ROOT = Path(__file__).parent
SRC = ROOT / "src"
PREVIEW = "--preview" in sys.argv
ALLOW_TBD = "--allow-tbd" in sys.argv
OUT = ROOT / ("preview" if PREVIEW else "docs")
LAUNCHED = bool(APP_STORE_ID)
TF_LINK = TESTFLIGHT_URL or ("https://testflight.apple.com/join/PREVIEW" if PREVIEW else "")
BETA = bool(TF_LINK) and not LAUNCHED   # beta CTA shows until the App Store launch
MAILTO = f'<a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>'

LOGO = '<img src="/assets/logo-96.png" width="36" height="36" alt="">'

APP_URL = f"https://apps.apple.com/app/id{APP_STORE_ID or '0000000000'}"
BADGE = (f'<a class="badge-link" href="{APP_URL}" aria-label="Download RapidRecall AI on the App Store">'
         f'<img src="/assets/app-store-badge.svg" alt="Download on the App Store" width="144" height="48"></a>')

if LAUNCHED:
    CTA_HERO = BADGE + '\n        <span class="cta-note">Free to download · iPhone</span>'
elif BETA:
    CTA_HERO = (f'<a class="btn" href="{TF_LINK}">Join the iPhone beta</a>\n'
                '        <a class="btn btn-ghost" href="#beta">How the beta works</a>\n'
                '        <span class="soon">Free beta through Apple\'s TestFlight app · App Store launch coming soon</span>')
else:
    CTA_HERO = ('<a class="btn" href="#updates">Get launch updates</a>\n'
                '        <span class="soon">Coming soon to the App Store</span>')

TESTFLIGHT_APP = "https://apps.apple.com/app/testflight/id899247664"
BETA_SECTION = f'''<section class="band beta" id="beta" aria-labelledby="beta-title">
  <div class="wrap split">
    <div class="stack">
      <p class="eyebrow">Beta testers</p>
      <h2 id="beta-title">Try RapidRecall AI before it launches</h2>
      <p class="muted measure">The beta is free and runs through TestFlight, Apple's app for testing new iPhone apps. In-app purchases in the beta are test purchases, so you're never charged. Tell us what works and what doesn't, and you'll help shape the app before it reaches the App Store.</p>
      <div class="cta-row"><a class="btn" href="{TF_LINK}">Join the iPhone beta</a></div>
    </div>
    <ol class="beta-steps">
      <li><strong>Install TestFlight.</strong> Get Apple's free <a href="{TESTFLIGHT_APP}">TestFlight app</a> from the App Store.</li>
      <li><strong>Open the invite on your iPhone.</strong> Tap <a href="{TF_LINK}">Join the iPhone beta</a> on your phone. It opens in TestFlight.</li>
      <li><strong>Tap Accept, then Install.</strong> RapidRecall AI appears on your home screen like any other app.</li>
      <li><strong>Send feedback.</strong> Take a screenshot in the app and TestFlight asks if you want to send it to us, or email {MAILTO}.</li>
    </ol>
  </div>
</section>''' if BETA else ""

BETA_FAQ = f'''<h3>How do I join the beta?</h3>
      <p>Install Apple's free <a href="{TESTFLIGHT_APP}">TestFlight app</a>, then open <a href="{TF_LINK}">our beta invite</a> on your iPhone and tap Accept, then Install. Beta builds expire after 90 days; TestFlight will offer the newest build automatically.</p>
      ''' if BETA else ""

MAILTO = f'<a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>'
EMAIL_BLOCK = (f'<div class="email-line"><code id="support-email">{SUPPORT_EMAIL}</code>'
               f'<button class="copy-btn" type="button" data-copy="{SUPPORT_EMAIL}">Copy</button>'
               f'<a href="mailto:{SUPPORT_EMAIL}">Open in Mail</a></div>')

SIGNUP = f'''<form class="signup-form" id="signup" action="https://buttondown.com/api/emails/embed-subscribe/{BUTTONDOWN_USER}" method="post">
      <label class="sr-only" for="signup-email">Email address</label>
      <div class="field-row">
        <input type="email" id="signup-email" name="email" required autocomplete="email" inputmode="email" placeholder="you@school.edu">
        <button class="btn" type="submit">Sign up</button>
      </div>
      <input type="hidden" name="tag" value="website">
      <p class="form-msg" id="signup-msg" role="status" aria-live="polite"></p>
    </form>'''

SCRIPT = f'''<script>
(function () {{
  var f = document.getElementById("signup");
  if (f) f.addEventListener("submit", function (e) {{
    e.preventDefault();
    var m = document.getElementById("signup-msg");
    if (!f.checkValidity()) {{ m.textContent = "Enter a valid email address."; return; }}
    if (!/(^|\\.){re.escape(DOMAIN)}$/.test(location.hostname)) {{
      m.className = "form-msg"; m.textContent = "Preview only. Signups go live on {DOMAIN}."; return;
    }}
    m.className = "form-msg"; m.textContent = "Signing you up…";
    fetch(f.action, {{ method: "POST", body: new FormData(f), mode: "no-cors" }})
      .then(function () {{ m.className = "form-msg ok"; m.textContent = "Thanks! Check your inbox to confirm."; f.reset(); }})
      .catch(function () {{ f.submit(); }});
  }});
  document.querySelectorAll("[data-copy]").forEach(function (b) {{
    b.addEventListener("click", function () {{
      var t = b.getAttribute("data-copy");
      var done = function () {{ b.textContent = "Copied"; setTimeout(function () {{ b.textContent = "Copy"; }}, 1800); }};
      try {{
        navigator.clipboard.writeText(t).then(done, function () {{ sel(); }});
      }} catch (err) {{ sel(); }}
      function sel() {{ var c = document.getElementById("support-email"); var r = document.createRange(); r.selectNodeContents(c); var s = getSelection(); s.removeAllRanges(); s.addRange(r); }}
    }});
  }});
}})();
</script>'''

HEADER = f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/" aria-label="RapidRecall AI home">{LOGO}<span>RapidRecall AI</span></a>
    <nav class="nav" aria-label="Main">
      <a class="nav-wide" href="/#how">How it works</a>
      <a href="/#pricing">Pricing</a>
      <a class="nav-wide" href="/#faq">FAQ</a>
      <a href="/support">Support</a>
    </nav>
  </div>
</header>'''

FOOTER = f'''<footer class="site-footer">
  <div class="wrap">
    <div class="foot-top">
      <a class="brand" href="/" aria-label="RapidRecall AI home">{LOGO}<span>RapidRecall AI</span></a>
      <nav class="foot-links" aria-label="Footer">
        <a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="/support">Support</a>{MAILTO}
      </nav>
    </div>
    <p class="fine">RapidRecall AI is an independent study tool and is not affiliated with, endorsed by, or sponsored by Google or NVIDIA. Certification names are trademarks of their respective owners and are used only to describe exam content. Practice questions are not actual exam questions. Apple, the Apple logo, iPhone, and App Store are trademarks of Apple Inc.</p>
    <p class="fine">© {YEAR} Daniel Francis. RapidRecall AI. All rights reserved.</p>
  </div>
</footer>'''


def parse(page: Path):
    raw = page.read_text()
    m = re.match(r"<!--META\n(.*?)\n-->\n", raw, re.S)
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines())
    return meta, raw[m.end():]


def jsonld():
    data = {
        "@context": "https://schema.org", "@type": "MobileApplication", "name": "RapidRecall AI",
        "operatingSystem": "iOS", "applicationCategory": "EducationalApplication", "url": SITE + "/",
        "offers": [
            {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "USD"},
            {"@type": "Offer", "name": "Premium (monthly)", "price": "12.99", "priceCurrency": "USD"},
            {"@type": "Offer", "name": "Premium (yearly)", "price": "79.99", "priceCurrency": "USD"},
            {"@type": "Offer", "name": "Exam Pass (60 days)", "price": "29.99", "priceCurrency": "USD"},
        ],
    }
    if APP_STORE_ID:
        data["downloadUrl"] = APP_URL
    return '<script type="application/ld+json">' + json.dumps(data, separators=(",", ":")) + "</script>"


def head(meta, css, is_home):
    url = SITE + ("/" if meta["path"] == "/" else meta["path"])
    t, d = html.escape(meta["title"]), html.escape(meta["description"])
    parts = [
        f"<title>{t}</title>",
        f'<meta name="description" content="{d}">',
        f'<link rel="canonical" href="{url}">',
        '<meta name="theme-color" content="#f4f6f9" media="(prefers-color-scheme: light)">',
        '<meta name="theme-color" content="#0b1320" media="(prefers-color-scheme: dark)">',
        '<link rel="icon" type="image/png" sizes="48x48" href="/assets/favicon-48.png">',
        '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">',
        f'<meta property="og:image" content="{SITE}/assets/og.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="RapidRecall AI">',
        f'<meta property="og:title" content="{t}">',
        f'<meta property="og:description" content="{d}">',
        f'<meta property="og:url" content="{url}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if APP_STORE_ID and not PREVIEW:
        parts.append(f'<meta name="apple-itunes-app" content="app-id={APP_STORE_ID}">')  # Smart App Banner
    if meta["path"] == "/404":
        parts.append('<meta name="robots" content="noindex">')
    if is_home:
        parts.append(jsonld())
    if PLAUSIBLE and not PREVIEW:
        parts.append(f'<script defer data-domain="{DOMAIN}" src="https://plausible.io/js/script.js"></script>')
    parts.append(f"<style>{css}</style>")
    return "\n".join(parts)


def fill(body):
    return (body.replace("{{CTA_HERO}}", CTA_HERO).replace("{{SIGNUP_FORM}}", SIGNUP)
                .replace("{{BETA_SECTION}}", BETA_SECTION).replace("{{BETA_FAQ}}", BETA_FAQ)
                .replace("{{SUPPORT_EMAIL_TEXT}}", MAILTO).replace("{{SUPPORT_EMAIL_BLOCK}}", EMAIL_BLOCK))


def preview_links(doc, name):
    on_home = name == "index"
    def rep(m):
        target = m.group(1)
        path, _, frag = target.partition("#")
        if path.startswith("/assets/"):
            return f'href="{path[1:]}"'
        if path == "/":
            return f'href="{"#" + frag if on_home and frag else "index.html" + ("#" + frag if frag else "")}"'
        return f'href="{path.strip("/")}.html{("#" + frag) if frag else ""}"'
    doc = re.sub(r'href="(/[^"]*)"', rep, doc)
    return doc.replace('src="/assets/', 'src="assets/').replace('poster="/assets/', 'poster="assets/')


def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};:,>])\s*", r"\1", css)
    return css.replace(";}", "}").strip()


def main():
    css = minify_css((SRC / "styles.css").read_text())
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    for a in (SRC / "assets").iterdir():
        shutil.copy(a, OUT / "assets" / a.name)

    tbd_report = []
    for page in sorted((SRC / "pages").glob("*.html")):
        name = page.stem
        meta, body = parse(page)
        body = fill(body)
        tbds = re.findall(r'class="tbd"[^>]*>(.*?)</', body)
        tbd_report += [(name, re.sub("<[^>]+>", "", t)) for t in tbds]
        if not PREVIEW and ALLOW_TBD:
            body = body.replace(' class="tbd"', "").replace('class="tbd"', "")
        main_html = f'{HEADER}\n<main id="main">\n{body}\n</main>\n{FOOTER}\n{SCRIPT}'
        if PREVIEW and name == "index":
            # Artifact page: the publisher supplies doctype/head/body
            doc = (f"<title>RapidRecall AI</title>\n"
                   f'<meta name="claude:viewport-fit-sides" content="cover">\n'
                   f"<style>{css}</style>\n{main_html}\n")
        else:
            doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                   '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                   f"{head(meta, css, name == 'index')}\n</head>\n<body>\n{main_html}\n</body>\n</html>\n")
        if PREVIEW:
            doc = preview_links(doc, name)
        (OUT / f"{name}.html").write_text(doc)

    if not PREVIEW:
        (OUT / "CNAME").write_text(DOMAIN + "\n")
        (OUT / ".nojekyll").write_text("")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
        urls = ["/", "/privacy", "/terms", "/support"]
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{SITE}{u}</loc></url>\n" for u in urls) + "</urlset>\n")

    print(f"Built {OUT.name}/  (mode: {'launch' if LAUNCHED else 'beta' if BETA else 'coming soon'})")
    if tbd_report:
        print(f"\n{len(tbd_report)} items still to confirm:")
        for n, t in tbd_report:
            print(f"  [{n}] {t}")
        if not PREVIEW and not ALLOW_TBD:
            shutil.rmtree(OUT)
            sys.exit("\nProduction build stopped: confirm the items above (or pass --allow-tbd).")


if __name__ == "__main__":
    main()
