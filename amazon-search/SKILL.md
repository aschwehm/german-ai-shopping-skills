---
name: amazon-search
description: >-
  Use this skill whenever the user asks to search for products on Amazon (e.g. Amazon.de),
  scrape or inspect Amazon product links/ASINs, compare specifications, verify Prime eligibility,
  or evaluate items against criteria. Always delegates execution to a Gemini Flash subagent.
---

# Amazon Search & Product Inspector Skill

## Execution Policy (Mandatory)

1. **Always Delegate to a Subagent:**
   When the user asks to search Amazon or inspect Amazon links, the parent agent must NEVER execute searches in the main context. Always spawn a subagent via `invoke_subagent`:
   * `TypeName`: `"research"` (or `"self"`)
   * `Role`: `"Amazon Shopping Researcher"`
   * `Model`: `"flash"` (Gemini 3.8 Flash)
   * **Thinking Effort:** Fixed to **Medium** (balanced reasoning: fast execution while strictly vetting detailed dimensions, colors, materials, and Prime status).

2. **Rate Limiting & Anti-Block Safeguard:**
   To prevent Amazon from blocking requests or triggering CAPTCHAs:
   * Keep a polite delay of **1.5 to 3.0 seconds** between consecutive requests.
   * Cap search queries to 5–10 results per query (`--max 8`).
   * When batch scraping multiple links, use the built-in batch scraper which enforces 3-second delays between items.

---

## Tool Functions & CLI Commands

The underlying engine is located at `./amazon-scraper` and registered in `~/.gemini/config/mcp_config.json`.

### 1. Product Search (`search_amazon`)
Searches Amazon.de with criteria matching and returns ASIN, title, price, rating, reviews, thumbnail, and Prime status.
```bash
node ./amazon-search/scripts/search.js --query "<Suchbegriff>" --domain "amazon.de" --max 8
```

### 2. Product Inspection (`scrape_amazon_product`)
Inspects a specific Amazon product URL or ASIN. Extracts complete title, price, discount, brand, seller, Prime status, bullet points/features, technical specs, high-resolution images, and full description.
```bash
node ./amazon-search/scripts/search.js --url "<Amazon-URL>"
# OR by ASIN:
node ./amazon-search/scripts/search.js --asin "<ASIN>"
```

### 3. Batch Inspection (`scrape_amazon_batch`)
Scrapes multiple products sequentially with built-in rate-limiting delays.
```bash
node ./amazon-search/scripts/search.js --batch "<URL1>,<URL2>,<URL3>"
```

---

## Output Guidelines

* Always verify that products match the user's specific dimensions, colors, materials, and Prime availability.
* Present direct, clean markdown links (`https://www.amazon.de/dp/<ASIN>`).
* Highlight any criteria deviations immediately.

---

## Attribution & Modifications

* **Upstream Project:** Based on [`amazon-scrapper-mcp`](https://github.com/BillyMRX1/amazon-scrapper-mcp) by BillyMRX1.
* **Modifications in this Skill:**
  1. Wrapped for modular AI agent execution with dedicated subagent policies (Gemini 3.8 Flash, Medium Effort).
  2. Implemented client-side jitter delays (1.5s–3.0s) and search result capping (`--max 8`) to respect Amazon rate limits and prevent 503 / CAPTCHA blocks.
  3. Added unified CLI interface (`search.js`) supporting direct `--query`, `--asin`, `--url`, and `--batch` scraping.
  4. Regional adaptation for Amazon.de (`amazon.de` domain default, German currency and specs parsing).
