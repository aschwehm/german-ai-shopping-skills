---
name: centershop-search
description: >-
  Use this skill whenever the user asks to inspect the weekly leaflet (Prospekt) or search products
  and budget DIY/hardware (Baumarkt) items at CenterShop (centershop.de). Supports retrieving current weekly
  flyer dates and PDFs, checking store-only availability, and categorizing items for local branches.
  Always delegates execution to a Gemini Flash subagent.
---

# CenterShop Prospekt & Product Inspector Skill

## Execution Policy (Mandatory)

1. **Always Delegate to a Subagent:**
   When checking CenterShop leaflets or searching products, the parent agent must NEVER execute searches in the main context. Always spawn a subagent via `invoke_subagent`:
   * `TypeName`: `"research"` (or `"self"`)
   * `Role`: `"CenterShop Shopping Researcher"`
   * `Model`: `"flash"` (Gemini 3.8 Flash)
   * **Thinking Effort:** Fixed to **Medium** (balanced reasoning: fast lookup while checking weekly flyer validity dates and in-store tags).

2. **Rate Limiting:**
   * Keep a polite delay of **1.5 to 2.5 seconds** between requests.
   * Cap search queries to 6–8 results.

---

## Filial- & Prospektlogik für CenterShop

* **Wochenprospekt:** Unter `https://www.centershop.de/prospekt/` wird die aktuelle KW und der PDF-Direktlink für die Woche ausgelesen.
* **Filial-Verfügbarkeit:** Kennzeichnung von Artikeln mit `Nur in den Filialen erhältlich!` vs. `Bestellartikel`.
* **Baumarkt-Ergänzung:** Günstiges Basissortiment für Werkzeuge, Haushaltswaren und Gartenartikel zur Vermeidung von Extrafahrten zu Großbaumärkten.

---

## CLI Commands

```bash
# 1. Aktuellen Wochenprospekt mit Gültigkeitsdatum und PDF-Link abrufen:
python3 ./centershop-search/scripts/search.py --prospekt

# 2. Baumarkt-Sortiment durchsuchen:
python3 ./centershop-search/scripts/search.py --category baumarkt --max 6

# 3. Bestimmten Artikel suchen:
python3 ./centershop-search/scripts/search.py --query "Akkuschrauber"
```
