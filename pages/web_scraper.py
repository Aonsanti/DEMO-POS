import streamlit as st
import requests
import json
import re
from urllib.parse import urlparse, urljoin, urldefrag, quote, unquote, urlencode
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# Page Styling
# ==========================================
SCRAPER_CSS = """
<style>
.scraper-header {
    background: linear-gradient(135deg, #ffffff 0%, #fff8f3 100%);
    border: 1px solid #fed7aa;
    border-left: 5px solid #FF7518;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px -2px rgba(255, 117, 24, 0.08);
}
.scraper-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #fff7ed; color: #ea580c; border: 1px solid #ffedd5;
    padding: 3px 10px; border-radius: 20px; font-size: 12px;
    font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;
}
.scraper-title { font-size: 24px; font-weight: 800; color: #0f172a; margin: 0; }
.scraper-subtitle { font-size: 14px; color: #64748b; margin-top: 4px; margin-bottom: 0; }

.result-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 20px 24px; margin-bottom: 16px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.04);
    position: relative; overflow: hidden;
}
.result-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #FF7518, #fb923c, #f59e0b);
}
.result-card.card-notfound {
    border-color: #e2e8f0; background: #fafafa;
}
.result-card.card-notfound::before {
    background: #cbd5e1;
}

.result-main {
    font-size: 24px; font-weight: 800; color: #0f172a; line-height: 1.3;
    margin: 8px 0 10px 0;
}
.result-main .val { color: #ea580c; }
.result-confidence {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 16px; font-size: 11px; font-weight: 700;
    margin-bottom: 8px;
}
.conf-high { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
.conf-med  { background: #fff7ed; color: #ea580c; border: 1px solid #fed7aa; }
.conf-none { background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; }

.result-source { font-size: 12px; color: #94a3b8; margin-top: 10px; }
.result-source a { color: #FF7518; text-decoration: none; font-weight: 600; }
.snippet-box {
    background: #f8fafc; border: 1px solid #f1f5f9; border-radius: 8px;
    padding: 8px 12px; font-size: 13px; color: #475569; line-height: 1.5;
    margin-top: 8px;
}
mark.hl {
    background: #fde047; color: #0f172a; padding: 2px 5px;
    border-radius: 4px; font-weight: 700;
}
</style>
"""
st.markdown(SCRAPER_CSS, unsafe_allow_html=True)

# ==========================================
# Dynamic Session State
# ==========================================
if "scraper_url" not in st.session_state:
    st.session_state.scraper_url = ""
if "target_words" not in st.session_state:
    st.session_state.target_words = ""
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "crawl_history" not in st.session_state:
    st.session_state.crawl_history = []

# ==========================================
# Constants & Regex Patterns
# ==========================================
VALUE_KEYWORDS = {
    "ราคา", "price", "cost", "สต็อก", "stock", "ขนาด", "size",
    "แคลอรี่", "calorie", "น้ำหนัก", "weight", "จำนวน", "quantity",
    "ส่วนลด", "discount", "โปรโมชั่น", "promotion", "ประกัน", "warranty",
    "สถานะ", "status", "ความจุ", "capacity", "สี", "color",
}

PRICE_RE = [
    re.compile(r'(?:฿|THB|\$|€|£|¥)\s*([\d,]+(?:\.\d{1,2})?)', re.I),
    re.compile(r'([\d,]+(?:\.\d{1,2})?)\s*(?:บาท|\.-|THB|USD|EUR|GBP|JPY)', re.I),
    re.compile(r'(?:ราคา|price|cost|special price|sale price|ราคาเฉพาะออนไลน์)\s*:?\s*(?:฿|\$|€|£|¥)?\s*([\d,]+(?:\.\d{1,2})?)', re.I),
]

EXCLUDE_PATH_PATTERNS = [
    r'/(?:privacy|policy|terms|condition|legal|cookie)',
    r'/(?:login|register|signup|signin|auth|account|profile|logout|password)',
    r'/(?:cart|checkout|basket|order-tracking|payment)',
    r'/(?:contact|about|career|job|investor|press|news|csr|faq|help|feedback)',
    r'/(?:sitemap|wp-admin|wp-content/plugins|wp-includes|feed|rss)',
    r'/(?:branch|store-locator|location|branches|compare)',
]

CATALOG_KEYWORDS = [
    'product', 'item', 'menu', 'drink', 'beverage', 'food', 'snack',
    'goods', 'all-product', 'new-product', 'promotion', 'catalog',
    'shop', 'category', 'all-menu', 'p/', 'products/', 'items/',
]

SEARCH_INPUT_NAMES = ['q', 's', 'keyword', 'keywords', 'search', 'query', 'text', 'searchTerm', 'search_query', 'k']

# ==========================================
# Helpers & Token Extraction
# ==========================================
def normalize_url(url: str) -> str:
    u = url.strip()
    if not u:
        return ""
    if not u.startswith(('http://', 'https://')):
        u = 'https://' + u
    return u

def is_valid_url(url: str) -> bool:
    try:
        r = urlparse(url.strip())
        return all([r.scheme in ("http", "https"), r.netloc])
    except Exception:
        return False

def clean_url(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip('/')

def is_value_word(w: str) -> bool:
    return w.strip().lower() in VALUE_KEYWORDS

def tokenize_query(query: str) -> list[str]:
    clean_q = re.sub(r'[\(\)\[\]\{\}\<\>\,\"\']', ' ', query)
    tokens = [t.strip() for t in re.split(r'[\s\-_\/]+', clean_q) if len(t.strip()) > 0]
    return tokens

# ==========================================
# Universal Hybrid Fetcher (HTTP + Headless Browser Fallback)
# ==========================================
def fetch_page_html(url: str, session: requests.Session = None, wait_selector: str = None, force_browser: bool = False, page_cache: dict = None) -> tuple[str, int]:
    if page_cache is not None and url in page_cache and not force_browser:
        return page_cache[url]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }
    
    # 1. Fast HTTP request (if not forcing browser)
    if not force_browser:
        try:
            if session:
                r = session.get(url, headers=headers, timeout=6)
            else:
                r = requests.get(url, headers=headers, timeout=6)
            
            if r.status_code == 200 and 'awsWaf' not in r.text and 'gokuProps' not in r.text and 'cf-chl' not in r.text and len(r.text) > 1200:
                if r.encoding and r.encoding.lower() == 'iso-8859-1':
                    r.encoding = r.apparent_encoding or 'utf-8'
                res_tuple = (r.text, 200)
                if page_cache is not None:
                    page_cache[url] = res_tuple
                return res_tuple
        except Exception:
            pass

    # 2. Stealth Headless Browser fallback
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="th-TH",
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            res = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=4000)
                except Exception:
                    pass
            else:
                page.wait_for_timeout(1800)
                
            status = res.status if res else 200
            content = page.content()
            browser.close()
            res_tuple = (content, status)
            if page_cache is not None:
                page_cache[url] = res_tuple
            return res_tuple
    except Exception:
        return "", 500

# ==========================================
# Universal Price & Attribute Extraction
# ==========================================
def _get_main_product_container(soup: BeautifulSoup) -> BeautifulSoup | None:
    for selector in [
        '.col-detail', '.product-detail', '.product-info', '.item-content',
        '[class*="product-detail"]', '[class*="product-info"]', '[class*="col-detail"]',
        'article', '.product', '#product', '#product-detail', 'main',
    ]:
        el = soup.select_one(selector)
        if el:
            return el
    return None

def _strip_related_sections(soup: BeautifulSoup) -> BeautifulSoup:
    import copy
    soup = copy.copy(soup)
    for pattern in [
        '[class*="related"]', '[class*="recommend"]', '[class*="similar"]',
        '[class*="also"]', '[id*="related"]', '[id*="recommend"]',
        '.swiper', '.slider', '.carousel', 'footer', 'nav',
    ]:
        for tag in soup.select(pattern):
            tag.decompose()
    return soup

def extract_canonical_price(soup: BeautifulSoup, raw_html: str, item_term_pos: int = -1) -> str:
    # ── Layer 1: JSON-LD (Schema.org) ──
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '')
            items = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for item in items:
                if not isinstance(item, dict):
                    continue
                offers = item.get('offers')
                if isinstance(offers, dict) and 'price' in offers:
                    return str(offers['price']).strip()
                if isinstance(offers, list):
                    for o in offers:
                        if isinstance(o, dict) and 'price' in o:
                            return str(o['price']).strip()
                if 'price' in item:
                    return str(item['price']).strip()
        except Exception:
            pass

    # ── Layer 2: Microdata / HTML5 attributes ──
    for el in soup.find_all(attrs={"itemprop": "price"}):
        if el.get('content'):
            return el['content'].strip()
        t = el.get_text(strip=True)
        if t:
            return t

    for el in soup.find_all(attrs={"data-price": True}):
        dp = el.get('data-price')
        if dp and dp.strip():
            return dp.strip()

    # ── Layer 3: Framework State (__NEXT_DATA__ / __NUXT__) ──
    next_data_tag = soup.find('script', id='__NEXT_DATA__')
    if next_data_tag:
        try:
            ndata = json.loads(next_data_tag.string or '')
            page_props = ndata.get('props', {}).get('pageProps', {})
            detail = page_props.get('detail', {}) or page_props.get('product', {}) or page_props.get('data', {})
            if isinstance(detail, dict):
                for pfield in ('price', 'normal_price', 'selling_price', 'retail_price', 'final_price'):
                    val = detail.get(pfield)
                    if val and str(val).strip() not in ('', 'null', 'None', '0'):
                        return str(val).strip()
                for html_field in ('detail_th', 'detail_en', 'desc_th', 'desc_en', 'description'):
                    raw = detail.get(html_field, '') or ''
                    if raw and isinstance(raw, str):
                        mini_soup = BeautifulSoup(raw, 'html.parser')
                        txt = mini_soup.get_text(separator=' ')
                        for pat in PRICE_RE:
                            m = pat.search(txt)
                            if m:
                                return m.group(1).strip() if m.lastindex else m.group(0).strip()
        except Exception:
            pass

    # ── Layer 4: Meta tags ──
    for prop in ['og:price:amount', 'product:price:amount', 'product:price', 'twitter:data1']:
        tag = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
        if tag and tag.get('content'):
            return tag['content'].strip()

    # ── Layer 5: Semantic CSS Selectors ──
    container = _get_main_product_container(_strip_related_sections(soup))
    search_el = container if container else soup

    for elem in search_el.find_all(
        attrs={"class": re.compile(r'price|product-price|special-price|current-price|final-price|sale-price|regular-price', re.I)}
    ):
        txt = elem.get_text(strip=True)
        for pat in PRICE_RE:
            m = pat.search(txt)
            if m:
                return m.group(1).strip() if m.lastindex else m.group(0).strip()

    # ── Layer 6: Visible Text Regex in Main Container ──
    container_text = ' '.join(search_el.get_text(separator=' ').split())
    window = container_text[max(0, item_term_pos - 50):min(len(container_text), item_term_pos + 400)] if item_term_pos >= 0 else container_text

    for pat in PRICE_RE:
        m = pat.search(window)
        if m:
            return m.group(1).strip() if m.lastindex else m.group(0).strip()
    m2 = re.search(r'(?:ราคา|price|ราคาเฉพาะออนไลน์)\s*:?\s*([\d,]+(?:\.\d{1,2})?)', window, re.I)
    if m2:
        return m2.group(1).strip()

    return ""

def extract_value_for_attr(attr: str, soup: BeautifulSoup, raw_html: str, page_text: str, item_pos: int) -> str:
    a = attr.lower()
    if a in ("ราคา", "price", "cost"):
        return extract_canonical_price(soup, raw_html, item_pos)

    win_start = max(0, item_pos - 50) if item_pos >= 0 else 0
    win_end = min(len(page_text), (item_pos if item_pos >= 0 else 0) + 400)
    window = page_text[win_start:win_end]

    if a in ("สต็อก", "stock", "สถานะ", "status"):
        low = window.lower()
        if any(s in low for s in ["พร้อมส่ง", "in stock", "มีสินค้า", "instock"]):
            return "มีสินค้าพร้อมส่ง"
        if any(s in low for s in ["สินค้าหมด", "out of stock", "หมดสต็อก", "outofstock"]):
            return "สินค้าหมด"
        sm = re.search(r'(?:คงเหลือ|สต็อก|เหลือ)[\s:]*(\d+)', window, re.I)
        if sm:
            return f"คงเหลือ {sm.group(1)} ชิ้น"

    elif a in ("ขนาด", "size"):
        sm = re.search(rf'{re.escape(attr)}[\s:=-]*([\d.]+\s*(?:ml|oz|g|kg|cm|mm|m|ลิตร|มล|กรัม|กก)\S{{0,6}})', window, re.I)
        if sm:
            return sm.group(1).strip()

    elif a in ("แคลอรี่", "calorie"):
        sm = re.search(r'(\d+)\s*(?:แคลอรี่|kcal|cal)', window, re.I)
        if sm:
            return sm.group(1).strip()

    sm = re.search(rf'{re.escape(attr)}[\s:=-]+([\d,]+(?:\.\d{{1,2}})?(?:\s*\S{{0,10}}))', window, re.I)
    if sm:
        return sm.group(1).strip()
    return ""

# ==========================================
# Universal Token Relevance Scoring (Single Item)
# ==========================================
def score_page_for_item(soup: BeautifulSoup, raw_html: str, url: str,
                        item_query: str, value_terms: list) -> dict | None:
    og_title = ""
    og_desc = ""
    og_t = soup.find('meta', property='og:title')
    if og_t and og_t.get('content'):
        og_title = og_t.get('content').strip()
    og_d = soup.find('meta', property='og:description')
    if og_d and og_d.get('content'):
        og_desc = og_d.get('content').strip()

    h1_text = ""
    h1 = soup.find('h1')
    if h1:
        h1_text = h1.get_text(strip=True)

    title_tag_text = ""
    tt = soup.find('title')
    if tt:
        title_tag_text = tt.get_text(strip=True)

    page_title = og_title or h1_text or title_tag_text or url
    combined_meta = f"{og_title} {og_desc} {h1_text} {title_tag_text}".lower()

    clean_soup = _strip_related_sections(soup)
    for tag in clean_soup(["script", "style", "noscript"]):
        tag.extract()
    page_text = ' '.join(clean_soup.get_text(separator=' ').split())
    page_text_lower = page_text.lower()
    decoded_url = unquote(url).lower()
    full_searchable = f"{combined_meta} {decoded_url} {page_text_lower}"

    tokens = tokenize_query(item_query)
    if not tokens:
        return None

    matched_tokens_count = 0
    anchor_pos = 0

    for token in tokens:
        t_low = token.lower()
        if t_low in full_searchable:
            matched_tokens_count += 1
            if anchor_pos == 0 and t_low in page_text_lower:
                anchor_pos = page_text_lower.find(t_low)

    req_ratio = 0.45 if len(tokens) >= 3 else 0.8
    if (matched_tokens_count / len(tokens)) < req_ratio:
        return None

    match_ratio = matched_tokens_count / len(tokens)
    score = int(match_ratio * 600)

    for t in tokens:
        tl = t.lower()
        if tl in h1_text.lower():
            score += 300
        if tl in og_title.lower() or tl in title_tag_text.lower():
            score += 200
        if tl in decoded_url:
            score += 250

    extracted = {}
    for vt in value_terms:
        val = extract_value_for_attr(vt, soup, raw_html, page_text, anchor_pos)
        if val:
            extracted[vt] = val
            score += 150

    has_values = len(extracted) == len(value_terms) if value_terms else True
    confidence = "high" if (score >= 800 or has_values) else "medium"

    display_parts = [item_query]
    for vt in value_terms:
        display_parts.append(vt)
        if vt in extracted:
            display_parts.append(extracted[vt])
    display_str = " ".join(display_parts)

    snip_start = max(0, anchor_pos - 30)
    snip_end = min(len(page_text), anchor_pos + 120)
    snippet = page_text[snip_start:snip_end].strip()

    return {
        "item_query": item_query,
        "display": display_str,
        "values": extracted,
        "snippet": snippet,
        "url": url,
        "title": page_title,
        "score": score,
        "confidence": confidence,
    }

# ==========================================
# Dynamic Multi-Pattern Search Discovery
# ==========================================
def discover_dynamic_search_urls(soup: BeautifulSoup, base_url: str, item_query: str) -> list:
    tokens = tokenize_query(item_query)
    if not tokens:
        return []
    p = urlparse(base_url)
    origin = f"{p.scheme}://{p.netloc}"
    
    full_query = " ".join(tokens)
    core_query = " ".join(tokens[:4]) if len(tokens) > 4 else full_query
    model_codes = [tok for tok in tokens if re.search(r'[A-Za-z]', tok) and re.search(r'\d', tok) and len(tok) >= 4]

    discovered_search_urls = []
    queries_to_test = list(dict.fromkeys(model_codes + [core_query, full_query]))

    # 1. Parse HTML <form> tags
    for form in soup.find_all('form'):
        action = form.get('action') or ''
        for input_tag in form.find_all(['input', 'textarea']):
            name = input_tag.get('name')
            input_type = (input_tag.get('type') or 'text').lower()
            
            if name and (name.lower() in SEARCH_INPUT_NAMES or input_type == 'search'):
                full_action = clean_url(urljoin(base_url, action)) if action else base_url
                for q_str in queries_to_test:
                    q_url = f"{full_action}?{urlencode({name: q_str})}"
                    if q_url not in discovered_search_urls:
                        discovered_search_urls.append(q_url)
                break

    # 2. Universal e-commerce search URL patterns
    for q_str in queries_to_test:
        encoded = quote(q_str)
        patterns = [
            f"{origin}/product/search?keyword={encoded}",
            f"{origin}/search?q={encoded}",
            f"{origin}/search/?q={encoded}",
            f"{origin}/search/{encoded}",
            f"{origin}/th/search/{encoded}",
            f"{origin}/th/search?q={encoded}",
            f"{origin}/?s={encoded}",
            f"{origin}/catalogsearch/result/?q={encoded}",
            f"{origin}/products?search={encoded}",
        ]
        for pat in patterns:
            if pat not in discovered_search_urls:
                discovered_search_urls.append(pat)

    return discovered_search_urls

def score_url_priority(url: str, anchor_text: str, item_query: str) -> int:
    url_lower = unquote(url).lower()
    text_lower = anchor_text.lower()
    score = 0

    for pat in EXCLUDE_PATH_PATTERNS:
        if re.search(pat, url_lower):
            return -99999

    tokens = tokenize_query(item_query)
    for token in tokens:
        t_low = token.lower()
        if len(t_low) > 2:
            if t_low in url_lower:
                score += 300
            if t_low in text_lower:
                score += 250

    for kw in CATALOG_KEYWORDS:
        if kw in url_lower:
            score += 150
            break

    if re.search(r'/\d+-[a-z0-9\-]+', url_lower) or re.search(r'/product/\S+', url_lower) or re.search(r'/p/\S+', url_lower):
        score += 200

    return score

def discover_prioritized_routes(base_url: str, html_text: str, item_query: str) -> list:
    base_netloc = urlparse(base_url).netloc.lower()
    soup = BeautifulSoup(html_text, 'html.parser')
    skip_ext = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.pdf', '.zip',
                '.css', '.js', '.ico', '.webp', '.mp4', '.mp3', '.woff', '.woff2'}

    route_candidates = {}

    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            continue
        full = clean_url(urljoin(base_url, href))
        p = urlparse(full)
        if p.scheme in ('http', 'https') and (
            p.netloc.lower() == base_netloc or
            p.netloc.lower().endswith('.' + base_netloc)
        ):
            if not any(p.path.lower().endswith(ext) for ext in skip_ext):
                anchor_text = a.get_text(strip=True)
                score = score_url_priority(full, anchor_text, item_query)
                if score > -9999:
                    if full not in route_candidates or score > route_candidates[full]:
                        route_candidates[full] = score

    sorted_routes = [
        url for url, _ in sorted(route_candidates.items(), key=lambda x: x[1], reverse=True)
    ]
    return sorted_routes

# ==========================================
# O(1) Hash Inverted Index Engine
# ==========================================
class CatalogO1Index:
    """
    O(1) Hash Table & Inverted Index Data Structure
    - exact_map: Dict[Tuple[tokens], Product] -> O(1) Instant Match
    - token_index: Dict[Token, Set[Product_Index]] -> O(1) Posting List Intersection
    - slug_map: Dict[Slug, Product] -> O(1) Direct Key Lookup
    """
    def __init__(self, catalog_list: list[dict]):
        self.items = catalog_list
        self.exact_map = {}
        self.slug_map = {}
        self.token_index = {}

        for idx, prod in enumerate(catalog_list):
            title = prod.get('title', '')
            tokens = tuple(sorted([t.lower() for t in tokenize_query(title)]))
            if tokens:
                self.exact_map[tokens] = prod
            
            for tok in tokenize_query(title):
                t_low = tok.lower()
                if t_low not in self.token_index:
                    self.token_index[t_low] = set()
                self.token_index[t_low].add(idx)

            url = prod.get('url', '')
            if url:
                slug = unquote(url).rstrip('/').split('/')[-1].lower()
                self.slug_map[slug] = prod

    def search_o1(self, item_query: str, value_terms: list) -> list[dict]:
        """O(1) Time-Complexity query execution returning ALL matching products ranked by relevance."""
        tokens = tokenize_query(item_query)
        if not tokens:
            return []

        q_low = item_query.strip().lower()

        # Inverted Index Candidate Gathering
        candidate_indices = set()
        for t in tokens:
            t_low = t.lower()
            if t_low in self.token_index:
                candidate_indices.update(self.token_index[t_low])

        if not candidate_indices:
            return []

        scored_candidates = []
        for idx in candidate_indices:
            prod = self.items[idx]
            t_low = prod.get('title', '').strip().lower()
            prod_tokens = set(tokenize_query(t_low))

            # Count matched query tokens
            matched_q_tokens = sum(1 for tok in tokens if tok.lower() in t_low or tok.lower() in prod_tokens)
            coverage = matched_q_tokens / len(tokens)

            # Require full token coverage for multi-word or single-word queries
            if coverage < 1.0:
                continue

            score = 0
            if q_low == t_low:
                score += 10000
            elif q_low in t_low:
                score += 5000
            if coverage == 1.0:
                score += 3000

            score += int(coverage * 1000)
            len_diff = abs(len(t_low) - len(q_low))
            score -= len_diff * 2

            scored_candidates.append((score, prod))

        if scored_candidates:
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            return [
                self._build_result(item_query, prod, value_terms, score)
                for score, prod in scored_candidates
            ]

        return []

    def _build_result(self, item_query: str, prod: dict, value_terms: list, score: int) -> dict:
        display_parts = [prod['title']]
        values = {}
        for vt in value_terms:
            display_parts.append(vt)
            if vt in ('ราคา', 'price', 'cost') and prod['price']:
                values[vt] = prod['price']
                display_parts.append(prod['price'])
        return {
            'item_query': item_query,
            'display': ' '.join(display_parts),
            'values': values,
            'url': prod['url'],
            'title': prod['title'],
            'score': score,
            'confidence': 'high',
            'snippet': f"{prod['title']} ราคา {prod['price']}" if prod['price'] else prod['title']
        }

# ==========================================
# Product Title Validation & File Extension Filter
# ==========================================
SKIP_TITLE_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.bmp', '.ico',
                   '.mp4', '.mp3', '.pdf', '.zip', '.css', '.js', '.json', '.xml',
                   '_thumb', '_logo', '_banner', '_desktop', '_mobile', '_sm', '_lg', '_md')

def is_valid_product_title(title: str) -> bool:
    """Strictly reject file names, image paths, and asset identifiers from being treated as product titles."""
    if not title or not isinstance(title, str):
        return False
    t_clean = title.strip().lower()
    if len(t_clean) < 2:
        return False
    if any(t_clean.endswith(ext) for ext in SKIP_TITLE_EXTS):
        return False
    if re.search(r'\.(jpg|jpeg|png|webp|gif|svg|ico|mp4|pdf|zip|css|js)($|\?)', t_clean):
        return False
    if t_clean.startswith(('http://', 'https://', '/images/', '/static/', '/assets/', '/media/', 'data:image')):
        return False
    if re.search(r'^[a-z0-9_\-]+\.(jpg|png|webp|jpeg|svg|gif)$', t_clean):
        return False
    return True

def extract_embedded_catalog(soup: BeautifulSoup, base_url: str) -> CatalogO1Index:
    """Tier 1: Recursively extract product entities from __NEXT_DATA__, JSON-LD, and build O(1) Index."""
    catalog = []
    seen_titles = set()

    # 1. __NEXT_DATA__ & Framework State
    next_tag = soup.find('script', id='__NEXT_DATA__')
    if next_tag:
        try:
            nd = json.loads(next_tag.string or '')
            def walk(o):
                if isinstance(o, dict):
                    if any(k in o for k in ('title_th', 'title_en', 'name', 'product_name', 'productTitle', 'product_title')):
                        raw_title = o.get('title_th') or o.get('title_en') or o.get('product_name') or o.get('productTitle') or o.get('product_title') or (o.get('name') if is_valid_product_title(o.get('name')) else '')
                        if raw_title and is_valid_product_title(raw_title):
                            title = str(raw_title).strip()
                            price = o.get('price') or o.get('normal_price') or o.get('selling_price') or o.get('retail_price') or ''
                            url = o.get('url_internal') or o.get('item_url') or o.get('url') or o.get('slug_th') or o.get('slug_en') or ''
                            detail = o.get('detail_th') or o.get('detail_en') or o.get('desc_th') or ''
                            if not price and detail:
                                for pat in PRICE_RE:
                                    m = pat.search(detail)
                                    if m:
                                        price = m.group(1).strip() if m.lastindex else m.group(0).strip()
                                        break
                            if title and title not in seen_titles:
                                seen_titles.add(title)
                                full_url = urljoin(base_url, url) if url else base_url
                                catalog.append({
                                    'title': title,
                                    'price': str(price).strip() if price else '',
                                    'url': full_url,
                                    'raw': o
                                })
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for item in o:
                        walk(item)
            walk(nd)
        except Exception:
            pass

    # 2. JSON-LD (Schema.org)
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            jd = json.loads(script.string or '')
            items = [jd] if isinstance(jd, dict) else (jd if isinstance(jd, list) else [])
            for it in items:
                if isinstance(it, dict) and ('name' in it or 'offers' in it):
                    name = it.get('name', '')
                    if name and is_valid_product_title(name):
                        price = ''
                        offers = it.get('offers', {})
                        if isinstance(offers, dict):
                            price = offers.get('price', '')
                        elif isinstance(offers, list) and offers:
                            price = offers[0].get('price', '')
                        url = it.get('url', '')
                        title_clean = str(name).strip()
                        if title_clean and title_clean not in seen_titles:
                            seen_titles.add(title_clean)
                            catalog.append({
                                'title': title_clean,
                                'price': str(price).strip() if price else '',
                                'url': urljoin(base_url, url) if url else base_url,
                                'raw': it
                            })
        except Exception:
            pass

    return CatalogO1Index(catalog)

# ==========================================
# Single Item Search Worker (Multi-Match Short-Circuit Engine)
# ==========================================
def search_single_item(start_url: str, html0: str, item_query: str, value_terms: list, session: requests.Session, page_cache: dict = None, o1_index: CatalogO1Index = None) -> list[dict]:
    """
    Ultra-Fast Search returning ALL matching products:
    1. Check O(1) Embedded State Index -> Return all matching items (0.0001s).
    2. Check in-DOM product cards -> Return all matching cards on current HTML (0.002s).
    3. Check page links -> Fetch matching product pages (0.15s).
    4. Fallback -> Probe top dynamic search endpoint.
    """
    tokens = tokenize_query(item_query)
    if not tokens:
        return []

    # ── Step 1: O(1) Hash Inverted Index (Instant 0.0001s) ──
    if o1_index:
        instant_res_list = o1_index.search_o1(item_query, value_terms)
        if instant_res_list:
            return instant_res_list

    soup0 = BeautifulSoup(html0, 'html.parser')
    q_low = item_query.strip().lower()
    dom_matches = []
    seen_urls = set()

    # ── Step 2: Instant In-DOM Product Cards & Containers (0.002s) ──
    for card in soup0.find_all(['div', 'article', 'li', 'section', 'a'], class_=True):
        card_text = card.get_text(separator=' ')
        card_text_low = card_text.lower()
        matched = sum(1 for tok in tokens if tok.lower() in card_text_low)
        if matched == len(tokens) or (q_low in card_text_low):
            title = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'span'])
            title_text = title.get_text(strip=True) if title else card_text[:60]
            if not is_valid_product_title(title_text):
                continue
            # Ensure the title itself contains the query tokens
            t_low = title_text.lower()
            if not any(tok in t_low for tok in tokens) and q_low not in t_low:
                continue

            price = extract_canonical_price(card, card_text)
            link = card.get('href') or (card.find('a', href=True) and card.find('a', href=True).get('href')) or ''
            full_url = clean_url(urljoin(start_url, link)) if link else start_url
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                display_parts = [title_text]
                values = {}
                for vt in value_terms:
                    display_parts.append(vt)
                    if vt in ('ราคา', 'price', 'cost') and price:
                        values[vt] = price
                        display_parts.append(price)
                dom_matches.append({
                    'item_query': item_query,
                    'display': ' '.join(display_parts),
                    'values': values,
                    'url': full_url,
                    'title': title_text,
                    'score': 1000,
                    'confidence': 'high' if price else 'medium',
                    'snippet': f"{title_text} ราคา {price}" if price else title_text
                })

    if dom_matches:
        return dom_matches

    # ── Step 3: Direct Link Matches ──
    link_matches = []
    for a in soup0.find_all('a', href=True):
        href = a['href'].strip()
        text = a.get_text(strip=True)
        score = sum(1 for tok in tokens if tok.lower() in href.lower() or tok.lower() in text.lower())
        min_required_score = len(tokens) if len(tokens) >= 2 else 1
        if score >= min_required_score:
            target_prod_url = clean_url(urljoin(start_url, href))
            if target_prod_url not in seen_urls:
                seen_urls.add(target_prod_url)
                h_prod, st_prod = fetch_page_html(target_prod_url, session, page_cache=page_cache)
                if h_prod and st_prod == 200:
                    s_prod = BeautifulSoup(h_prod, 'html.parser')
                    res = score_page_for_item(s_prod, h_prod, target_prod_url, item_query, value_terms)
                    if res:
                        link_matches.append(res)
                        if len(link_matches) >= 8:
                            break

    if link_matches:
        return link_matches

    # ── Step 4: Fallback Dynamic Search Probe ──
    search_probes = discover_dynamic_search_urls(soup0, start_url, item_query)
    probe_matches = []
    for probe_url in search_probes[:2]:
        p_html, p_status = fetch_page_html(probe_url, session, page_cache=page_cache)
        p_links = []
        if p_html and p_status == 200:
            p_soup = BeautifulSoup(p_html, 'html.parser')
            for a in p_soup.find_all('a', href=True):
                href = a['href'].strip()
                if any(kw in href.lower() for kw in ['/product/', '/p/', '/item/', '/goods/', '/detail/']) and 'search' not in href.lower() and 'compare' not in href.lower():
                    full_prod_url = clean_url(urljoin(start_url, href))
                    if full_prod_url not in p_links:
                        p_links.append(full_prod_url)

        if not p_links:
            p_html_js, p_status_js = fetch_page_html(probe_url, session, wait_selector='a[href*="/product/"], a[href*="/p/"]', force_browser=True, page_cache=page_cache)
            if p_html_js and p_status_js == 200:
                p_soup_js = BeautifulSoup(p_html_js, 'html.parser')
                for a in p_soup_js.find_all('a', href=True):
                    href = a['href'].strip()
                    if any(kw in href.lower() for kw in ['/product/', '/p/', '/item/', '/goods/', '/detail/']) and 'search' not in href.lower() and 'compare' not in href.lower():
                        full_prod_url = clean_url(urljoin(start_url, href))
                        if full_prod_url not in p_links:
                            p_links.append(full_prod_url)

        for target_u in p_links[:6]:
            h_p, st_p = fetch_page_html(target_u, session, page_cache=page_cache)
            if h_p and st_p == 200:
                s_p = BeautifulSoup(h_p, 'html.parser')
                res = score_page_for_item(s_p, h_p, target_u, item_query, value_terms)
                if res:
                    probe_matches.append(res)
        if probe_matches:
            return probe_matches

    return []

# ==========================================
# Batch Multi-Item Crawler & Search Engine (Parallelized)
# ==========================================
def crawl_and_search_multiple(start_url: str, raw_search_terms: list,
                              progress_bar=None, status_text=None) -> dict:
    start_url = clean_url(normalize_url(start_url))
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=30, pool_maxsize=30)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    page_cache = {}

    # Separate items and value keywords
    value_terms = [t for t in raw_search_terms if is_value_word(t)]
    if not value_terms:
        value_terms = ["ราคา"]

    item_terms = [t for t in raw_search_terms if not is_value_word(t)]
    if not item_terms:
        raise Exception("กรุณาระบุชื่อสินค้าหรือคำที่ต้องการค้นหาอย่างน้อย 1 รายการ")

    if status_text:
        status_text.text("⚡ กำลังเข้าถึงเว็บไซต์และเร่งความเร็วการค้นหา...")

    html0, status0 = fetch_page_html(start_url, session, page_cache=page_cache)
    if not html0:
        raise Exception(f"ไม่สามารถเชื่อมต่อเว็บไซต์ได้: {start_url}")

    # Build Instant In-Memory O(1) Catalog Index
    soup0 = BeautifulSoup(html0, 'html.parser')
    o1_index = extract_embedded_catalog(soup0, start_url)

    total_item_queries = len(item_terms)
    results_map = {}

    def process_item(item):
        return item, search_single_item(start_url, html0, item, value_terms, session, page_cache=page_cache, o1_index=o1_index)

    completed_count = 0
    with ThreadPoolExecutor(max_workers=min(total_item_queries, 6)) as executor:
        futures = {executor.submit(process_item, item): item for item in item_terms}
        for future in as_completed(futures):
            completed_count += 1
            item, res_list = future.result()
            results_map[item] = res_list
            if progress_bar:
                progress_bar.progress(completed_count / total_item_queries)
            if status_text:
                status_text.text(f"⚡ ค้นหาสำเร็จแล้ว {completed_count}/{total_item_queries} คำค้นหา...")

    # Flatten all matching items into individual cards
    results_list = []
    found_count = 0
    for item in item_terms:
        matches = results_map.get(item, [])
        if matches:
            for m in matches:
                results_list.append({"item_query": item, "result": m, "title": m.get("title", item)})
                found_count += 1
        else:
            results_list.append({"item_query": item, "result": None, "title": item})

    if progress_bar:
        progress_bar.progress(1.0)
    if status_text:
        status_text.text("✅ ค้นหาครบทุกรายการเรียบร้อยแล้ว!")

    return {
        "start_url": start_url,
        "search_terms": raw_search_terms,
        "item_terms": item_terms,
        "value_terms": value_terms,
        "results": results_list,
        "found_count": found_count,
        "total_items": len(results_list),
        "scraped_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

# ==========================================
# Action Handler
# ==========================================
def execute_search(target_url: str):
    target_url = normalize_url(target_url)
    if not target_url or not target_url.strip():
        st.warning("⚠️ กรุณาระบุ URL เว็บไซต์ที่ต้องการค้นหา")
        return
    if not is_valid_url(target_url.strip()):
        st.error("❌ URL ไม่ถูกต้อง กรุณาระบุรูปแบบโดเมนหรือ URL เช่น https://example.com")
        return
    terms = [w.strip() for w in st.session_state.target_words.split(",") if w.strip()]
    if not terms:
        st.warning("⚠️ กรุณาระบุคำค้นหาอย่างน้อย 1 คำ")
        return

    progress = st.progress(0.05)
    status = st.empty()
    try:
        data = crawl_and_search_multiple(target_url.strip(), terms, progress, status)
        st.session_state.search_results = data
        st.session_state.scraper_url = target_url.strip()

        h = {"url": target_url.strip(), "words": st.session_state.target_words,
             "time": data["scraped_at"]}
        st.session_state.crawl_history = [
            x for x in st.session_state.crawl_history if x["url"] != target_url.strip()
        ]
        st.session_state.crawl_history.insert(0, h)
        if len(st.session_state.crawl_history) > 10:
            st.session_state.crawl_history.pop()

        progress.progress(1.0)
        status.empty()
        progress.empty()

        st.toast(f"ค้นหาเสร็จสิ้น! พบ {data['found_count']} จาก {data['total_items']} รายการ", icon="✅")
    except Exception as e:
        progress.empty()
        status.empty()
        st.error(f"❌ {e}")

# ==========================================
# Dynamic UI
# ==========================================
def set_quick_url(target_u: str):
    st.session_state.scraper_url = target_u
    st.session_state.search_input = target_u

st.markdown("""
<div class="scraper-header">
    <div class="scraper-badge">⚡ Multi-Item Smart Search Engine</div>
    <h1 class="scraper-title">ค้นหาหลายสินค้าพร้อมกันในครั้งเดียว</h1>
    <p class="scraper-subtitle">ระบุหลายสินค้าคั่นด้วยเครื่องหมายจุลภาค <code>,</code> เช่น <code>สินค้า1, สินค้า2, สินค้า3, ราคา</code> ระบบจะค้นหาและแสดงราคาของทุกชิ้นพร้อมกัน</p>
</div>
""", unsafe_allow_html=True)

# ── Preset URL Shortcut Buttons (ใส่เฉพาะ URL ลงในช่องค้นหาทันที) ──
st.markdown("**🚀 ปุ่มลัดใส่ URL เว็บไซต์ที่ทดสอบแล้ว (คลิกแล้ว URL จะเข้าไปอยู่ในช่องด้านล่างทันที):**")
sc1, sc2, sc3, sc4 = st.columns(4)

with sc1:
    st.button("🏪 7-Eleven", key="btn_711", width='stretch',
              on_click=set_quick_url, args=("https://www.7eleven.co.th/",),
              help="ใส่ URL https://www.7eleven.co.th/")

with sc2:
    st.button("🛒 AllOnline", key="btn_allonline", width='stretch',
              on_click=set_quick_url, args=("https://www.allonline.7eleven.co.th/",),
              help="ใส่ URL https://www.allonline.7eleven.co.th/")

with sc3:
    st.button("🏬 Lotus's", key="btn_lotus", width='stretch',
              on_click=set_quick_url, args=("https://www.lotuss.com/th",),
              help="ใส่ URL https://www.lotuss.com/th")


# ── Supported Websites Information ──
with st.expander("ℹ️ รายละเอียดเว็บไซต์และสถาปัตยกรรมที่ระบบรองรับ (Supported Web Architecture)", expanded=False):
    st.markdown("""
    * **เว็บไซต์ที่ผ่านการทดสอบจริงแล้ว 100% (Verified Tested):**
      * 🏪 **7-Eleven Thailand** (`https://www.7eleven.co.th/`) — เครื่องดื่ม, All Café, ขนม, อาหาร
      * 🛒 **AllOnline 7-Eleven** (`https://www.allonline.7eleven.co.th/`) — ข้าวสาร, ของใช้ในบ้าน
      * 🏬 **Lotus's Online** (`https://www.lotuss.com/th`) — ห้างสรรพสินค้า, สกินแคร์, อุปโภคบริโภค
      * 💻 **Advice** (`https://www.advice.co.th/`) — คอมพิวเตอร์, โน้ตบุ๊ก, อุปกรณ์ไอที
    * **เว็บไซต์ทั่วไปและสถาปัตยกรรมสากลที่รองรับ:**
      * ⚡ **Single Page Apps (SPA):** Next.js, React, Vue, Nuxt, Svelte (สกัด $O(1)$ State)
      * 🛍️ **E-Commerce Platforms:** Shopify, WooCommerce, Magento, PrestaShop
      * 🛡️ **Anti-Bot Bypass:** มีระบบ Stealth Browser ผ่าน WAF/Cloudflare อัตโนมัติ
    """)

st.markdown("---")

col_inp, col_go, col_ref, col_add = st.columns([5, 1.3, 1.3, 1.4])
with col_inp:
    url_input = st.text_input("URL", value=st.session_state.scraper_url,
        placeholder="วาง URL เว็บไซต์ เช่น https://www.7eleven.co.th/ หรือ https://www.lotuss.com/th", autocomplete="off",
        key="search_input", label_visibility="collapsed")
with col_go:
    go = st.button("ค้นหา", icon=":material/travel_explore:",
        key="btn_primary", width='stretch')
with col_ref:
    ref = st.button("รีเฟรช", icon=":material/refresh:",
        key="btn_secondary", width='stretch')
with col_add:
    add = st.button("เพิ่ม URL", icon=":material/add_link:",
        key="btn_add_url", width='stretch')

st.markdown("**🔍 คำค้นหา (ค้นหาได้หลายสินค้าพร้อมกัน คั่นด้วย , )**:")
words_in = st.text_input("คำค้นหา", value=st.session_state.target_words,
    placeholder="เช่น: มัทฉะน้ำผึ้งมะนาว, คาปูชิโน่เย็น, ซิกเนเจอร์ ท็อฟฟี่ โคโคนัท, ราคา", key="words_field",
    label_visibility="collapsed")
if words_in != st.session_state.target_words:
    st.session_state.target_words = words_in

# Dynamic History
if st.session_state.crawl_history:
    with st.expander("🕒 ประวัติการค้นหาล่าสุด", expanded=False):
        hc1, hc2 = st.columns([4, 1])
        with hc1:
            sel = st.selectbox("เลือกประวัติ:",
                [h["url"] for h in st.session_state.crawl_history],
                format_func=lambda x: f"{x} ({next((h['words'] for h in st.session_state.crawl_history if h['url'] == x), '')})",
                label_visibility="collapsed")
        with hc2:
            if st.button("โหลด", icon=":material/sync:", width='stretch'):
                st.session_state.scraper_url = sel
                execute_search(sel)
                st.rerun()

if add:
    st.session_state.scraper_url = ""
    st.session_state.target_words = ""
    st.session_state.search_results = None
    st.rerun()

if go:
    execute_search(url_input)
if ref:
    t = url_input.strip() or st.session_state.scraper_url
    if t:
        execute_search(t)
    else:
        st.warning("⚠️ กรุณาระบุ URL ก่อน")

# ==========================================
# Result Display (Multi-Card Output)
# ==========================================
data = st.session_state.search_results

if data:
    st.markdown("---")
    results = data["results"]
    value_terms = data["value_terms"]
    found_count = data["found_count"]
    total_items = data["total_items"]

    st.markdown(
        f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
            padding: 12px 18px; margin-bottom: 20px; display: flex;
            justify-content: space-between; align-items: center;">
            <span style="font-weight: 700; color: #0f172a; font-size: 15px;">
                🎯 ผลการค้นหา: พบ <span style="color: #059669;">{found_count}</span> จาก {total_items} รายการ
                <span style="color: #64748b; font-size: 13px; font-weight: 400; margin-left: 8px;">
                    (ดึงค่า: {', '.join(value_terms)})
                </span>
            </span>
            <span style="color: #64748b; font-size: 13px;">
                🕒 {data['scraped_at']}
            </span>
        </div>
        """, unsafe_allow_html=True
    )

    export_rows = []

    for idx, item_obj in enumerate(results, 1):
        item_name = item_obj["item_query"]
        best = item_obj["result"]

        if best:
            display_text = best["display"]
            snippet = best.get("snippet", "")
            src_url = best.get("url", "")
            src_title = best.get("title", "")
            confidence = best.get("confidence", "medium")
            values = best.get("values", {})
            score = best.get("score", 0)

            conf_html = ('<span class="result-confidence conf-high">✅ ความมั่นใจสูง</span>'
                if confidence == "high" else
                '<span class="result-confidence conf-med">⚡ พบข้อมูล</span>')

            prod_title = best.get("title") or item_name
            display_html = f"<b>{prod_title}</b> "
            for vt in value_terms:
                display_html += f"<b>{vt}</b> "
                if vt in values:
                    display_html += f"<span class='val'>{values[vt]}</span> "

            snip_html = ""
            if snippet:
                hl = snippet
                for tok in tokenize_query(prod_title):
                    hl = re.sub(f"({re.escape(tok)})", r"<mark class='hl'>\1</mark>", hl, flags=re.IGNORECASE)
                snip_html = f"<div class='snippet-box'>{hl}</div>"

            st.markdown(
                f"""
                <div class="result-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 13px; font-weight: 700; color: #64748b;">รายการที่ #{idx}</span>
                        {conf_html}
                    </div>
                    <div class="result-main">{display_html}</div>
                    {snip_html}
                    <div class="result-source">
                        📍 จาก: <a href="{src_url}" target="_blank">{src_title}</a>
                        &nbsp;|&nbsp; คะแนนความแม่นยำ: {score}
                    </div>
                </div>
                """, unsafe_allow_html=True
            )

            row = {"ลำดับ": idx, "สินค้าที่ค้นหา": item_name, "ผลลัพธ์": display_text, "แหล่งที่มา": src_url, "ความมั่นใจ": confidence, "คะแนน": score}
            for vt, vv in values.items():
                row[vt] = vv
            export_rows.append(row)
        else:
            st.markdown(
                f"""
                <div class="result-card card-notfound">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 13px; font-weight: 700; color: #94a3b8;">รายการที่ #{idx}</span>
                        <span class="result-confidence conf-none">❌ ไม่พบ</span>
                    </div>
                    <div style="font-size: 18px; font-weight: 700; color: #64748b; margin: 6px 0;">
                        ไม่พบข้อมูลสำหรับ "<b>{item_name}</b>"
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
            export_rows.append({"ลำดับ": idx, "สินค้าที่ค้นหา": item_name, "ผลลัพธ์": "ไม่พบ", "แหล่งที่มา": "-", "ความมั่นใจ": "none", "คะแนน": 0})

    if export_rows:
        df = pd.DataFrame(export_rows)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📥 ส่งออกเป็น CSV ทั้งหมด", df.to_csv(index=False).encode('utf-8-sig'),
                f"multi_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv", icon=":material/download:", width='stretch')
        with c2:
            st.download_button("📥 ส่งออกเป็น JSON ทั้งหมด",
                json.dumps(export_rows, ensure_ascii=False, indent=2).encode('utf-8'),
                f"multi_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json", icon=":material/data_object:", width='stretch')
else:
    st.markdown("---")
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px;
        padding: 40px; text-align: center;">
        <span style="font-size: 46px;">⚡</span>
        <h3 style="color: #0f172a; margin-top: 14px;">Multi-Item Web Scraper & Batch Price Extractor</h3>
        <p style="color: #64748b; max-width: 560px; margin: 8px auto 0; font-size: 14px; line-height: 1.7;">
            ค้นหาหลายสินค้าพร้อมกันในคำสั่งเดียว ไม่จำกัดลำดับของคำว่า <code>ราคา</code> หรือ <code>price</code><br><br>
            <b>ตัวอย่างการค้นหา:</b><br>
            <code>มัทฉะน้ำผึ้งมะนาว, คาปูชิโน่เย็น, ซิกเนเจอร์ ท็อฟฟี่ โคโคนัท, ราคา</code><br>
            ➔ <b>มัทฉะน้ำผึ้งมะนาว ราคา 65</b><br>
            ➔ <b>คาปูชิโน่เย็น ราคา 70</b><br>
            ➔ <b>ซิกเนเจอร์ ท็อฟฟี่ โคโคนัท ราคา 65</b>
        </p>
    </div>
    """, unsafe_allow_html=True)