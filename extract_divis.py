import csv
import re
from collections import defaultdict

# Valid categories from the scraped data and incomplete overview
VALID_CATEGORIES = {
    "Algemeen",
    "Anesthesie en pijnbestrijding",
    "Anesthesiologie en pijnbestrijding",
    "Borstkanker",
    "Cardiologie",
    "Chirurgie",
    "Dermatologie",
    "Fysiotherapie",
    "Geriatrie",
    "Gynaecologie en verloskunde",
    "Gynaecologie en Verloskunde",
    "Huisarts",
    "Infectieziektebestrijding",
    "Intensive Care",
    "Interne geneeskunde",
    "Interne Geneeskunde",
    "KNO",
    "Kindergeneeskunde",
    "Longgeneeskunde",
    "Longziekten",
    "Maag-darm-leverziekten",
    "Mond-, kaak- en aangezichtschirurgie",
    "Neonatologie",
    "Neurologie",
    "Nucleaire geneeskunde",
    "Oncologie",
    "Oogheelkunde",
    "Orthopedie",
    "Plastische Chirurgie",
    "Psychiatrie",
    "Psychologie & Psychiatrie",
    "Radiologie",
    "Radiologie en beeldvormende technieken",
    "Reumatologie",
    "Revalidatie",
    "Spoedeisende Hulp en Gipskamer",
    "Urologie",
    "Wetenschappelijk onderzoek",
    "Partner Divi",
    "PDF",
}

# Normalize category names to match the original incomplete overview format
CATEGORY_NORMALIZATION = {
    "Anesthesie en pijnbestrijding": "Anesthesiologie en pijnbestrijding",
    "Gynaecologie en verloskunde": "Gynaecologie en Verloskunde",
    "Interne geneeskunde": "Interne Geneeskunde",
    "Longgeneeskunde": "Longziekten",
    "Radiologie en beeldvormende technieken": "Radiologie",
    "Psychologie & Psychiatrie": "Psychiatrie",
}

def normalize_category(cat):
    """Normalize a category name to match the original format."""
    cat = cat.strip()
    return CATEGORY_NORMALIZATION.get(cat, cat)

def extract_divis():
    """Extract divi names and their categories from the scraped CSV."""
    divis = {}

    with open('Indiveo (1).csv', 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # Each record starts with a pattern like "1765314254-1"
    # Split by this pattern to get individual records
    records = re.split(r'"(\d{10}-\d+)"', content)

    # Process records (skip header and empty parts)
    for i in range(2, len(records), 2):  # Skip id, take content
        record_content = records[i] if i < len(records) else ""

        # Clean up the record
        record_content = record_content.strip()
        if not record_content:
            continue

        # Extract divi name - it's in the field after category_link
        # Pattern: ,"https://indiveo.nl/themas/...","Divi Name","https://indiveo.nl/divis/..."
        divi_match = re.search(
            r'https://indiveo\.nl/themas/[^"]+","([^"]+)","https://indiveo\.nl/divis/',
            record_content
        )

        if not divi_match:
            continue

        divi_name = divi_match.group(1).strip()

        # Extract categories - they're at the very end of the record
        # The record ends with something like: "Longziekten, Wetenschappelijk onderzoek"
        # But be careful with "Mond-, kaak- en aangezichtschirurgie" which has a comma inside

        # Find the last quoted value that looks like categories
        all_quotes = re.findall(r'"([^"]*)"', record_content)

        categories_str = None
        # Work backwards to find the categories
        for q in reversed(all_quotes):
            q = q.strip()
            # Skip content descriptions
            if q.startswith('Deze Divi') or q.startswith('Animatie') or q.startswith('B1 ') or q.startswith('Begrijpelijke'):
                continue
            # Skip URLs
            if q.startswith('http'):
                continue
            # Skip empty
            if not q:
                continue
            # Skip very long text (descriptions)
            if len(q) > 150:
                continue
            # Skip if it's the divi name itself
            if q == divi_name:
                continue
            # This should be categories
            categories_str = q
            break

        if divi_name and categories_str:
            if divi_name not in divis:
                divis[divi_name] = set()

            # Handle special case: "Mond-, kaak- en aangezichtschirurgie"
            # This category has a comma in the middle
            if "Mond-" in categories_str and "kaak- en aangezichtschirurgie" in categories_str:
                categories_str = categories_str.replace("Mond-, kaak- en aangezichtschirurgie", "MKAC_PLACEHOLDER")

            # Split categories by comma and add each
            for cat in categories_str.split(','):
                cat = cat.strip()
                if cat == "MKAC_PLACEHOLDER":
                    cat = "Mond-, kaak- en aangezichtschirurgie"

                # Normalize
                cat = normalize_category(cat)

                # Validate - skip if not a known category
                if cat and (cat in VALID_CATEGORIES or any(valid.lower() == cat.lower() for valid in VALID_CATEGORIES)):
                    divis[divi_name].add(cat)
                elif cat:
                    # Check if it might be a valid category we missed
                    # Only add if it looks like a category (not too long, not a divi name pattern)
                    if len(cat) < 50 and cat != divi_name:
                        divis[divi_name].add(cat)

    return divis

def main():
    divis = extract_divis()

    print(f"Total divis found: {len(divis)}")

    # Count categories
    all_cats = set()
    for cats in divis.values():
        all_cats.update(cats)

    print(f"\nTotal unique categories: {len(all_cats)}")
    print("\nCategories found:")
    for cat in sorted(all_cats):
        count = sum(1 for d_cats in divis.values() if cat in d_cats)
        print(f"  - {cat} ({count} divis)")

    print("\n\nSample entries (first 30):")
    for i, (name, cats) in enumerate(sorted(divis.items())[:30]):
        print(f"  {name}: {', '.join(sorted(cats))}")

    # Check for potential issues
    print("\n\nEntries with potentially incorrect categories:")
    for name, cats in sorted(divis.items()):
        for cat in cats:
            if len(cat) > 40 or cat == name:
                print(f"  WARNING: {name} has suspicious category: {cat}")

if __name__ == '__main__':
    main()
