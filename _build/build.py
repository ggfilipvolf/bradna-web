#!/usr/bin/env python3
"""
Generátor webu bradnaladislav.cz – podstránky, blog, RSS a sitemap.

Spuštění:  python3 _build/build.py
  --vse      vygeneruje i články s budoucím datem (jen pro lokální náhled, nikdy necommitovat)

Zdroje:
  _clanky/*.md       články (hlavička --- title/slug/date/description/perex/kategorie ---)
  _build/stranky/*   obsah podstránek (O mně, Co řeším, Jak to probíhá, Reference)

Článek se zveřejní, když je jeho datum (Europe/Prague) dnes nebo dřív a je aspoň 10:00.
Volitelně hlavička `cas: 10:00` a `koncept: ano` (koncept se nikdy nezveřejní).
"""
import datetime as dt
import html
import json
import os
import re
import shutil
import sys
from email.utils import format_datetime
from zoneinfo import ZoneInfo

import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.bradnaladislav.cz"
TZ = ZoneInfo("Europe/Prague")
NOW = dt.datetime.now(TZ)
INCLUDE_FUTURE = "--vse" in sys.argv

MESICE = ["ledna", "února", "března", "dubna", "května", "června", "července",
          "srpna", "září", "října", "listopadu", "prosince"]

KATEGORIE = ["První byt", "Podnikatelé", "Konec fixace", "Rodina a rodiče",
             "Stavba a rekonstrukce", "Jak to v bance chodí", "Trh a sazby"]

NAV = [("/o-mne/", "O mně"), ("/co-resim/", "Co řeším"), ("/jak-to-probiha/", "Jak to probíhá"),
       ("/reference/", "Reference"), ("/blog/", "Blog")]

SOCIAL = {
    "ig": "https://www.instagram.com/ladislav.bradna/",
    "yt": "https://www.youtube.com/@ladislavbradna1630",
    "li": "https://cz.linkedin.com/in/ladislav-bradna-23654611a",
}

ICONS = {
    "ig": '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1"/></svg>',
    "yt": '<svg viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14" rx="4"/><path d="M10 9l5 3-5 3z" fill="currentColor" stroke="none"/></svg>',
    "li": '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M7.5 10.5V17M7.5 7.3v.2M11.5 17v-3.6a2.3 2.3 0 0 1 4.6 0V17"/></svg>',
}
SOC_LABEL = {"ig": "Instagram", "yt": "YouTube", "li": "LinkedIn"}

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%230C1D2E'/%3E%3Crect x='10' y='10' width='44' height='44' fill='none' stroke='%23C9A96A' stroke-width='1.4'/%3E%3Ctext x='32' y='41' font-family='Georgia,serif' font-size='22' fill='%23F4F1EA' text-anchor='middle' letter-spacing='1'%3ELB%3C/text%3E%3C/svg%3E")

METRICOOL = ('<script>function loadScript(a){var b=document.getElementsByTagName("head")[0],c=document.createElement("script");'
             'c.type="text/javascript",c.src="https://tracker.metricool.com/resources/be.js",c.onreadystatechange=a,c.onload=a,b.appendChild(c)}'
             'loadScript(function(){beTracker.t({hash:"cbddf5d687b5ed580fc45296ffd1684a"})});</script>')

PERSON = {"@type": "Person", "name": "Ladislav Bradna", "jobTitle": "Hypoteční specialista",
          "url": SITE + "/o-mne/", "image": SITE + "/portrait.jpg", "sameAs": list(SOCIAL.values())}


def esc(s):
    return html.escape(s or "", quote=True)


def cz_date(d):
    return f"{d.day}. {MESICE[d.month - 1]} {d.year}"


# ---------------------------------------------------------------- šablony
def head(title, description, path, og_type="website", extra_ld=None, og_image="/og-image.jpg", rss=True):
    url = SITE + path
    ld = ""
    for block in (extra_ld or []):
        ld += '<script type="application/ld+json">' + json.dumps(block, ensure_ascii=False) + "</script>\n"
    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="cs_CZ">
<meta property="og:site_name" content="Ladislav Bradna">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{SITE}{og_image}">
{'<link rel="alternate" type="application/rss+xml" title="Blog Ladislava Bradny" href="' + SITE + '/feed.xml">' if rss else ''}
{ld}<link rel="icon" href="{FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Yantramanav:wght@100;300;400;500;700&family=Archivo:wght@300;400;500;600&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<link rel="stylesheet" href="/assets/pages.css">
<!-- Metricool tracking -->
{METRICOOL}
</head>
<body>
<div class="grain" aria-hidden="true"></div>
<div id="scrollbar"></div>
"""


def header(active):
    act = ' class="active" aria-current="page"'
    links = "\n".join(
        f'      <a href="{href}"{act if href == active else ""}>{label}</a>'
        for href, label in NAV)
    mlinks = "\n".join(f'  <a href="{href}">{label}</a>' for href, label in NAV)
    soc = "\n".join(
        f'        <a href="{SOCIAL[k]}" target="_blank" rel="noopener" aria-label="{SOC_LABEL[k]}" title="{SOC_LABEL[k]}">{ICONS[k]}</a>'
        for k in ("ig", "yt", "li"))
    msoc = "\n".join(
        f'    <a href="{SOCIAL[k]}" target="_blank" rel="noopener" aria-label="{SOC_LABEL[k]}">{ICONS[k]}</a>'
        for k in ("ig", "yt", "li"))
    return f"""
<header id="header">
  <div class="nav">
    <a href="/" class="brand" aria-label="Ladislav Bradna – úvod">
      <span class="mono">LB</span>
      <span class="name">Ladislav<br>Bradna</span>
    </a>
    <nav class="nav-links">
{links}
    </nav>
    <div class="nav-cta">
      <div class="nav-social">
{soc}
      </div>
      <a href="/konzultace.html" class="btn btn-primary"><span class="lbl">Chci konzultaci</span></a>
      <button class="burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>

<div class="mobile-menu" id="mobileMenu">
  <button class="close" id="closeMenu" aria-label="Zavřít">&times;</button>
  <a href="/">Úvod</a>
{mlinks}
  <a href="/konzultace.html" class="btn btn-primary"><span class="lbl">Chci konzultaci</span></a>
  <div class="mm-social">
{msoc}
  </div>
</div>
"""


def cta_band(title_html="Pojďme to <em class=\"acc\">spočítat.</em>",
             text="Napište mi, co řešíte. Ozvu se s termínem nezávazného úvodního hovoru – 20 minut, online. Mě platí banka, vás to nic nestojí."):
    return f"""
<section class="cta-band">
  <div class="wrap">
    <div>
      <span class="kicker reveal">Nezávazná konzultace</span>
      <h2 class="reveal">{title_html}</h2>
      <p class="reveal">{text}</p>
    </div>
    <div class="cta-actions reveal">
      <a href="/konzultace.html" class="btn btn-primary"><span class="lbl">Chci konzultaci</span> <span class="arrow">→</span></a>
      <span class="cta-note">Úvodní hovor 20 min · online · zdarma</span>
    </div>
  </div>
</section>
"""


def footer():
    pages = "\n".join(f'        <a href="{h}">{l}</a>' for h, l in NAV)
    return f"""
<footer>
  <div class="wrap">
    <img src="/signature.png" alt="" aria-hidden="true" class="foot-sign" loading="lazy">
    <div class="foot-grid">
      <div class="foot-brand">
        <div class="fmotto">Financování — jednoduše a přehledně.</div>
        <p>Hypotéky, refinancování i složitější financování — s klidem a odborností.</p>
      </div>
      <div class="foot-col">
        <h4>Kontakt</h4>
        <a href="mailto:ladislav@mech.cz">ladislav@mech.cz</a>
        <a href="tel:+420734249626">+420 734 249 626</a>
        <a href="/konzultace.html">Chci konzultaci</a>
        <a href="/gdpr.html">Ochrana osobních údajů</a>
      </div>
      <div class="foot-col">
        <h4>Web</h4>
{pages}
        <a href="/feed.xml">RSS</a>
      </div>
    </div>
    <div class="foot-bottom">
      <p>© <span id="year"></span> Ladislav Bradna · IČO 87998963 · Kroměřížská 181, 752 01 Kojetín</p>
      <p><a href="{SOCIAL['ig']}" target="_blank" rel="noopener">Instagram</a> · <a href="{SOCIAL['yt']}" target="_blank" rel="noopener">YouTube</a> · <a href="{SOCIAL['li']}" target="_blank" rel="noopener">LinkedIn</a></p>
    </div>
  </div>
</footer>

<div class="cookiebar" id="cookieBar" role="dialog" aria-label="Souhlas s cookies">
  <p>Používáme cookies pro měření návštěvnosti a účinnosti reklamy (Meta Pixel). Více v <a href="/cookies.html">zásadách cookies</a>.</p>
  <div class="cookiebar-btns">
    <button type="button" class="cb-btn cb-ghost" id="cookieReject">Odmítnout</button>
    <button type="button" class="cb-btn cb-primary" id="cookieAccept">Souhlasím</button>
  </div>
</div>
<script src="/assets/site.js" defer></script>
</body>
</html>
"""


def crumbs(items):
    """items = [(label, href|None)]"""
    out = []
    for i, (label, href) in enumerate(items):
        if i:
            out.append('<span class="sep">/</span>')
        out.append(f'<a href="{href}">{esc(label)}</a>' if href else f'<span>{esc(label)}</span>')
    return '<nav class="crumbs" aria-label="Drobečková navigace">' + "".join(out) + "</nav>"


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": label, "item": SITE + (href or "")}
        for i, (label, href) in enumerate(items)]}


def write(path, content):
    full = os.path.join(ROOT, path.lstrip("/"))
    if full.endswith("/"):
        full += "index.html"
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- články
def parse_post(fn):
    raw = open(fn, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise SystemExit(f"Chybí hlavička v {fn}")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            v = re.sub(r"\s+#.*$", "", v).strip().strip('"').strip("'")
            meta[k.strip()] = v
    body = m.group(2).strip()
    for req in ("title", "slug", "date", "description"):
        if not meta.get(req):
            raise SystemExit(f"{fn}: chybí '{req}'")
    d = dt.date.fromisoformat(meta["date"])
    hh, mm = (meta.get("cas") or "10:00").split(":")
    meta["published"] = dt.datetime(d.year, d.month, d.day, int(hh), int(mm), tzinfo=TZ)
    meta["kategorie"] = meta.get("kategorie") or "Jak to v bance chodí"
    meta["body_md"] = body
    md = markdown.Markdown(extensions=["tables", "sane_lists", "toc"],
                           extension_configs={"toc": {"slugify": slugify}})
    body_html = md.convert(body)
    body_html = re.sub(r"<table>", '<div class="table-scroll"><table>', body_html)
    body_html = re.sub(r"</table>", "</table></div>", body_html)
    meta["body_html"] = body_html
    words = len(re.findall(r"\w+", body))
    meta["words"] = words
    meta["minutes"] = max(2, round(words / 200))
    meta["faq"] = extract_faq(body_html)
    meta["path"] = f"/blog/{meta['slug']}/"
    meta["draft"] = (meta.get("koncept") or "").lower() in ("ano", "yes", "true", "1")
    return meta


def slugify(value, separator="-"):
    tbl = str.maketrans("áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ", "acdeeinorstuuyzACDEEINORSTUUYZ")
    value = value.translate(tbl).lower()
    value = re.sub(r"[^a-z0-9]+", separator, value).strip(separator)
    return value


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def extract_faq(body_html):
    m = re.search(r'<h2[^>]*>\s*Časté otázky\s*</h2>(.*?)(?=<h2|\Z)', body_html, re.S)
    if not m:
        return []
    qa = []
    for q, a in re.findall(r"<h3[^>]*>(.*?)</h3>(.*?)(?=<h3|\Z)", m.group(1), re.S):
        qa.append({"@type": "Question", "name": strip_tags(q),
                   "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}})
    return qa


def post_card(p, heading="h3", featured=False):
    cls = "post-card reveal" + (" featured" if featured else "")
    return f"""<a class="{cls}" href="{p['path']}" data-cat="{esc(p['kategorie'])}">
  <div>
    <div class="post-meta"><span class="cat">{esc(p['kategorie'])}</span><span>{cz_date(p['published'])}</span><span>{p['minutes']} min čtení</span></div>
    <{heading}>{esc(p['title'])}</{heading}>
  </div>
  <div>
    <p>{esc(p.get('perex') or p['description'])}</p>
    <span class="read">Číst článek <span>→</span></span>
  </div>
</a>"""


def build_post(p, posts):
    items = [("Úvod", "/"), ("Blog", "/blog/"), (p["title"], p["path"])]
    ld = [{
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "description": p["description"],
        "datePublished": p["published"].isoformat(), "dateModified": p["published"].isoformat(),
        "inLanguage": "cs", "mainEntityOfPage": SITE + p["path"],
        "image": SITE + "/og-image.jpg", "author": PERSON,
        "publisher": {"@type": "Person", "name": "Ladislav Bradna", "url": SITE + "/"},
        "articleSection": p["kategorie"], "wordCount": p["words"]},
        crumbs_ld(items)]
    if p["faq"]:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": p["faq"]})
    same = [x for x in posts if x is not p and x["kategorie"] == p["kategorie"]]
    other = [x for x in posts if x is not p and x not in same]
    related = (same + other)[:3]
    rel_html = ""
    if related:
        rel_html = f"""
<section class="related">
  <div class="wrap">
    <span class="kicker reveal">Další články</span>
    <h2 class="reveal">Mohlo by vás <em class="acc">zajímat.</em></h2>
    <div class="blog-grid">
      {''.join(post_card(r) for r in related)}
    </div>
  </div>
</section>"""
    page = head(f"{p['title']} | Ladislav Bradna", p["description"], p["path"], og_type="article", extra_ld=ld)
    page += header("/blog/")
    page += f"""
<main>
<article>
<section class="article-hero">
  <div class="wrap">
    {crumbs(items[:2] + [(p['kategorie'], None)])}
    <div class="post-meta"><span class="cat">{esc(p['kategorie'])}</span><span><time datetime="{p['published'].date().isoformat()}">{cz_date(p['published'])}</time></span><span>{p['minutes']} min čtení</span></div>
    <h1>{esc(p['title'])}</h1>
    {f'<p class="perex">{esc(p["perex"])}</p>' if p.get('perex') else ''}
    <div class="author-line">
      <img src="/about.jpg" alt="Ladislav Bradna" width="52" height="52">
      <div><div class="an">Ladislav Bradna</div><div class="ar">Hypoteční specialista · ve financích od 2012</div></div>
    </div>
  </div>
</section>

<section class="article-body">
  <div class="wrap">
    <div class="prose">
{p['body_html']}
    </div>

    <aside class="article-cta">
      <span class="k">Nezávazná konzultace</span>
      <h2>Chcete to spočítat pro vaši situaci?</h2>
      <p>Napište mi pár vět o tom, co řešíte. Ozvu se s termínem úvodního hovoru – 20 minut, online. Mě platí banka, vás to nic nestojí.</p>
      <div class="row">
        <a href="/konzultace.html" class="btn btn-primary"><span class="lbl">Chci konzultaci</span> <span class="arrow">→</span></a>
        <a href="tel:+420734249626" class="btn btn-ghost">+420 734 249 626</a>
      </div>
    </aside>

    <div class="author-box">
      <img src="/about.jpg" alt="Ladislav Bradna" loading="lazy" width="90" height="90">
      <div>
        <div class="an">Ladislav Bradna</div>
        <p>Ve financích od roku 2012, posledních čtrnáct let se věnuju jen úvěrům a hypotékám. Složité věci vysvětluju jednoduše a na rovinu. <a href="/o-mne/">Více o mně</a></p>
      </div>
    </div>
  </div>
</section>
</article>
{rel_html}
</main>
"""
    page += footer()
    write(p["path"], page)


def build_blog_index(posts):
    items = [("Úvod", "/"), ("Blog", "/blog/")]
    cats = [c for c in KATEGORIE if any(p["kategorie"] == c for p in posts)]
    filt = ""
    if len(cats) > 1:
        filt = '<div class="cat-filter reveal"><button class="on" data-cat="">Vše</button>' + "".join(
            f'<button data-cat="{esc(c)}">{esc(c)}</button>' for c in cats) + "</div>"
    if posts:
        cards = post_card(posts[0], heading="h2", featured=True) + "".join(post_card(p, heading="h2") for p in posts[1:])
    else:
        cards = '<p class="reveal">První články připravuji.</p>'
    ld = [{"@context": "https://schema.org", "@type": "Blog", "name": "Blog Ladislava Bradny",
           "url": SITE + "/blog/", "inLanguage": "cs", "author": PERSON,
           "blogPost": [{"@type": "BlogPosting", "headline": p["title"], "url": SITE + p["path"],
                         "datePublished": p["published"].isoformat()} for p in posts[:20]]},
          crumbs_ld(items)]
    page = head("Blog o hypotékách a financování bydlení | Ladislav Bradna",
                "Hypotéky srozumitelně: kolik vám banka půjčí, co dělat při konci fixace, hypotéka pro OSVČ, rodiče jako pomoc. Praktické rady z praxe.",
                "/blog/", extra_ld=ld)
    page += header("/blog/")
    page += f"""
<main>
<section class="page-hero">
  <div class="wrap">
    {crumbs(items)}
    <span class="kicker reveal">Blog</span>
    <h1 class="reveal">Hypotéky <em class="acc">srozumitelně.</em></h1>
    <p class="lead reveal">Co lidi na schůzkách řeší nejčastěji – vysvětlené jednoduše a na rovinu. Každý týden jeden článek, vždycky s konkrétním výpočtem.</p>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    {filt}
    <div class="blog-grid">
{cards}
    </div>
  </div>
</section>
</main>
"""
    page += cta_band()
    page += footer()
    write("/blog/", page)


def build_feed(posts):
    items = []
    for p in posts[:30]:
        content = p["body_html"] + (
            f'<p><a href="{SITE}/konzultace.html">Chcete to spočítat pro vaši situaci? Domluvte si nezávaznou konzultaci.</a></p>')
        items.append(f"""    <item>
      <title>{esc(p['title'])}</title>
      <link>{SITE}{p['path']}</link>
      <guid isPermaLink="true">{SITE}{p['path']}</guid>
      <pubDate>{format_datetime(p['published'])}</pubDate>
      <category>{esc(p['kategorie'])}</category>
      <description>{esc(p.get('perex') or p['description'])}</description>
      <content:encoded><![CDATA[{content}]]></content:encoded>
      <enclosure url="{SITE}/og-image.jpg" length="0" type="image/jpeg"/>
      <media:content url="{SITE}/og-image.jpg" medium="image" type="image/jpeg"/>
    </item>""")
    last = format_datetime(posts[0]["published"]) if posts else format_datetime(NOW)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Ladislav Bradna – blog o hypotékách</title>
    <link>{SITE}/blog/</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Hypotéky a financování bydlení srozumitelně a na rovinu.</description>
    <language>cs</language>
    <lastBuildDate>{last}</lastBuildDate>
    <image><url>{SITE}/og-image.jpg</url><title>Ladislav Bradna – blog o hypotékách</title><link>{SITE}/blog/</link></image>
{chr(10).join(items)}
  </channel>
</rss>
"""
    with open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(feed)


def build_sitemap(posts, pages):
    urls = [(SITE + "/", posts[0]["published"].date().isoformat() if posts else None, "weekly", "1.0")]
    for path in pages:
        urls.append((SITE + path, None, "monthly", "0.8"))
    urls.append((SITE + "/blog/", posts[0]["published"].date().isoformat() if posts else None, "weekly", "0.8"))
    urls.append((SITE + "/konzultace.html", None, "monthly", "0.9"))
    for p in posts:
        urls.append((SITE + p["path"], p["published"].date().isoformat(), "yearly", "0.7"))
    body = "\n".join(
        "  <url>\n    <loc>{}</loc>{}\n    <changefreq>{}</changefreq>\n    <priority>{}</priority>\n  </url>".format(
            u, f"\n    <lastmod>{lm}</lastmod>" if lm else "", cf, pr) for u, lm, cf, pr in urls)
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + body + "\n</urlset>\n")


# ---------------------------------------------------------------- podstránky
def posts_snippet(posts, kategorie=None, n=3):
    sel = [p for p in posts if not kategorie or p["kategorie"] in kategorie][:n]
    if not sel:
        return ""
    return ('<div class="blog-grid">' + "".join(post_card(p) for p in sel) + "</div>")


def render_fragment(text, posts):
    # <!--POSTS:Kategorie|Kategorie:3--> → karty článků; prázdný blok <!--IFPOSTS-->…<!--/IFPOSTS--> se vynechá
    def repl(m):
        cats = [c for c in m.group(1).split("|") if c] or None
        return posts_snippet(posts, cats, int(m.group(2)))
    text = re.sub(r"<!--POSTS:([^:]*):(\d+)-->", repl, text)
    text = re.sub(r"<!--IFPOSTS-->(.*?)<!--/IFPOSTS-->",
                  lambda m: m.group(1) if 'class="post-card' in m.group(1) else "", text, flags=re.S)
    return text


def build_pages(posts):
    built = []
    d = os.path.join(ROOT, "_build", "stranky")
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".html"):
            continue
        raw = open(os.path.join(d, fn), encoding="utf-8").read()
        m = re.match(r"^<!--\s*(\{.*?\})\s*-->\s*\n(.*)$", raw, re.S)
        meta = json.loads(m.group(1))
        body = render_fragment(m.group(2), posts)
        items = [("Úvod", "/"), (meta["crumb"], meta["path"])]
        ld = [crumbs_ld(items)]
        if meta.get("ld"):
            ld.append(meta["ld"])
        faq = re.findall(r"<summary>(.*?)</summary>\s*<p>(.*?)</p>", body, re.S)
        if faq:
            ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": strip_tags(q),
                 "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in faq]})
        page = head(meta["title"], meta["description"], meta["path"], extra_ld=ld)
        page += header(meta["path"])
        page += "\n<main>\n" + body.replace("{{CRUMBS}}", crumbs(items)) + "\n</main>\n"
        if meta.get("cta", True):
            page += cta_band()
        page += footer()
        write(meta["path"], page)
        built.append(meta["path"])
    return built


def update_home(posts):
    """Na homepage obnoví sekci „Z blogu“ mezi značkami <!-- BLOG:START --> a <!-- BLOG:END -->."""
    fn = os.path.join(ROOT, "index.html")
    s = open(fn, encoding="utf-8").read()
    if "<!-- BLOG:START -->" not in s:
        return
    if posts:
        block = f"""<!-- BLOG:START -->
<section class="sec home-blog" id="blog">
  <div class="sec-index"><b>06</b> — Blog</div>
  <div class="wrap">
    <div class="sec-head">
      <span class="kicker reveal">Z blogu</span>
      <h2 class="split"><span class="ln"><span class="li">Hypotéky <em class="acc">srozumitelně.</em></span></span></h2>
    </div>
    <div class="blog-grid">
      {''.join(post_card(p) for p in posts[:3])}
    </div>
    <a href="/blog/" class="more-link reveal">Všechny články <span>→</span></a>
  </div>
</section>
<!-- BLOG:END -->"""
    else:
        block = "<!-- BLOG:START -->\n<!-- BLOG:END -->"
    s = re.sub(r"<!-- BLOG:START -->.*?<!-- BLOG:END -->", block, s, flags=re.S)
    with open(fn, "w", encoding="utf-8") as f:
        f.write(s)


def main():
    src = os.path.join(ROOT, "_clanky")
    allposts = [parse_post(os.path.join(src, f)) for f in sorted(os.listdir(src)) if f.endswith(".md")] if os.path.isdir(src) else []
    slugs = [p["slug"] for p in allposts]
    dup = {s for s in slugs if slugs.count(s) > 1}
    if dup:
        raise SystemExit(f"Duplicitní slug: {dup}")
    for p in allposts:
        if p["kategorie"] not in KATEGORIE:
            print(f"  ! neznámá kategorie '{p['kategorie']}' v {p['slug']}")
    posts = [p for p in allposts if not p["draft"] and (INCLUDE_FUTURE or p["published"] <= NOW)]
    posts.sort(key=lambda p: p["published"], reverse=True)

    # smaže vygenerované složky článků, které už nemají být venku (např. přesunuté datum)
    blog_dir = os.path.join(ROOT, "blog")
    if os.path.isdir(blog_dir):
        keep = {p["slug"] for p in posts}
        for name in os.listdir(blog_dir):
            if os.path.isdir(os.path.join(blog_dir, name)) and name not in keep:
                shutil.rmtree(os.path.join(blog_dir, name))

    for p in posts:
        build_post(p, posts)
    build_blog_index(posts)
    pages = build_pages(posts)
    build_feed(posts)
    build_sitemap(posts, pages)
    update_home(posts)
    upcoming = sorted([p for p in allposts if p not in posts and not p["draft"]], key=lambda p: p["published"])
    print(f"Zveřejněno: {len(posts)} článků · naplánováno: {len(upcoming)}")
    if upcoming:
        print(f"Další: {upcoming[0]['published']:%d.%m.%Y %H:%M} – {upcoming[0]['title']}")


if __name__ == "__main__":
    main()
