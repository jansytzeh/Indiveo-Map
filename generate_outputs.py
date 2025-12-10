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

def extract_divis_from_scrape():
    """Extract divi names, their categories, and URLs from the scraped CSV."""
    divis = {}
    divi_urls = {}

    with open('Indiveo (1).csv', 'r', encoding='utf-8-sig') as f:
        content = f.read()

    records = re.split(r'"(\d{10}-\d+)"', content)

    for i in range(2, len(records), 2):
        record_content = records[i] if i < len(records) else ""
        record_content = record_content.strip()
        if not record_content:
            continue

        divi_match = re.search(
            r'https://indiveo\.nl/themas/[^"]+","([^"]+)","(https://indiveo\.nl/divis/[^"]+)"',
            record_content
        )

        if not divi_match:
            continue

        divi_name = divi_match.group(1).strip()
        divi_url = divi_match.group(2).strip()

        # Store the URL
        divi_urls[divi_name] = divi_url

        all_quotes = re.findall(r'"([^"]*)"', record_content)

        categories_str = None
        for q in reversed(all_quotes):
            q = q.strip()
            if q.startswith('Deze Divi') or q.startswith('Animatie') or q.startswith('B1 ') or q.startswith('Begrijpelijke'):
                continue
            if q.startswith('http'):
                continue
            if not q:
                continue
            if len(q) > 150:
                continue
            if q == divi_name:
                continue
            categories_str = q
            break

        if divi_name and categories_str:
            if divi_name not in divis:
                divis[divi_name] = set()

            if "Mond-" in categories_str and "kaak- en aangezichtschirurgie" in categories_str:
                categories_str = categories_str.replace("Mond-, kaak- en aangezichtschirurgie", "MKAC_PLACEHOLDER")

            for cat in categories_str.split(','):
                cat = cat.strip()
                if cat == "MKAC_PLACEHOLDER":
                    cat = "Mond-, kaak- en aangezichtschirurgie"

                cat = normalize_category(cat)

                if cat and (cat in VALID_CATEGORIES or any(valid.lower() == cat.lower() for valid in VALID_CATEGORIES)):
                    divis[divi_name].add(cat)
                elif cat and len(cat) < 50 and cat != divi_name:
                    divis[divi_name].add(cat)

    return divis, divi_urls

def read_incomplete_overview():
    """Read the incomplete overview to identify Partner Divi's and existing entries."""
    partner_divis = set()
    pdf_divis = set()
    existing_entries = {}

    with open("Overzicht Divi's in Divitheek.xlsx - Worksheet.csv", 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0] or row[0] == 'Divi':
                continue

            divi_name = row[0].strip()
            categories = []

            for cell in row[1:]:
                cell = cell.strip()
                if cell and cell != '-':
                    if 'Partner Divi' in cell:
                        partner_divis.add(divi_name)
                    if 'PDF' in cell and 'Partner' not in cell:
                        pdf_divis.add(divi_name)
                    elif 'PDF, Partner Divi' in cell:
                        pdf_divis.add(divi_name)
                        partner_divis.add(divi_name)
                    # Check if it's a regular category
                    if cell not in ['Partner Divi', 'PDF', 'PDF, Partner Divi']:
                        categories.append(cell)

            existing_entries[divi_name] = categories

    return partner_divis, pdf_divis, existing_entries

def generate_completed_overview(scraped_divis, partner_divis, pdf_divis, existing_entries):
    """Generate the completed overview CSV with the same structure."""
    all_divis = set(scraped_divis.keys()) | set(existing_entries.keys())

    rows = []
    for divi_name in sorted(all_divis):
        # Get categories from scraped data
        scraped_cats = list(scraped_divis.get(divi_name, set()))

        # If no scraped categories, use existing
        if not scraped_cats and divi_name in existing_entries:
            scraped_cats = existing_entries[divi_name]

        # Sort categories
        scraped_cats = sorted(scraped_cats)

        # Build the row - now with up to 10 columns like the original
        row = [divi_name]

        is_partner = divi_name in partner_divis
        is_pdf = divi_name in pdf_divis

        if scraped_cats:
            # Has categories
            for cat in scraped_cats:
                row.append(cat)

            # Add Partner Divi marker if applicable (after categories)
            if is_partner:
                row.append("Partner Divi")

        elif is_pdf and is_partner:
            # Only PDF and Partner (no regular categories)
            row.append("")
            row.append("PDF, Partner Divi")
        elif is_partner:
            # Only Partner Divi (no regular categories)
            row.append("Partner Divi")
            row.append("-")
        elif is_pdf:
            # Only PDF
            row.append("")
            row.append("PDF")
        else:
            # No categories at all
            row.append("-")

        # Ensure at least 3 columns (Divi, Type, Type)
        while len(row) < 3:
            row.append("")

        rows.append(row)

    # Determine max columns needed
    max_cols = max(len(row) for row in rows)

    # Pad rows to same length
    for row in rows:
        while len(row) < max_cols:
            row.append("")

    # Write to CSV
    with open('Compleet_Overzicht_Divis.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        # Header
        header = ['Divi'] + ['Type'] * (max_cols - 1)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Generated: Compleet_Overzicht_Divis.csv ({len(rows)} entries, {max_cols} columns)")
    return rows

def generate_completed_overview_v2(scraped_divis, divi_urls, partner_divis, pdf_divis, existing_entries):
    """Generate the completed overview CSV v2 with URLs."""
    all_divis = set(scraped_divis.keys()) | set(existing_entries.keys())

    rows = []
    for divi_name in sorted(all_divis):
        # Get categories from scraped data
        scraped_cats = list(scraped_divis.get(divi_name, set()))

        # If no scraped categories, use existing
        if not scraped_cats and divi_name in existing_entries:
            scraped_cats = existing_entries[divi_name]

        # Sort categories
        scraped_cats = sorted(scraped_cats)

        # Get URL
        url = divi_urls.get(divi_name, "")

        # Build the row - now with up to 10 columns like the original + URL at end
        row = [divi_name]

        is_partner = divi_name in partner_divis
        is_pdf = divi_name in pdf_divis

        if scraped_cats:
            # Has categories
            for cat in scraped_cats:
                row.append(cat)

            # Add Partner Divi marker if applicable (after categories)
            if is_partner:
                row.append("Partner Divi")

        elif is_pdf and is_partner:
            # Only PDF and Partner (no regular categories)
            row.append("")
            row.append("PDF, Partner Divi")
        elif is_partner:
            # Only Partner Divi (no regular categories)
            row.append("Partner Divi")
            row.append("-")
        elif is_pdf:
            # Only PDF
            row.append("")
            row.append("PDF")
        else:
            # No categories at all
            row.append("-")

        rows.append((row, url))

    # Determine max columns needed (excluding URL)
    max_cols = max(len(row) for row, url in rows)

    # Pad rows to same length and add URL
    final_rows = []
    for row, url in rows:
        while len(row) < max_cols:
            row.append("")
        row.append(url)  # Add URL as last column
        final_rows.append(row)

    # Write to CSV
    with open('Compleet_Overzicht_Divis_v2.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        # Header
        header = ['Divi'] + ['Type'] * (max_cols - 1) + ['URL']
        writer.writerow(header)
        writer.writerows(final_rows)

    print(f"Generated: Compleet_Overzicht_Divis_v2.csv ({len(final_rows)} entries, {max_cols + 1} columns, including URL)")
    return final_rows

def generate_creative_catalog(scraped_divis, partner_divis):
    """Generate a creative catalog CSV organized by category."""
    # Invert the mapping: category -> list of divis
    category_divis = defaultdict(list)

    for divi_name, categories in scraped_divis.items():
        for cat in categories:
            info = {"name": divi_name, "is_partner": divi_name in partner_divis}
            category_divis[cat].append(info)

    # Also add divis without categories from scraped data
    for divi_name in partner_divis:
        if divi_name not in scraped_divis:
            category_divis["Partner Divi's"].append({"name": divi_name, "is_partner": True})

    # Write main catalog CSV
    rows = []
    rows.append(["Categorie", "Aantal Divi's", "Divi Namen"])

    for cat in sorted(category_divis.keys()):
        divi_list = sorted(category_divis[cat], key=lambda x: x["name"])
        divi_names = []
        for d in divi_list:
            name = d["name"]
            if d["is_partner"]:
                name += " (Partner)"
            divi_names.append(name)
        rows.append([cat, len(divi_list), ", ".join(divi_names)])

    with open('Catalogus_Per_Categorie.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Generated: Catalogus_Per_Categorie.csv ({len(category_divis)} categories)")

    # Write detailed catalog
    detail_rows = []
    detail_rows.append(["Divi Naam", "Categorieën", "Is Partner Divi"])

    for divi_name in sorted(scraped_divis.keys()):
        cats = sorted(scraped_divis[divi_name])
        is_partner = "Ja" if divi_name in partner_divis else "Nee"
        detail_rows.append([divi_name, ", ".join(cats), is_partner])

    # Add partner divis not in scraped data
    for divi_name in sorted(partner_divis):
        if divi_name not in scraped_divis:
            detail_rows.append([divi_name, "Partner Divi", "Ja"])

    with open('Catalogus_Detail.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(detail_rows)

    print(f"Generated: Catalogus_Detail.csv ({len(detail_rows)-1} entries)")

    return category_divis

def generate_html_catalog(scraped_divis, partner_divis, category_divis):
    """Generate an interactive HTML catalog."""
    # Get all categories
    all_categories = sorted(category_divis.keys())

    html = '''<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Indiveo Divi Catalogus</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            color: white;
            padding: 30px 0;
        }
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .stat-box {
            background: rgba(255,255,255,0.2);
            padding: 15px 30px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .search-filter {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        .search-box {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        .search-input {
            flex: 1;
            min-width: 300px;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .category-filter {
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            min-width: 250px;
            cursor: pointer;
        }
        .category-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }
        .category-tag {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .category-tag:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(102,126,234,0.4);
        }
        .category-tag.active {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .category-tag .count {
            background: rgba(255,255,255,0.3);
            padding: 2px 8px;
            border-radius: 10px;
            margin-left: 5px;
        }
        .results {
            margin-top: 20px;
        }
        .results-header {
            color: white;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        .divi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        .divi-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .divi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        .divi-card.partner {
            border-left: 4px solid #f5576c;
        }
        .divi-name {
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }
        .divi-categories {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .divi-cat {
            background: #f0f0f0;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            color: #666;
        }
        .partner-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
        }
        .no-results {
            text-align: center;
            color: white;
            padding: 50px;
            font-size: 1.2em;
        }
        footer {
            text-align: center;
            color: white;
            padding: 30px 0;
            opacity: 0.8;
        }
        @media (max-width: 768px) {
            header h1 {
                font-size: 1.8em;
            }
            .divi-grid {
                grid-template-columns: 1fr;
            }
            .search-input {
                min-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Indiveo Divi Catalogus</h1>
            <p>Overzicht van alle beschikbare Divi's voor zorgprofessionals</p>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number" id="totalDivis">0</div>
                    <div class="stat-label">Totaal Divi's</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" id="totalCategories">0</div>
                    <div class="stat-label">Categorieën</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" id="visibleDivis">0</div>
                    <div class="stat-label">Getoond</div>
                </div>
            </div>
        </header>

        <div class="search-filter">
            <div class="search-box">
                <input type="text" class="search-input" id="searchInput" placeholder="Zoek een Divi...">
                <select class="category-filter" id="categorySelect">
                    <option value="">Alle Categorieën</option>
'''

    # Add category options
    for cat in all_categories:
        count = len(category_divis[cat])
        html += f'                    <option value="{cat}">{cat} ({count})</option>\n'

    html += '''                </select>
            </div>
            <div class="category-tags" id="categoryTags">
'''

    # Add category tags
    for cat in all_categories:
        count = len(category_divis[cat])
        html += f'                <span class="category-tag" data-category="{cat}">{cat}<span class="count">{count}</span></span>\n'

    html += '''            </div>
        </div>

        <div class="results">
            <p class="results-header" id="resultsHeader">Alle Divi's</p>
            <div class="divi-grid" id="diviGrid">
'''

    # Add divi cards
    for divi_name in sorted(scraped_divis.keys()):
        cats = sorted(scraped_divis[divi_name])
        is_partner = divi_name in partner_divis
        card_class = "divi-card partner" if is_partner else "divi-card"
        cats_str = ",".join(cats)

        html += f'                <div class="{card_class}" data-name="{divi_name.lower()}" data-categories="{cats_str.lower()}">\n'
        html += f'                    <div class="divi-name">{divi_name}</div>\n'
        html += '                    <div class="divi-categories">\n'

        for cat in cats:
            html += f'                        <span class="divi-cat">{cat}</span>\n'

        if is_partner:
            html += '                        <span class="partner-badge">Partner Divi</span>\n'

        html += '                    </div>\n'
        html += '                </div>\n'

    # Add partner divis not in scraped data
    for divi_name in sorted(partner_divis):
        if divi_name not in scraped_divis:
            html += f'                <div class="divi-card partner" data-name="{divi_name.lower()}" data-categories="partner divi">\n'
            html += f'                    <div class="divi-name">{divi_name}</div>\n'
            html += '                    <div class="divi-categories">\n'
            html += '                        <span class="partner-badge">Partner Divi</span>\n'
            html += '                    </div>\n'
            html += '                </div>\n'

    html += '''            </div>
            <div class="no-results" id="noResults" style="display: none;">
                Geen Divi's gevonden voor deze zoekopdracht
            </div>
        </div>

        <footer>
            <p>Indiveo - Begrijpelijke patiëntvoorlichting</p>
        </footer>
    </div>

    <script>
        const searchInput = document.getElementById('searchInput');
        const categorySelect = document.getElementById('categorySelect');
        const categoryTags = document.querySelectorAll('.category-tag');
        const diviCards = document.querySelectorAll('.divi-card');
        const diviGrid = document.getElementById('diviGrid');
        const noResults = document.getElementById('noResults');
        const resultsHeader = document.getElementById('resultsHeader');
        const totalDivisEl = document.getElementById('totalDivis');
        const totalCategoriesEl = document.getElementById('totalCategories');
        const visibleDivisEl = document.getElementById('visibleDivis');

        // Initialize stats
        totalDivisEl.textContent = diviCards.length;
        totalCategoriesEl.textContent = categoryTags.length;
        visibleDivisEl.textContent = diviCards.length;

        let activeCategory = '';

        function filterDivis() {
            const searchTerm = searchInput.value.toLowerCase();
            const selectedCategory = categorySelect.value.toLowerCase();

            let visibleCount = 0;

            diviCards.forEach(card => {
                const name = card.dataset.name;
                const categories = card.dataset.categories;

                const matchesSearch = name.includes(searchTerm) || categories.includes(searchTerm);
                const matchesCategory = !selectedCategory || categories.includes(selectedCategory.toLowerCase());

                if (matchesSearch && matchesCategory) {
                    card.style.display = 'block';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            visibleDivisEl.textContent = visibleCount;
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
            diviGrid.style.display = visibleCount === 0 ? 'none' : 'grid';

            // Update header
            if (selectedCategory) {
                resultsHeader.textContent = `${categorySelect.value} (${visibleCount} Divi's)`;
            } else if (searchTerm) {
                resultsHeader.textContent = `Zoekresultaten voor "${searchTerm}" (${visibleCount} Divi's)`;
            } else {
                resultsHeader.textContent = `Alle Divi's (${visibleCount})`;
            }
        }

        searchInput.addEventListener('input', filterDivis);
        categorySelect.addEventListener('change', () => {
            // Update active tag
            categoryTags.forEach(tag => {
                tag.classList.remove('active');
                if (tag.dataset.category === categorySelect.value) {
                    tag.classList.add('active');
                }
            });
            filterDivis();
        });

        categoryTags.forEach(tag => {
            tag.addEventListener('click', () => {
                const category = tag.dataset.category;

                if (categorySelect.value === category) {
                    // Deselect
                    categorySelect.value = '';
                    tag.classList.remove('active');
                } else {
                    categorySelect.value = category;
                    categoryTags.forEach(t => t.classList.remove('active'));
                    tag.classList.add('active');
                }
                filterDivis();
            });
        });
    </script>
</body>
</html>
'''

    with open('Divi_Catalogus_Interactief.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated: Divi_Catalogus_Interactief.html")

def main():
    print("=" * 60)
    print("Indiveo Divi Catalogus Generator")
    print("=" * 60)
    print()

    # Extract data from scraped file
    print("1. Extracting divis from scraped data...")
    scraped_divis, divi_urls = extract_divis_from_scrape()
    print(f"   Found {len(scraped_divis)} divis")
    print(f"   Found {len(divi_urls)} URLs")

    # Read incomplete overview for Partner Divi info
    print("\n2. Reading incomplete overview for Partner Divi info...")
    partner_divis, pdf_divis, existing_entries = read_incomplete_overview()
    print(f"   Found {len(partner_divis)} Partner Divis")
    print(f"   Found {len(pdf_divis)} PDF entries")

    # Generate completed overview
    print("\n3. Generating completed overview CSV...")
    rows = generate_completed_overview(scraped_divis, partner_divis, pdf_divis, existing_entries)

    # Generate completed overview v2 with URLs
    print("\n3b. Generating completed overview CSV v2 (with URLs)...")
    rows_v2 = generate_completed_overview_v2(scraped_divis, divi_urls, partner_divis, pdf_divis, existing_entries)

    # Generate creative catalog
    print("\n4. Generating creative catalog CSV...")
    category_divis = generate_creative_catalog(scraped_divis, partner_divis)

    # Generate HTML catalog
    print("\n5. Generating interactive HTML catalog...")
    generate_html_catalog(scraped_divis, partner_divis, category_divis)

    print("\n" + "=" * 60)
    print("COMPLETE! Generated files:")
    print("  1. Compleet_Overzicht_Divis.csv - Same structure as original")
    print("  1b. Compleet_Overzicht_Divis_v2.csv - With URL column")
    print("  2. Catalogus_Per_Categorie.csv - Overview per category")
    print("  3. Catalogus_Detail.csv - Detailed divi list")
    print("  4. Divi_Catalogus_Interactief.html - Interactive HTML")
    print("=" * 60)

if __name__ == '__main__':
    main()
