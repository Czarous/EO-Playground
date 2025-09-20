# main.py (robust, NLTK + cloudscraper + cleaned fields)
import json
import time
import cloudscraper
from bs4 import BeautifulSoup
import os
import re
import sys

OUTPUT_FILE = "oils_detailed.json"
INPUT_FILE = "all_oils_to_scrape.json"
SKIP_FIRST = 5  # skip non-oil entries
REQUEST_DELAY = 2.0  # seconds between requests

# ---------------- NLTK support ----------------
USE_NLTK = True
try:
    import nltk
    from nltk import sent_tokenize
except Exception:
    USE_NLTK = False

def ensure_nltk():
    global USE_NLTK
    if not USE_NLTK:
        try:
            import nltk
            USE_NLTK = True
        except Exception:
            return False
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")
    return True

# ---------------- Helpers ----------------
def clean_text(s):
    if not s: return ""
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    return s

def sentence_split(text):
    if not text: return []
    if USE_NLTK:
        return sent_tokenize(text)
    return re.split(r'(?<=[.!?])\s+', text)

def unique_preserve(seq):
    seen = set()
    out = []
    for s in seq:
        s_lower = s.lower()
        if s_lower not in seen:
            seen.add(s_lower)
            out.append(s)
    return out

def extract_list_from_ul(ul):
    if not ul: return []
    items = []
    for li in ul.find_all("li"):
        txt = clean_text(li.get_text(" ", strip=True))
        if txt:
            items.append(txt)
    return unique_preserve(items)

# ---------------- Constants ----------------
COMMON_COUNTRIES = ["United Kingdom","United States","Thailand","Kenya","Australia","Dominican Republic"] # can expand

SCENT_WORDS = [
    "woody","sweet","balsamic","citrus","lemony","orange","bergamot","floral","rose","neroli","jasmine",
    "ylang","powdery","earthy","musky","smoky","spicy","peppery","camphor","medicinal","herbal","green",
    "fresh","fruity","vanilla","resinous","amber","pine","cedar","sandalwood","almond","nutty","coconut"
]

SPECIFIERS = ["slightly","slight","strongly","mildly","very","sweetly","softly","powerfully","distinctly","subtly"]

AROMA_NORMALIZE = {s:s.capitalize() for s in SCENT_WORDS}

AROMA_KEYWORDS = ["aroma","fragrance","scent","olfactory","aromatic","nose","odor","odour","aromatic description"]
EMOTION_KEYWORDS = ["emotion","calm","grounding","uplift","energ","focus","meditation","sleep","sensual","aphrodisiac"]
THERAPEUTIC_KEYWORDS = ["benefit","uses","treat","help","application","anti","asthma","pain","inflammation","infection","skin","digest","respir"]

# ---------------- Extraction functions ----------------
def normalize_descriptor_phrase(phrase):
    if not phrase: return None
    p = phrase.lower()
    p = re.sub(r"[^\w\s]", " ", p)  # remove punctuation
    # Only keep valid aroma words
    found = [AROMA_NORMALIZE[s] for s in SCENT_WORDS if re.search(r"\b"+re.escape(s)+r"\b", p)]
    if found:
        return ", ".join(unique_preserve(found))
    return None



def extract_aroma_descriptors(all_text):
    text = clean_text(all_text)
    sents = sentence_split(text)
    aroma_sents = [s for s in sents if any(k in s.lower() for k in AROMA_KEYWORDS)]
    candidates = []
    for s in aroma_sents:
        if any(bad in s.lower() for bad in ["source","pregnant","tisserand","constituents","edition"]):
            continue
        parts = re.split(r",| with | and | including |;|:|\(|\)| - ", s, flags=re.I)
        for p in parts:
            norm = normalize_descriptor_phrase(p)
            if norm:
                candidates.append(norm)
    return ", ".join(unique_preserve(candidates))


def extract_emotional_effects(all_text):
    text = clean_text(all_text)
    sents = sentence_split(text)
    matches = []
    for s in sents:
        for kw in EMOTION_KEYWORDS:
            if kw in s.lower():
                matches.append(kw.capitalize())
    return unique_preserve(matches)

def extract_therapeutic_properties(article):
    ul = article.find("ul")
    if ul:
        return extract_list_from_ul(ul)
    p_texts = " ".join([p.get_text(" ",strip=True) for p in article.find_all("p")])
    sents = sentence_split(p_texts)
    items = []
    for s in sents:
        if any(k in s.lower() for k in THERAPEUTIC_KEYWORDS):
            parts = re.split(r":|;|,|\band\b|\bor\b", s, flags=re.I)
            for p in parts:
                p = clean_text(p)
                if 2 < len(p) < 120:
                    items.append(p.capitalize())
    return unique_preserve(items)

def extract_origin(article):
    text = " ".join([p.get_text(" ",strip=True) for p in article.find_all("p")])
    found = [c for c in COMMON_COUNTRIES if re.search(r"\b"+re.escape(c)+r"\b", text)]
    return ", ".join(unique_preserve(found))

# ---------------- Helper for blends ----------------   
def build_oil_name_set(input_file):
    """
    Build a set of known oil names (lowercased) from all_oils_to_scrape.json.
    """
    import json
    with open(input_file, "r", encoding="utf-8") as f:
        oils_list = json.load(f)
    return set([o.get('oil_name','').lower() for o in oils_list if o.get('oil_name')])

def extract_blends_from_text(all_text, oil_name_set):
    """
    Extract blends-well-with oils from text, keeping only names in the reference set.
    """
    matches = []
    patterns = [
        r"reminiscent (?:to|of) ([^.;\n]+)", 
        r"(?:similar to|like|complements|works well with) ([^.;\n]+)"
    ]
    for pat in patterns:
        for grp in re.findall(pat, all_text, re.I):
            parts = re.split(r",| and | & |\/", grp)
            for p in parts:
                p_clean = clean_text(p).lower()
                # include only if it matches a known oil
                for oil in oil_name_set:
                    if oil in p_clean:
                        matches.append(oil.title())
    return unique_preserve(matches)


# ---------------- Core scraping ----------------
# ---------------- Scraping function ----------------
def scrape_oil_page(oil, scraper, oil_id, oil_name_set):
    oil_name = oil.get("oil_name","Unknown")
    url = oil.get("url") or (oil.get("references") and oil.get("references")[0])
    if not url:
        print(f"⚠️ Skipping {oil_name} – no URL")
        return None
    print(f"🔎 Scraping {oil_name} -> {url}")
    try:
        r = scraper.get(url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        article = soup.find("article") or soup.find("div", class_="content")
        if not article:
            print(f"⚠️ Article not found for {oil_name}")
            return None
        paragraphs = [p.get_text(" ",strip=True) for p in article.find_all("p")]
        all_text = " ".join(paragraphs)

        # Extract fields
        aroma_raw = extract_aroma_descriptors(all_text).split(",")
        # Remove duplicates and unwanted descriptors
        aroma_clean = unique_preserve([a.strip() for a in aroma_raw if a.lower() not in ["medicinal", "methyl salicylate-like"]])

        data = {
            "oil_id": oil_id,
            "oil_name": oil_name,
            "botanical_name": "",
            "composition": [],
            "main_chemical_components": [],
            "therapeutic_properties": extract_therapeutic_properties(article),
            "emotional_effects": extract_emotional_effects(all_text),
            "aroma_profile": ", ".join(aroma_clean),
            "note": "",
            "blends_well_with": [],  # leave empty for now
            "color": "",
            "origin": extract_origin(article),
            "url": url
        }

        # Botanical name
        h2_bot = article.find("h2", style=re.compile("italic", re.I))
        if h2_bot:
            data["botanical_name"] = clean_text(h2_bot.get_text())
        else:
            h2_bot_p = article.find("h2", string=re.compile("Botanical Name", re.I))
            if h2_bot_p:
                p = h2_bot_p.find_next("p")
                if p: data["botanical_name"] = clean_text(p.get_text())

        # Major constituents
        h2_major = article.find("h2", string=re.compile("Major Constituents", re.I))
        if h2_major:
            ul = h2_major.find_next("ul")
            data["main_chemical_components"] = extract_list_from_ul(ul)

        # Color
        h2_color = article.find("h2", string=re.compile("Color", re.I))
        if h2_color:
            p = h2_color.find_next("p")
            if p: data["color"] = clean_text(p.get_text())

        # Note
        h2_note = article.find("h2", string=re.compile("Perfumery Note|Perfumery", re.I))
        if h2_note:
            p = h2_note.find_next("p")
            if p: data["note"] = clean_text(p.get_text())

        # Blends well with (filtered using reference set)
        data["blends_well_with"] = extract_blends_from_text(all_text, oil_name_set)

        return data
    except Exception as e:
        print(f"❌ Failed {oil_name}: {e}")
        return None

# ---------------- Runner ----------------
def save_progress(results):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

# ---------------- Main runner ----------------
def main():
    if USE_NLTK:
        try: ensure_nltk()
        except: print("⚠️ NLTK setup failed, continuing without it.")

    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} not found.")
        sys.exit(1)

    # Load oils and build reference set
    with open(INPUT_FILE,"r",encoding="utf-8") as f:
        oils = json.load(f)
    oils_to_scrape = oils[SKIP_FIRST:]

    # Build reference set for blends (lowercase oil names)
    OIL_NAME_SET = set([o.get('oil_name','').lower() for o in oils if o.get('oil_name')])

    results = []
    scraper = cloudscraper.create_scraper(browser={'browser':'chrome','platform':'windows','mobile':False})
    oil_id = 1

    for oil in oils_to_scrape:
        print(f"⏳ Processing {oil.get('oil_name','Unknown')}")
        data = scrape_oil_page(oil, scraper, oil_id, oil_name_set=OIL_NAME_SET)
        if data:
            results.append(data)
            oil_id += 1
        else:
            print(f"⚠️ Skipped {oil.get('oil_name','Unknown')} (scrape failed)")

        # Save progress after each attempt
        save_progress(results)
        print(f"💾 Progress saved ({len(results)} oils scraped so far)")

        time.sleep(REQUEST_DELAY)

    print(f"✅ Finished scraping {len(results)} oils.")



if __name__=="__main__":
    main()
