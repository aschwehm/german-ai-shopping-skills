---
name: rewe-search
description: >-
  Use this skill whenever the user asks to search products, groceries, or weekly offers at REWE (rewe.de).
  Supports market-bound searches (configurable via REWE_MARKET_ID or --market <ID>),
  filtering weekly deals, and checking availability states ("vorrätig", "meist vorrätig", "nicht vorrätig").
  Always delegates execution to a Gemini Flash subagent.
---

# REWE Search & Market Offers Inspector Skill

## Execution Policy (Mandatory)

1. **Always Delegate to a Subagent:**
   When searching REWE or checking market offers, the parent agent must NEVER execute searches in the main context. Always spawn a subagent via `invoke_subagent`:
   * `TypeName`: `"research"` (or `"self"`)
   * `Role`: `"REWE Shopping Researcher"`
   * `Model`: `"flash"` (Gemini 3.8 Flash)
   * **Thinking Effort:** Fixed to **Medium** (balanced reasoning: fast search while strictly verifying local market availability and weekly deals).

2. **Rate Limiting:**
   * Keep a polite delay of **1.5 to 2.5 seconds** between requests.
   * Cap search queries to 6–8 results.

---

## Market Configuration & Availability Levels

* **Markt-Konfiguration:** Konfigurierbar über `--market <ID>` oder Umgebungsvariable `REWE_MARKET_ID` (Standard: `8100134` für Köln Rudolfplatz). Ohne Angabe werden überregionale Standardangebote geladen.
* **Verfügbarkeitsstufen:**
  * **Vorrätig:** Im Markt gelistet bzw. Prospektangebot.
  * **Meist vorrätig:** Hohe Wahrscheinlichkeit vor Ort.
  * **Nicht vorrätig:** Aktuell im ausgewählten Markt vergriffen.

---

## CLI Commands

```bash
# 1. Aktuelle Angebote des Markts abrufen:
python3 ./rewe-search/scripts/search.py --offers --max 6

# 2. Produkt suchen (z. B. Butter, Kaffee):
python3 ./rewe-search/scripts/search.py --query "Butter" --max 6

# 3. Bestimmte Filiale ansteuern (z. B. Markt-ID 8100134 Köln Rudolfplatz):
python3 ./rewe-search/scripts/search.py --query "Milch" --market 8100134
```
