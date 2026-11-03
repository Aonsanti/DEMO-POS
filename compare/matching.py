"""Query/product name matching and size parsing (works for Thai: no word spaces)."""
import re

_STRIP = re.compile(r"[\s\-_.,/\\()\[\]{}\"'+*|:;!?]+")


def norm(text: str) -> str:
    return _STRIP.sub("", (text or "").lower())


def _bigrams(s: str) -> set:
    return {s[i:i + 2] for i in range(len(s) - 1)} or {s}


def relevance(query: str, name: str) -> float:
    """0..1 — how well a product name fits the query."""
    nq, nn = norm(query), norm(name)
    if not nq or not nn:
        return 0.0
    if nq in nn:
        return 1.0
    tokens = [norm(t) for t in re.split(r"[\s,/+]+", query) if norm(t)]
    contain = sum(t in nn for t in tokens) / len(tokens) if tokens else 0.0
    bq, bn = _bigrams(nq), _bigrams(nn)
    dice = 2 * len(bq & bn) / (len(bq) + len(bn))
    # dice is length-biased against long names, so use "how much of the query is covered" too
    cover = len(bq & bn) / len(bq)
    return max(contain * 0.95, dice, cover * 0.9)


def query_variants(query: str) -> list:
    """Fallback queries when the full query finds nothing: each word, longest first."""
    words = sorted({w for w in re.split(r"[\s,/+]+", query) if len(w) >= 2 and w != query.strip()},
                   key=len, reverse=True)
    return words[:3]


# ── size parsing ─────────────────────────────────────────────
_UNITS = {
    "มล": ("ml", 1), "ml": ("ml", 1), "ลิตร": ("ml", 1000), "ล": ("ml", 1000), "l": ("ml", 1000),
    "กรัม": ("g", 1), "ก": ("g", 1), "g": ("g", 1), "กก": ("g", 1000), "กิโลกรัม": ("g", 1000), "kg": ("g", 1000),
}
_UNIT_RE = r"(มล|ml|ลิตร|กรัม|กิโลกรัม|kg|กก|ล|ก|g|l)(?![a-zA-Zก-ฮ])"
_SIZE = re.compile(r"(\d+(?:[.,]\d+)?)\s*" + _UNIT_RE + r"\.?", re.I)
_MULT_BEFORE = re.compile(r"(\d+)\s*[x×]\s*\d+(?:[.,]\d+)?\s*" + _UNIT_RE, re.I)
_MULT_AFTER = re.compile(r"(?:[x×]|แพ็ค|แพค|pack|ยกลัง)\s*(\d+)", re.I)


def parse_size(name: str):
    """-> (unit 'ml'|'g', total amount) or None. Multipacks (x6, แพ็ค 6, ยกลัง 48) are multiplied in."""
    m = _SIZE.search(name or "")
    if not m:
        return None
    unit, factor = _UNITS[m.group(2).lower()]
    amount = float(m.group(1).replace(",", ".")) * factor
    mult = 1
    mb = _MULT_BEFORE.search(name)
    ma = _MULT_AFTER.search(name)
    if mb:
        mult = int(mb.group(1))
    elif ma:
        mult = int(ma.group(1))
    total = amount * max(mult, 1)
    return (unit, total) if total > 0 else None


def size_info(name: str, price):
    """Dict with size label and price per 100 ml/g (None when it can't be worked out)."""
    parsed = parse_size(name)
    if not parsed or not price:
        return {"unit": None, "total": None, "per100": None}
    unit, total = parsed
    return {"unit": unit, "total": total, "per100": round(price / total * 100, 2)}
