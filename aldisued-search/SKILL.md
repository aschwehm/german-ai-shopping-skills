---
name: aldisued-search
description: >-
  Use this skill whenever the user asks to search products, grocery items, or special offers (Aktionen)
  at ALDI SÜD (aldi-sued.de). Supports filtering for Thursday offers, custom store zip codes,
  and inspecting offer validity dates. Always delegates execution to a Gemini Flash subagent.
---

# ALDI SÜD Search & Offers Inspector Skill

## Execution Policy (Mandatory)

1. **Always Delegate to a Subagent:**
   When searching ALDI SÜD or checking weekly offers, the parent agent must NEVER execute searches in the main context. Always spawn a subagent via `invoke_subagent`:
   * `TypeName`: `"research"` (or `"self"`)
   * `Role`: `"Aldi Shopping Researcher"`
   * `Model`: `"flash"` (Gemini 3.8 Flash)
   * **Thinking Effort:** Fixed to **Medium** (balanced reasoning: fast search while checking exact offer dates and Thursday availability).

2. **Rate Limiting:**
   * Keep a polite delay of **1.5 to 2.5 seconds** between requests.
   * Cap search queries to 6–8 results.

---

## Store Configuration & Thursday Logic

* **Filial-Standort:** Anpassbar über `--zip <PLZ>` oder Umgebungsvariable `ALDI_ZIP` (Standard: `50667` Köln).
* **Donnerstags-Prüfung (`--thursday`):** Filtert gezielt nach Angeboten und Aktionen, die ab Donnerstag gültig sind, ideal für die wöchentliche Donnerstags-Einkaufsroute.

---

## CLI Commands

```bash
# 1. Speziell Angebote für Donnerstag abrufen:
python3 ./aldisued-search/scripts/search.py --thursday --max 6

# 2. Suche nach bestimmtem Produkt:
python3 ./aldisued-search/scripts/search.py --query "Kaffee" --max 6

# 3. Bestimmte Filiale über PLZ ansteuern (z. B. Köln 50667):
python3 ./aldisued-search/scripts/search.py --query "Milch" --zip 50667
```
