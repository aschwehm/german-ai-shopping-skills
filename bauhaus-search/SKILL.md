---
name: bauhaus-search
description: >-
  Use this skill whenever the user asks to search for products on BAUHAUS (bauhaus.info),
  inspect Bauhaus product links/SKUs, compare technical specifications, or evaluate store
  availability for in-store pickup ("Reservieren & Abholen") at local BAUHAUS stores.
  Always delegates execution to a Gemini Flash subagent.
---

# BAUHAUS Search & Product Inspector Skill

## Execution Policy (Mandatory)

1. **Always Delegate to a Subagent:**
   When the user asks to search Bauhaus or inspect Bauhaus links, the parent agent must NEVER execute searches in the main context. Always spawn a subagent via `invoke_subagent`:
   * `TypeName`: `"research"` (or `"self"`)
   * `Role`: `"Bauhaus Shopping Researcher"`
   * `Model`: `"flash"` (Gemini 3.8 Flash)
   * **Thinking Effort:** Fixed to **Medium** (balanced speed while vetting dimensions, delivery times, shipping costs, and local pickup eligibility).

2. **Rate Limiting & Safety Safeguards:**
   * Keep a polite delay of **1.5 to 3.0 seconds** between consecutive requests.
   * Cap search queries to 5–8 results (`--max 6`).
   * Never interfere with the user's running browser sessions or open tabs.

---

## Filial- & Verfügbarkeitsregeln für lokale BAUHAUS-Fachcentren

Konfigurierbar über `--store <ID>` oder Umgebungsvariable `BAUHAUS_STORE_ID` (Standard: `616` für BAUHAUS Köln-Kalk).
Der Scraper prüft jedes Produkt anhand der 3 Kernkriterien:

1. **Sofort abholbereit / Reguläre Lagerware (Bevorzugt):**
   * Kennzeichen: Lieferzeit 1–3 Werktage, reguläre Paketware, versandkostenfrei.
   * Bewertung: Hohe Verfügbarkeit im Markt. "Reservieren & Abholen" empfohlen.
2. **Bestellbar vor Ort / Sperrgut (Akzeptabel bei Großartikeln):**
   * Kennzeichen: Speditionsware oder Lieferzeit ≥ 7 Werktage (z. B. Geräteschränke, Gartenhäuser, schwere Badewannen).
   * Bewertung: "Bestellbar im Markt". Vor-Ort-Kauf/Abholung ist sinnvoll, um teure Speditionszuschläge zu sparen.
3. **Online-Kleinartikel mit Versandzuschlag (Ausschluss):**
   * Kennzeichen: Warenwert < 30 € und anfallende Versandkosten (z. B. 5,70 € Paketversand).
   * Bewertung: Nicht für Einzelkauf bei Bauhaus empfohlen; auf alternative Händler (z. B. Amazon Prime) ausweichen, es sei denn, eine Sammelbestellung übersteigt die 30 €-Freigrenze.

---

## Tool Functions & CLI Commands

Der Scraper liegt unter `bauhaus-search/scripts/search.py` und nutzt Python `curl_cffi` (Chrome TLS Impersonation).

### 1. Produktsuche (`search_bauhaus`)
Sucht auf `bauhaus.info` und liefert Titel, SKU, Preis, Bewertung und Bild.
```bash
python3 ./bauhaus-search/scripts/search.py --query "<Suchbegriff>" --max 6
```

### 2. Produktprüfung (`scrape_bauhaus_product`)
Liest ein Produkt per URL oder SKU aus und liefert die Verfügbarkeitseinstufung:
```bash
# Per URL:
python3 ./bauhaus-search/scripts/search.py --url "<Bauhaus-URL>"

# Per Artikelnummer (SKU):
python3 ./bauhaus-search/scripts/search.py --sku "<SKU>"
```

### 3. Batch-Prüfung mehrerer Artikel
Prüft mehrere Artikel nacheinander mit automatischem Rate-Limit-Intervall (Standard: 2 Sekunden):
```bash
python3 ./bauhaus-search/scripts/search.py --batch "<SKU1>,<SKU2>,<SKU3>" --delay 2.0
```

---

## Blueprint für zukünftige Shop-Skills (Hornbach, Obi etc.)

Dieses Modul dient als Referenz-Architektur für weitere Baumärkte & Shops:
1. **Engine:** `curl_cffi` Session mit Chrome-TLS-Fingerprint (`impersonate="chrome124"`), um WAF/Cloudflare-Hürden schlank ohne Browser-Overhead zu überwinden.
2. **Datenquelle:** Schema.org (`ItemList` für Suche, `Product` mit `OfferShippingDetails` für Details).
3. **Filial-Heuristik:** Trennung nach Sofortware (1–3 Tage), Spedition/Sperrgut (≥ 7 Tage) und Kleinartikel-Freigrenzen (< 30 €).
