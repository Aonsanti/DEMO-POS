"""One adapter per store. Each returns a list of product dicts:
{store, name, price, regular_price, url, image, in_stock}

Only public pages / the store's own public search API are used, with plain requests.
If a store refuses (403/429) we report it instead of trying to get around it.
"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from .matching import query_variants, relevance, size_info

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "th,en;q=0.8",
}
TIMEOUT = 20
NUM = re.compile(r"[\d,]+(?:\.\d+)?")


class StoreError(Exception):
    pass


def _num(text):
    m = NUM.search(text or "")
    return float(m.group().replace(",", "")) if m else None


def _check(r):
    if r.status_code in (403, 429):
        raise StoreError(f"เว็บไซต์ปฏิเสธการเข้าถึงอัตโนมัติ (HTTP {r.status_code}) — เปิดค้นหาเองในเว็บแทน")
    if r.status_code >= 400:
        raise StoreError(f"เว็บไซต์ตอบกลับผิดปกติ (HTTP {r.status_code})")
    return r


def _product(store, name, price, regular, url, image, in_stock=True, **extra):
    return {"store": store, "name": name.strip(), "price": price, "regular_price": regular,
            "url": url, "image": image, "in_stock": in_stock, **extra}


# ── Lotus's : public JSON search API used by lotuss.com itself ──
def lotus(query, limit):
    r = _check(requests.post(
        f"https://api-o2o.lotuss.com/lotuss-mobile-bff/product/v6/search?sort=relevance:DESC&limit={limit}&page=1&seller_id=3",
        json={"keyword": query},
        headers={**HEADERS, "Referer": "https://www.lotuss.com/", "Accept-Language": "th"}, timeout=TIMEOUT))
    out = []
    for p in (r.json().get("data") or {}).get("products", [])[:limit]:
        out.append(_product(
            "Lotus's", p.get("name", ""), p.get("finalPricePerUOW"), p.get("regularPricePerUOW"),
            f"https://www.lotuss.com/th/product/{p.get('urlKey', '')}",
            (p.get("thumbnail") or {}).get("url"), p.get("stockStatus") == "IN_STOCK",
            member_price=p.get("loyaltyMemberPricePerUOW")))
    return out


# ── All Online (7-Eleven online shop) : server-rendered search page ──
def allonline(query, limit):
    r = _check(requests.get("https://www.allonline.7eleven.co.th/search?q=" + quote(query),
                            headers=HEADERS, timeout=TIMEOUT))
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for it in soup.select(".product-item")[:limit]:
        a = it.select_one("a.productlink")
        name_el = it.select_one("div.item.description")
        if not a or not name_el:
            continue
        nums = [float(n.replace(",", "")) for n in NUM.findall((it.select_one(".price-bottom") or it).get_text(" "))]
        if not nums:
            continue
        img = it.select_one("img.owl-lazy, img")
        out.append(_product("All Online", name_el.get_text(" ", strip=True), nums[0],
                            nums[1] if len(nums) > 1 else None,
                            urljoin("https://www.allonline.7eleven.co.th", a.get("href", "")),
                            img.get("src") if img else None))
    return out


# ── Big C : server-rendered search page ──
def bigc(query, limit):
    r = requests.get("https://www.bigc.co.th/search?q=" + quote(query), headers=HEADERS, timeout=TIMEOUT)
    if r.status_code == 404:  # Big C answers 404 when a search has no result
        return []
    soup = BeautifulSoup(_check(r).text, "html.parser")
    out = []
    for li in soup.find_all("li"):
        a = li.find("a", href=re.compile(r"/product/"))
        img = li.find("img", alt=True)
        if not a or not img:
            continue
        prices = [float(n.replace(",", "")) for n in re.findall(r"฿\s*([\d,]+(?:\.\d+)?)", li.get_text(" "))]
        if not prices:
            continue
        out.append(_product("Big C", img["alt"], prices[0], max(prices) if len(prices) > 1 else None,
                            urljoin("https://www.bigc.co.th", a["href"]), img.get("src")))
        if len(out) >= limit:
            break
    return out


# ── 7-Eleven (7eleven.co.th) : no search; index product + promotion pages once, then match locally ──
_SEVEN = "https://www.7eleven.co.th"
_SEVEN_PAGES = ["/new-product", "/new-product/drink", "/new-product/bakery",
                "/promotion", "/promotion/sale", "/promotion/trade", "/promotion/matching",
                "/promotion/allmember", "/promotion/redeem", "/promotion/stamp", "/promotion/only",
                "/promotion/newProduct", "/promotion/savemore", "/promotion/bigpack"]
_seven_cache = {"at": 0.0, "items": []}


def _next_data(path):
    r = _check(requests.get(_SEVEN + path, headers=HEADERS, timeout=TIMEOUT))
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    return json.loads(m.group(1)).get("props", {}).get("pageProps", {}) if m else {}


def _walk_items(node, found):
    """Collect every product / promotion campaign dict hiding anywhere in the page data."""
    if isinstance(node, dict):
        kind = node.get("item_type")
        url = node.get("item_url") or ""
        if node.get("title_th") and node.get("id") and (
                kind == "product" or kind == "promotion" or (kind == "banner" and url.startswith("/promotion/"))):
            found[(url, node["id"])] = node
        for v in node.values():
            _walk_items(v, found)
    elif isinstance(node, list):
        for v in node:
            _walk_items(v, found)


def _first_price(text):
    m = re.search(r"ราคา\s*:?\s*([\d,]+(?:\.\d+)?)\s*บาท", text) or re.search(r"([\d,]+(?:\.\d+)?)\s*บาท", text)
    return float(m.group(1).replace(",", "")) if m else None


def _period(it):
    end = (it.get("end_date") or "")[:10]
    return f"ถึง {end[8:10]}/{end[5:7]}/{end[:4]}" if len(end) == 10 else ""


def _seven_index():
    if time.time() - _seven_cache["at"] < 3600 and _seven_cache["items"]:
        return _seven_cache["items"]
    found = {}
    for path in _SEVEN_PAGES:
        try:
            _walk_items(_next_data(path), found)
        except StoreError:
            raise
        except Exception:   # one odd page must not hide the rest
            continue

    # promotion pages list the products that join the promotion -> tag those products
    promos = {k: v for k, v in found.items() if v.get("item_type") != "product"}

    def related(key):
        url, pid = key
        try:
            pp = _next_data(f"{url}{pid}")
        except Exception:
            return key, []
        return key, [i["id"] for i in (pp.get("related_product") or {}).get("items", []) if i.get("id")]

    notes = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        for key, ids in ex.map(related, list(promos)):
            for pid in ids:
                notes.setdefault(pid, []).append(promos[key]["title_th"])

    items = []
    for (url, pid), it in found.items():
        detail = BeautifulSoup(it.get("detail_th") or "", "html.parser").get_text(" ", strip=True)
        thumb = it.get("thumb_image") or it.get("detail_image") or []
        is_product = it.get("item_type") == "product"
        in_promos = notes.get(pid, []) if is_product else []
        items.append({
            "name": it["title_th"],
            "extra": " ".join(filter(None, [it.get("title_en"), it.get("keyword_tag"), it.get("desc_th"), detail[:200]]
                                     + in_promos)),
            "price": (_first_price(detail) or _num(str(it.get("price") or ""))) if is_product else None,
            "url": f"{_SEVEN}{url or '/new-product/'}{pid}",
            "image": (thumb[0].get("url") if thumb and isinstance(thumb[0], dict) else None),
            "note": ("🏷️ โปรโมชั่น " + _period(it)).strip() if not is_product else
                    ("อยู่ในโปร: " + ", ".join(dict.fromkeys(in_promos))) if in_promos else "",
            "kind": "สินค้า" if is_product else "โปรโมชั่น",
        })
    seen, unique = set(), []
    for i in items:   # several campaigns share one title (e.g. "ลดอย่างแรง 7 วันเท่านั้น") -> show it once
        key = (i["name"], i["kind"]) if i["kind"] == "โปรโมชั่น" else i["url"]
        if key not in seen:
            seen.add(key)
            unique.append(i)
    items = unique
    _seven_cache.update(at=time.time(), items=items)
    return items


def seven(query, limit):
    scored = sorted(((relevance(query, i["name"] + " " + i["extra"]), i) for i in _seven_index()),
                    key=lambda x: -x[0])
    return [_product("7-Eleven", i["name"], i["price"], None, i["url"], i["image"], note=i["note"], kind=i["kind"])
            for rel, i in scored[:limit] if rel >= 0.4]


STORES = {"7-Eleven": seven, "Lotus's": lotus, "Big C": bigc, "All Online": allonline}
HOME = {"7-Eleven": "https://www.7eleven.co.th/new-product", "Lotus's": "https://www.lotuss.com/th/search/{q}",
        "Big C": "https://www.bigc.co.th/search?q={q}", "All Online": "https://www.allonline.7eleven.co.th/search?q={q}"}


def search_store(store, query, limit=8):
    """-> {"products": [...], "error": str|None, "used": query-actually-matched}.
    Smarter than a single try: if the full query finds nothing, retry with its longest words,
    then rank everything against the ORIGINAL query so weak hits sink to the bottom."""
    fn = STORES[store]
    tried = [query] + query_variants(query)
    try:
        for q in tried:
            products = fn(q, max(limit * 2, 10))
            if products:
                break
        else:
            return {"products": [], "error": None, "used": query}
    except StoreError as e:
        return {"products": [], "error": str(e), "used": query}
    except Exception as e:  # network/parse problem in one store must not break the others
        return {"products": [], "error": f"ดึงข้อมูลไม่สำเร็จ ({type(e).__name__})", "used": query}

    for p in products:
        p["relevance"] = round(relevance(query, p["name"]), 2)
        p.update(size_info(p["name"], p["price"]))
    products.sort(key=lambda p: (-p["relevance"], p["price"] is None, p["price"] or 0))
    keep = [p for p in products if p["relevance"] >= 0.45]  # weak look-alikes are noise, not matches
    return {"products": keep[:limit], "error": None, "used": q}


def search_all(queries, stores, limit=8):
    """-> {query: {store: result}} — every (query, store) pair runs in parallel."""
    jobs = [(q, s) for q in queries for s in stores]
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda j: search_store(j[1], j[0], limit), jobs))
    out = {q: {} for q in queries}
    for (q, s), res in zip(jobs, results):
        out[q][s] = res
    return out
