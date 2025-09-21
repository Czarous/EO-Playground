import json, os
from collections import Counter
from flask import Flask, render_template, request, jsonify, abort
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import threading
from concurrent.futures import ThreadPoolExecutor
from PIL import Image


app = Flask(__name__)

# Always resolve path relative to this file
DATA_FILE = os.path.join("..", "data", "oils_full.json") 


# Google Custom Search API
GOOGLE_CSE_ID = "d6b272582a998423d"
GOOGLE_API_KEY = "AIzaSyD_OFB0XPOorVyA_P3lgyT-HCgpUUXoWZM"
UNSPLASH_ACCESS_KEY = "RcdKHp8-6ccDbxAjlMzsT9mT0gsi8fQGEGdK1Hjn17Y"

CACHE_META_FILE = os.path.join(app.root_path, "data", "image_cache_meta.json")
IMAGE_FOLDER = os.path.join(app.root_path, "static", "oils")
os.makedirs(IMAGE_FOLDER, exist_ok=True)
FALLBACK_IMAGE = "/static/oils/placeholder.jpg"

LOW_CONF_THRESHOLD = 0.6
HIGH_CONF_THRESHOLD = 0.8

# Example keyword list to score image relevance
PLANT_KEYWORDS = {"leaf","flower","plant","tree","herb","bloom","foliage","bottle","essential","oil","seed","petal"}




try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        oils_data = json.load(f)
except FileNotFoundError:
    print(f"ERROR: Could not find {DATA_FILE}")
    oils_data = []  # fallback to empty list
    

NOTE_SCORE_MAP = {
    "top": 0.5,
    "top/middle": 0.8,
    "middle": 1.0,
    "middle/base": 1.3,
    "base": 1.5,
    "top/base": 1.4
}

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def flatten_field(oils, field):
    items = []
    for oil in oils:
        data = oil.get(field) or []
        if isinstance(data, str):
            items.extend([i.strip() for i in data.split(",") if i.strip()])
        elif isinstance(data, list):
            items.extend([i for i in data if i])
    return items

def make_blends_bidirectional(oils):
    oil_lookup = {oil["oil_name"]: oil for oil in oils}
    for oil in oils:
        blends = oil.get("blends_well_with") or []
        for b in blends:
            b = b.strip()
            if b in oil_lookup:
                b_oil = oil_lookup[b]
                b_blends = b_oil.get("blends_well_with") or []
                if oil["oil_name"] not in b_blends:
                    b_blends.append(oil["oil_name"])
                    b_oil["blends_well_with"] = b_blends
    return oils



def compute_scores(oils):
    oils = make_blends_bidirectional(oils)
    blends_all = flatten_field(oils, "blends_well_with")
    blend_counts = Counter(blends_all)
    most_blended_oil = blend_counts.most_common(1)[0][0] if blend_counts else None

    for oil in oils:
        therapeutic = oil.get("therapeutic_properties") or []
        emotional = oil.get("emotional_effects") or []
        components = oil.get("main_chemical_components") or []
        blends = oil.get("blends_well_with") or []
        notes = oil.get("note") or []
        aroma = oil.get("aroma_profile") or []

        # Normalize each contribution to 0–10 scale
        max_therapeutic = 20
        max_emotional = 10
        max_components = 8
        max_blends = 10
        max_notes = 5
        max_aroma = 5

        # Top Oil Score
        score = 0
        score += min(len(therapeutic), max_therapeutic) / max_therapeutic * 3     # weight 3
        score += min(len(emotional), max_emotional) / max_emotional * 2          # weight 2
        score += min(len(components), max_components) / max_components * 2        # weight 2
        score += min(len(blends), max_blends) / max_blends * 1                    # weight 1
        score += sum(NOTE_SCORE_MAP.get(n.lower(), 0.5) for n in notes) / max_notes  # weight ~1
        score += len(aroma) / max_aroma                                           # weight ~1
        if oil["oil_name"] == most_blended_oil:
            score += 1   # bonus for most blended

        # Beneficial Score
        # Focus on therapeutic + emotional only, include blend diversity lightly
        beneficial_score = 0
        for i, t in enumerate(therapeutic):
            beneficial_score += 2 * (0.95 ** i)   # diminishing returns
        for i, e in enumerate(emotional):
            beneficial_score += 1.5 * (0.95 ** i)
        # Optional: small contribution from blend diversity
        beneficial_score += min(len(blends), max_blends) / max_blends * 1

        # Assign scores back
        oil["score"] = round(score, 2)
        oil["beneficial_score"] = round(beneficial_score, 2)
        oil["blend_count"] = len(blends)

    # Global ranking
    oils_sorted_by_score = sorted(oils, key=lambda o: o["score"], reverse=True)
    for i, oil in enumerate(oils_sorted_by_score):
        oil["rank"] = i + 1

    oils_sorted_by_beneficial = sorted(oils, key=lambda o: o["beneficial_score"], reverse=True)
    for i, oil in enumerate(oils_sorted_by_beneficial):
        oil["beneficial_rank"] = i + 1

    return oils, blend_counts







@app.route("/")
def index():
    query = request.args.get("q", "").lower()
    filter_type = request.args.get("filter", "").lower()

    # Load dataset and make blends bidirectional
    all_oils = make_blends_bidirectional(load_data())
    all_oils, blend_counts = compute_scores(all_oils)

    # Initialize summary with safe defaults
    summary = {
        "total_oils": len(all_oils),
        "composition": {"count": 0, "top": []},
        "main_components": {"count": 0, "top": []},
        "therapeutic": {"count": 0, "top": []},
        "emotional": {"count": 0, "top": []},
        "blends": {"count": 0, "top": []},
        "component_freq": {},
        "blend_freq": {}
    }

    if all_oils:
        # Filter by search query
        oils = [o for o in all_oils if query in o["oil_name"].lower()] if query else all_oils.copy()

        # Flatten fields
        compositions = flatten_field(all_oils, "composition")
        main_components = flatten_field(all_oils, "main_chemical_components")
        therapeutic_props = flatten_field(all_oils, "therapeutic_properties")
        emotional_effects = flatten_field(all_oils, "emotional_effects")
        blends = flatten_field(all_oils, "blends_well_with")

        # --- FIXED: Precompute unique-oil counts per component ---
        # --- FIXED: Precompute unique-oil counts per component ---
        component_occurrence_freq = {}
        canonical_names = {}

        for oil in all_oils:
            seen = set()
            for c in (oil.get("main_chemical_components") or []):
                if not c:
                    continue
                norm = c.strip().lower()
                if norm in seen:
                    continue
                seen.add(norm)

                # Pick a canonical display name (first time we see it)
                if norm not in canonical_names:
                    canonical_names[norm] = c.strip()

                # Count using the normalized key
                component_occurrence_freq[norm] = component_occurrence_freq.get(norm, 0) + 1

        # Convert back to displayable keys
        component_occurrence_freq_display = {
            norm: count for norm, count in component_occurrence_freq.items()
        }

        most_common_component = max(
            component_occurrence_freq_display,
            key=lambda k: component_occurrence_freq_display[k]
        ) if component_occurrence_freq_display else None


        # Build summary
        summary = {
            "total_oils": len(all_oils),
            "composition": {
                "count": len(set(compositions)),
                "top": [i for i,_ in Counter(compositions).most_common(5)]
            },
            "main_components": {
                "count": len(component_occurrence_freq_display),
                "top": [comp for comp, _ in Counter(component_occurrence_freq_display).most_common(5)]
            },
            "therapeutic": {
                "count": len(set(therapeutic_props)),
                "top": [i for i,_ in Counter(therapeutic_props).most_common(5)]
            },
            "emotional": {
                "count": len(set(emotional_effects)),
                "top": [i for i,_ in Counter(emotional_effects).most_common(5)]
            },
            "blends": {
                "count": len(set(blends)),
                "top": sorted(all_oils, key=lambda o: o["blend_count"], reverse=True)[:5]
            },
            "component_freq": component_occurrence_freq_display,
            "blend_freq": dict(blend_counts)
        }

        # --- NEW: attach global component frequencies to each oil ---
        for o in oils:
            o["component_freq"] = component_occurrence_freq_display

        # Apply display sorting/filter
        if filter_type == "components" and most_common_component:
            top_comp_name = most_common_component.lower()
            oils.sort(
                key=lambda o: (
                    top_comp_name in [c.lower() for c in (o.get("main_chemical_components") or [])],
                    o["score"]
                ),
                reverse=True
            )
        elif filter_type == "therapeutic" and therapeutic_props:
            top_prop_name = Counter(flatten_field(oils, "therapeutic_properties")).most_common(1)[0][0].lower()
            oils.sort(
                key=lambda o: (
                    top_prop_name in [t.lower() for t in (o.get("therapeutic_properties") or [])],
                    o["score"]
                ),
                reverse=True
            )
        elif filter_type == "blends":
            oils.sort(key=lambda o: (o["blend_count"], o["score"], o["oil_name"]), reverse=True)
        elif filter_type == "beneficial":
            oils.sort(key=lambda o: (o["beneficial_score"], o["oil_name"]), reverse=True)
        else:
            oils.sort(key=lambda o: o["score"], reverse=True)
    else:
        oils = []

    # Top cards
    top_oil_card = oils[0] if oils else None
    top_beneficial_card = max(oils, key=lambda o: o["beneficial_score"]) if oils else None
    top_blend_card = max(oils, key=lambda o: o["blend_count"]) if oils else None
    common_component_card = (
        (most_common_component, component_occurrence_freq.get(most_common_component, 0))
        if all_oils else (None, 0)
    )

    return render_template(
        "index.html",
        oils=oils,
        summary=summary,
        query=query,
        filter=filter_type,
        top_oil_card=top_oil_card,
        top_beneficial_card=top_beneficial_card,
        top_blend_card=top_blend_card,
        common_component_card=common_component_card,
        top_oils=sorted(all_oils, key=lambda o: o["score"], reverse=True)[:5],
        top_beneficial=sorted(all_oils, key=lambda o: o["beneficial_score"], reverse=True)[:5],
        active_page="index" 
    )




@app.route("/filter/<filter_type>")
def filter_oils_json(filter_type):
    oils = load_data()
    oils = make_blends_bidirectional(oils)

    query = request.args.get("q", "").lower()
    if query:
        oils = [o for o in oils if query in o["oil_name"].lower()]

    # Flatten fields
    main_components = flatten_field(oils, "main_chemical_components")
    therapeutic_props = flatten_field(oils, "therapeutic_properties")
    emotional_effects = flatten_field(oils, "emotional_effects")
    blends = flatten_field(oils, "blends_well_with")

    # Compute scores
    oils, blend_counts = compute_scores(oils)

    # Precompute top components (top 5)
    top_components = [c for c, _ in Counter(main_components).most_common(5)]

    # Apply filter
    if filter_type == "components" and top_components:
        def component_priority(oil):
            oil_comps = [c.lower() for c in (oil.get("main_chemical_components") or [])]
            # position of each top component, missing ones get 999
            return tuple(oil_comps.index(c.lower()) if c.lower() in oil_comps else 999 for c in top_components)
        oils.sort(key=lambda o: (component_priority(o), -o["score"]))

    elif filter_type == "therapeutic" and therapeutic_props:
        top_prop = Counter(therapeutic_props).most_common(1)[0][0].lower()
        oils.sort(
            key=lambda o: (top_prop in [t.lower() for t in (o.get("therapeutic_properties") or [])], o["score"]),
            reverse=True
        )
    elif filter_type == "blends":
        oils.sort(key=lambda o: (o.get("blend_count", 0), o["score"], o["oil_name"]), reverse=True)
    elif filter_type == "beneficial":
        oils.sort(key=lambda o: (o.get("beneficial_score", 0), o["oil_name"]), reverse=True)
    else:
        oils.sort(key=lambda o: o["score"], reverse=True)

    # Prepare summary data for JS tooltips
    summary_data = {
        "top_oils": sorted(oils, key=lambda o: o["score"], reverse=True)[:5],
        "top_beneficial": sorted(oils, key=lambda o: o["beneficial_score"], reverse=True)[:5],
        "main_components": {
            "top": top_components,
            "count": len(set(main_components)),
            "component_freq": {c: sum(1 for o in oils if c.lower() in [x.lower() for x in (o.get("main_chemical_components") or [])])
                               for c in top_components}
        },
        "blends": {
            "top": sorted(oils, key=lambda o: o.get("blend_count",0), reverse=True)[:5],
            "count": len(set(blends))
        },
        "therapeutic": {
            "count": len(set(therapeutic_props))
        },
        "emotional": {
            "count": len(set(emotional_effects))
        }
    }

    # Simplify oils for JSON
    simplified_oils = [
        {
            "oil_name": o["oil_name"],
            "botanical_name": o.get("botanical_name",""),
            "main_chemical_components": o.get("main_chemical_components", []),
            "composition": o.get("composition",""),
            "therapeutic_properties": o.get("therapeutic_properties", []),
            "emotional_effects": o.get("emotional_effects", []),
            "blends_well_with": o.get("blends_well_with", []),
            "aroma_profile": o.get("aroma_profile",""),
            "note": o.get("note",""),
            "score": o.get("score", 0),
            "beneficial_score": o.get("beneficial_score", 0),
            "blend_count": o.get("blend_count", 0)
        }
        for o in oils
    ]

    return jsonify({
        "oils": simplified_oils,
        "summary": summary_data
    })





# --- Utilities ---
def safe_name_for_file(name):
    return "".join(c if c.isalnum() else "_" for c in name)[:120]

def load_cache_meta():
    if os.path.exists(CACHE_META_FILE):
        try:
            with open(CACHE_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_cache_meta(meta):
    os.makedirs(os.path.dirname(CACHE_META_FILE), exist_ok=True)
    with open(CACHE_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def download_image(url, local_path):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(r.content)
        return True
    except:
        return False

# --- Image sources ---
def fetch_google_image(query):
    try:
        url = f"https://www.googleapis.com/customsearch/v1?q={quote(query)}&cx={GOOGLE_CSE_ID}&searchType=image&num=1&key={GOOGLE_API_KEY}"
        res = requests.get(url, timeout=6)
        res.raise_for_status()
        data = res.json()
        if data.get("items"):
            return data["items"][0]["link"]
    except: pass
    return None

def fetch_unsplash_image(query):
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {"query": query, "per_page": 1, "client_id": UNSPLASH_ACCESS_KEY}
        res = requests.get(url, params=params, timeout=6)
        res.raise_for_status()
        data = res.json()
        if data.get("results"):
            return data["results"][0]["urls"]["regular"]
    except: pass
    return None

def fetch_bing_image(query):
    try:
        url = f"https://www.bing.com/images/search?q={quote(query)}&qft=+filterui:imagesize-large&form=IRFLTR"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        img_tag = soup.find("a", class_="iusc")
        if img_tag and img_tag.get("m"):
            meta = json.loads(img_tag["m"])
            return meta.get("murl")
    except: pass
    return None

# --- Core ---
def fetch_and_cache_image(oil):
    name = oil.get("oil_name")
    botanical = oil.get("botanical_name")
    safe_name = safe_name_for_file(botanical or name)
    local_path = os.path.join(IMAGE_FOLDER, f"{safe_name}.jpg")
    local_url = f"/static/oils/{safe_name}.jpg"

    cache = load_cache_meta()
    if safe_name in cache and os.path.exists(local_path):
        return cache[safe_name].get("local_url", local_url)

    # Build query
    queries = []
    if botanical: queries.append(f"{botanical} essential oil")
    if name: queries.append(f"{name} essential oil")
    
    img_url = None
    for q in queries:
        for fetcher in [fetch_google_image, fetch_unsplash_image, fetch_bing_image]:
            img_url = fetcher(q)
            if img_url and download_image(img_url, local_path):
                break
        if img_url: break

    final_url = local_url if img_url else FALLBACK_IMAGE

    # Save cache
    cache[safe_name] = {"local_url": final_url, "source_url": img_url}
    save_cache_meta(cache)
    return final_url

# --- Route ---
@app.route("/get-oil-image")
def get_image_route():
    oil_name = request.args.get("oil_name")
    botanical_name = request.args.get("botanical_name")
    if not oil_name and not botanical_name:
        return jsonify({"error": "Missing oil or botanical name"}), 400

    oil_obj = {"oil_name": oil_name, "botanical_name": botanical_name}
    safe_name = safe_name_for_file(botanical_name or oil_name)
    local_path = os.path.join(IMAGE_FOLDER, f"{safe_name}.jpg")
    cache = load_cache_meta()

    # Return cached immediately, fetch in background if missing
    if safe_name in cache and os.path.exists(local_path):
        local_url = cache[safe_name].get("local_url", FALLBACK_IMAGE)
        threading.Thread(target=fetch_and_cache_image, args=(oil_obj,), daemon=True).start()
        return jsonify({"image_url": local_url})

    # Fetch now if not cached
    local_url = fetch_and_cache_image(oil_obj)
    return jsonify({"image_url": local_url})



        




    

@app.route("/oil/<int:oil_id>")
def oil_detail(oil_id):
    # Work on a copy so we don’t mutate global data permanently
    oils = json.loads(json.dumps(oils_data))

    # Ensure bidirectional blends
    oils = make_blends_bidirectional(oils)

    # Find the oil
    oil = next((o for o in oils if o["oil_id"] == oil_id), None)
    if not oil:
        abort(404)

    return render_template(
        "oil-detail.html",
        oil=oil,
        oils=oils
    )


@app.route("/compounds")
def compounds():
    return render_template("compounds.html", active_page="compounds")

@app.route("/blends")
def blends():
    return render_template("blends.html", active_page="blends")

@app.route("/properties")
def properties():
    return render_template("properties.html", active_page="properties")



if __name__=="__main__":
    app.run(debug=True)
