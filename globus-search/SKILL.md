---
name: globus-search
description: >-
  Use this skill whenever the user asks to search for products on Globus Baumarkt (globus-baumarkt.de),
  inspect Globus product links, compare prices and specifications, or evaluate live store
  stock for in-store pickup ("Reservieren & Abholen") with two-tier store prioritization.
  Always delegates execution to a Gemini Flash subagent.
---

# Globus Baumarkt Search & Product Inspector Skill

## Execution Policy (Mandatory)

1. **Always Delegate to a Subagent:**
   When the user asks to search Globus Baumarkt or inspect product links, the parent agent must NEVER execute searches in the main context. Always spawn a subagent via `invoke_subagent`:
   * `TypeName`: `"research"` (or `"self"`)
   * `Role`: `"Globus Baumarkt Shopping Researcher"`
   * `Model`: `"flash"` (Gemini 3.8 Flash)
   * **Thinking Effort:** Fixed to **Medium** (balanced reasoning: fast search while vetting exact stock counters, dimensions, prices, and shipping fees).

2. **Rate Limiting Safeguard:**
   * Keep a polite delay of **1.5 to 2.5 seconds** between consecutive requests.
   * Cap search queries to 5–6 results (`--max 6`).
   * Batch inspect multiple products with `--batch "<URL1>,<URL2>" --delay 2.0`.

---

## Filial-Priorisierung & Verfügbarkeitsregeln

Konfigurierbar über Umgebungsvariablen (Standard: `GLOBUS_PRIMARY_STORE_ID=71` Brühl, `GLOBUS_SECONDARY_STORE_ID=78` Meerbusch, `GLOBUS_ZIP=50667` Köln).
Globus Baumarkt liefert exakte Live-Bestände in Stückzahlen:

1. **1. Wahl (Bevorzugt) – Primärmarkt (z. B. Brühl):**
   * Wenn Bestand > 0 Stück: Sofort im Primärmarkt reservieren & abholen.
2. **2. Wahl (Sekundär) – Sekundärmarkt (z. B. Meerbusch):**
   * Wenn Primärmarkt 0 Stück hat, aber Sekundärmarkt > 0 Stück: Im Sekundärmarkt abholen.
3. **Kein Vor-Ort-Bestand (0 Stück in beiden Märkten):**
   * **Sperrgut / Großgerät:** Lieferzeit ≥ 7 Werktage -> Vor-Ort-Bestellung im Markt prüfen (um Speditionsaufschläge zu vermeiden).
   * **Kleinartikel:** Warenwert < 30 € mit anfallenden Versandkosten (z. B. 4,99 €) -> Uninteressant für Einzelkauf (andere Quellen wie Amazon bevorzugen).

---

## Tool Functions & CLI Commands

Der Scraper liegt unter `./globus-search/scripts/search.py` und nutzt Python `curl_cffi`.

### 1. Produktsuche (`search_globus`)
Sucht auf `globus-baumarkt.de` und liefert Titel, SKU, Preis und Link:
```bash
python3 ./globus-search/scripts/search.py --query "<Suchbegriff>" --max 6
```

### 2. Produktprüfung & Live-Bestandsabfrage (`scrape_globus_product`)
Prüft ein Produkt per URL und fragt die exakten Stückzahlen in den konfigurierten Märkten ab:
```bash
python3 ./globus-search/scripts/search.py --url "<Globus-URL>"
```

### 3. Batch-Prüfung mehrerer Artikel
```bash
python3 ./globus-search/scripts/search.py --batch "<URL1>,<URL2>" --delay 2.0
```
