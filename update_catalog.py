import csv
import re

# Read the CSV and create a mapping of Divi name to URL
url_mapping = {}
with open('Compleet_Overzicht_Divis_v2.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if row and len(row) >= 12:
            name = row[0].strip()
            url = row[-1].strip() if row[-1].strip().startswith('http') else ''
            if name:
                url_mapping[name.lower()] = url

print(f"Loaded {len(url_mapping)} URL mappings")

# Read the HTML file
with open('Divi_Catalogus_Indiveo_Style.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Function to add link to divi card
def add_link_to_card(match):
    full_match = match.group(0)
    name = match.group(1)
    display_name = match.group(2)
    categories = match.group(3)

    # Find URL for this divi
    url = url_mapping.get(name.lower(), '')

    if url:
        # Add link wrapper around the card content
        return full_match.replace(
            f'<div class="divi-name">{display_name}</div>',
            f'<a href="{url}" target="_blank" class="divi-link"><div class="divi-name">{display_name}</div></a>'
        )
    return full_match

# Pattern to match divi cards
pattern = r'<div class="divi-card(?:\s+partner)?" data-name="([^"]+)" data-categories="[^"]+">\s*<div class="divi-name">([^<]+)</div>\s*<div class="divi-categories">(.*?)</div>\s*</div>'

# Update cards with links
html = re.sub(pattern, add_link_to_card, html, flags=re.DOTALL)

# Add CSS for links
link_css = """
        .divi-link {
            text-decoration: none;
            color: inherit;
            display: block;
        }

        .divi-link:hover .divi-name {
            color: var(--color-primary);
        }

        /* Credits Section */
        .credits {
            background: var(--color-bg-alt);
            border-radius: 8px;
            padding: 24px;
            margin-top: 40px;
            text-align: center;
        }

        .credits-title {
            font-family: var(--font-heading);
            font-size: 1rem;
            font-weight: 600;
            color: var(--color-heading);
            margin-bottom: 12px;
        }

        .credits p {
            color: var(--color-text-light);
            font-size: 0.9rem;
            margin-bottom: 8px;
            line-height: 1.6;
        }

        .credits a {
            color: var(--color-primary);
            text-decoration: none;
        }

        .credits a:hover {
            text-decoration: underline;
        }

        .credits-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--color-bg);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            color: var(--color-text-light);
            margin-top: 12px;
            border: 1px solid var(--color-border);
        }

        /* Version Switcher */
        .version-switcher {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        }

        .version-btn {
            background: var(--color-heading);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            font-family: var(--font-body);
            font-size: 0.9rem;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.2s;
        }

        .version-btn:hover {
            background: var(--color-primary);
            transform: translateY(-2px);
        }
"""

# Insert CSS before closing </style>
html = html.replace('    </style>', link_css + '\n    </style>')

# Add credits section before footer
credits_html = """
        <div class="credits">
            <div class="credits-title">Over deze catalogus</div>
            <p>Deze interactieve Divi catalogus is gemaakt en wordt beheerd door <strong>Jan Sytze Heegstra</strong> in samenwerking met <strong>Claude Code</strong> (Anthropic AI) als een gratis zijproject en voorbeeld.</p>
            <p>Deze tool is <strong>open source</strong> en vrij te gebruiken.</p>
            <p>Voor directe integratie op uw website of hulp bij implementatie, neem contact op met:</p>
            <p><a href="mailto:jan@cazvid.com">jan@cazvid.com</a></p>
            <div class="credits-badge">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
                Gemaakt met Claude Code
            </div>
        </div>

        <footer>
"""

html = html.replace('<footer>', credits_html)

# Write updated HTML
with open('Divi_Catalogus_Indiveo_Style.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated Divi_Catalogus_Indiveo_Style.html with links and credits")

# Count how many links were added
link_count = html.count('class="divi-link"')
print(f"Added {link_count} links to divi cards")
