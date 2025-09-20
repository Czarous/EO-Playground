import json

# ---------------- Your 15 oils with only 10 fields ----------------
oils_15 = [
    {
        "oil_name": "Lavender",
        "botanical_name": "Lavandula angustifolia",
        "composition": ["Linalool", "Linalyl acetate"],
        "main_chemical_components": ["Linalool", "Linalyl acetate"],
        "therapeutic_properties": ["Calming", "Antiseptic", "Anti-inflammatory"],
        "emotional_effects": ["Relaxing", "Mood-lifting"],
        "aroma_profile": "Floral, Sweet, Herbaceous",
        "note": "Top/Middle",
        "blends_well_with": ["Rose", "Peppermint", "Bergamot"],
        "color": ""
    },
      {
    "oil_id": 2,
    "oil_name": "Lemon",
    "botanical_name": "Citrus limon",
    "composition": ["Limonene", "Beta-pinene"],
    "main_chemical_components": ["Limonene", "Beta-pinene"],
    "therapeutic_properties": ["Antibacterial", "Digestive Aid"],
    "emotional_effects": ["Energizing", "Refreshing"],
    "aroma_profile": "Fresh, Citrusy, Bright",
    "note": "Top",
    "blends_well_with": ["Lavender", "Peppermint", "Rosemary"]
  },
  {
    "oil_id": 3,
    "oil_name": "Peppermint",
    "botanical_name": "Mentha piperita",
    "composition": ["Menthol", "Menthone"],
    "main_chemical_components": ["Menthol", "Menthone"],
    "therapeutic_properties": ["Analgesic", "Cooling", "Antispasmodic"],
    "emotional_effects": ["Refreshing", "Invigorating"],
    "aroma_profile": "Minty, Fresh, Cool",
    "note": "Top/Middle",
    "blends_well_with": ["Lavender", "Lemon", "Eucalyptus"]
  },
  {
    "oil_id": 4,
    "oil_name": "Eucalyptus",
    "botanical_name": "Eucalyptus globulus",
    "composition": ["Eucalyptol", "Alpha-pinene"],
    "main_chemical_components": ["Eucalyptol", "Alpha-pinene"],
    "therapeutic_properties": ["Antiseptic", "Anti-inflammatory", "Expectorant"],
    "emotional_effects": ["Refreshing", "Clearing"],
    "aroma_profile": "Fresh, Camphoraceous, Medicinal",
    "note": "Top/Middle",
    "blends_well_with": ["Peppermint", "Lavender", "Tea Tree"]
  },
  {
    "oil_id": 5,
    "oil_name": "Frankincense",
    "botanical_name": "Boswellia carterii",
    "composition": ["Alpha-pinene", "Limonene"],
    "main_chemical_components": ["Alpha-pinene", "Limonene"],
    "therapeutic_properties": ["Anti-inflammatory", "Astringent", "Immunostimulant"],
    "emotional_effects": ["Grounding", "Calming"],
    "aroma_profile": "Woody, Spicy, Resinous",
    "note": "Middle/Base",
    "blends_well_with": ["Lavender", "Sandalwood", "Citrus oils"]
  },
  {
    "oil_id": 6,
    "oil_name": "Rosemary",
    "botanical_name": "Rosmarinus officinalis",
    "composition": ["1,8-Cineole", "Camphor"],
    "main_chemical_components": ["1,8-Cineole", "Camphor"],
    "therapeutic_properties": ["Stimulant", "Antimicrobial"],
    "emotional_effects": ["Invigorating", "Focus"],
    "aroma_profile": "Herbaceous, Woody, Fresh",
    "note": "Middle",
    "blends_well_with": ["Lavender", "Lemon", "Peppermint"]
  },
  {
    "oil_id": 7,
    "oil_name": "Tea Tree",
    "botanical_name": "Melaleuca alternifolia",
    "composition": ["Terpinen-4-ol", "Alpha-terpineol"],
    "main_chemical_components": ["Terpinen-4-ol", "Alpha-terpineol"],
    "therapeutic_properties": ["Antiseptic", "Anti-inflammatory", "Antifungal"],
    "emotional_effects": ["Refreshing", "Cleansing"],
    "aroma_profile": "Fresh, Medicinal, Camphoraceous",
    "note": "Top/Middle",
    "blends_well_with": ["Lavender", "Eucalyptus", "Lemon"]
  },
  {
    "oil_id": 8,
    "oil_name": "Geranium",
    "botanical_name": "Pelargonium graveolens",
    "composition": ["Citronellol", "Geraniol"],
    "main_chemical_components": ["Citronellol", "Geraniol"],
    "therapeutic_properties": ["Astringent", "Anti-inflammatory", "Antidepressant"],
    "emotional_effects": ["Uplifting", "Balancing"],
    "aroma_profile": "Floral, Sweet, Rose-like",
    "note": "Middle",
    "blends_well_with": ["Lavender", "Rose", "Citrus oils"]
  },
  {
    "oil_id": 9,
    "oil_name": "Chamomile",
    "botanical_name": "Matricaria recutita",
    "composition": ["Alpha-bisabolol", "Chamazulene"],
    "main_chemical_components": ["Alpha-bisabolol", "Chamazulene"],
    "therapeutic_properties": ["Anti-inflammatory", "Calming", "Antispasmodic"],
    "emotional_effects": ["Relaxing", "Soothing"],
    "aroma_profile": "Sweet, Herbaceous, Apple-like",
    "note": "Middle/Base",
    "blends_well_with": ["Lavender", "Rose", "Citrus oils"]
  },
  {
    "oil_id": 10,
    "oil_name": "Bergamot",
    "botanical_name": "Citrus bergamia",
    "composition": ["Limonene", "Linalyl acetate"],
    "main_chemical_components": ["Limonene", "Linalyl acetate"],
    "therapeutic_properties": ["Antidepressant", "Antiseptic"],
    "emotional_effects": ["Uplifting", "Refreshing"],
    "aroma_profile": "Citrusy, Sweet, Fresh",
    "note": "Top",
    "blends_well_with": ["Lavender", "Rosemary", "Geranium"]
  },
  {
    "oil_id": 11,
    "oil_name": "Palmarosa",
    "botanical_name": "Cymbopogon martinii",
    "composition": ["Geraniol", "Linalool"],
    "main_chemical_components": ["Geraniol", "Linalool"],
    "therapeutic_properties": ["Antibacterial", "Hydrating"],
    "emotional_effects": ["Uplifting", "Soothing"],
    "aroma_profile": "Floral, Sweet, Rosy",
    "note": "Middle",
    "blends_well_with": ["Ylang Ylang", "Geranium", "Bergamot"]
  },
  {
    "oil_id": 12,
    "oil_name": "Spikenard",
    "botanical_name": "Nardostachys jatamansi",
    "composition": ["Valeranone", "Jatamansone"],
    "main_chemical_components": ["Valeranone", "Jatamansone"],
    "therapeutic_properties": ["Sedative", "Anti-inflammatory"],
    "emotional_effects": ["Grounding", "Relaxing"],
    "aroma_profile": "Earthy, Woody, Rich",
    "note": "Base",
    "blends_well_with": ["Frankincense", "Patchouli", "Sandalwood"]
  },
  {
    "oil_id": 13,
    "oil_name": "Blue Tansy",
    "botanical_name": "Tanacetum annuum",
    "composition": ["Chamazulene", "Sabinene"],
    "main_chemical_components": ["Chamazulene", "Sabinene"],
    "therapeutic_properties": ["Anti-inflammatory", "Calming"],
    "emotional_effects": ["Relaxing", "Mood-lifting"],
    "aroma_profile": "Sweet, Herbal, Fruity",
    "note": "Middle",
    "blends_well_with": ["Lavender", "Geranium", "Chamomile"]
  },
  {
    "oil_id": 14,
    "oil_name": "Melissa (Lemon Balm)",
    "botanical_name": "Melissa officinalis",
    "composition": ["Citral", "Geraniol", "Nerol"],
    "main_chemical_components": ["Citral", "Geraniol", "Nerol"],
    "therapeutic_properties": ["Calming", "Antiviral"],
    "emotional_effects": ["Uplifting", "Soothing"],
    "aroma_profile": "Citrusy, Herbaceous, Sweet",
    "note": "Top",
    "blends_well_with": ["Lavender", "Bergamot", "Palmarosa"]
  },
  {
    "oil_id": 15,
    "oil_name": "Hinoki",
    "botanical_name": "Chamaecyparis obtusa",
    "composition": ["α-Pinene", "Sabinene", "Camphene"],
    "main_chemical_components": ["α-Pinene", "Sabinene", "Camphene"],
    "therapeutic_properties": ["Grounding", "Antimicrobial"],
    "emotional_effects": ["Calming", "Focused"],
    "aroma_profile": "Woody, Citrus-like, Fresh",
    "note": "Base",
    "blends_well_with": ["Frankincense", "Cedarwood", "Spikenard"]
  }
    # Add the other 14 oils here with the same 10 fields
]

# ---------------- Read scraped oils ----------------
with open("oils_detailed.json", "r", encoding="utf-8") as f:
    oils_detailed = json.load(f)

# ---------------- Merge and remove duplicates ----------------
merged = {o['oil_name'].lower(): o for o in oils_detailed}  # use oil_name as key

for oil in oils_15:
    key = oil['oil_name'].lower()
    if key in merged:
        # update missing fields from the 15 oils
        for field in oil:
            if field not in merged[key] or not merged[key][field]:
                merged[key][field] = oil[field]
    else:
        merged[key] = oil

# ---------------- Add sequential oil_id ----------------
oils_full = list(merged.values())
for idx, oil in enumerate(oils_full, start=1):
    oil['oil_id'] = idx

# ---------------- Save ----------------
with open("oils_full.json", "w", encoding="utf-8") as f:
    json.dump(oils_full, f, indent=2, ensure_ascii=False)

print(f"✅ Merged {len(oils_full)} oils into oils_full.json with sequential IDs")
