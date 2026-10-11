# 🛒 Shopping Skills für KI-Agenten

[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776ab.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18+-339933.svg?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Plattformen](https://img.shields.io/badge/Plattformen-Antigravity%20|%20Claude%20Code%20|%20Codex%20|%20Cursor-7928CA.svg)]()
[![Region](https://img.shields.io/badge/Region-Deutschland%20%F0%9F%87%A9%F0%9F%87%AA-red.svg)]()
[![Status](https://img.shields.io/badge/Status-Aktiv%20%26%20Getestet-success.svg)]()

Modulare Such- und Bestandsabfrage-Tools für KI-Agenten (**Google Antigravity CLI**, **Claude Code**, **OpenAI Codex** und **Cursor**).

Die Skills fragen bei deutschen Händlern (**ALDI SÜD**, **REWE**, **BAUHAUS**, **Globus Baumarkt**, **CenterShop** und **Amazon.de**) aktuelle Wochenangebote, Live-Filialbestände, Abholmöglichkeiten ("Reservieren & Abholen") und Artikeldetails ab. Alle Abfragen laufen über Python `curl_cffi` direkt und unauffällig im Hintergrund, ohne Browserfenster zu öffnen.

---

## 💡 Was man damit machen kann

Statt selbst durch zig Onlineshops zu klicken und Verfügbarkeiten mühsam abzugleichen, übernimmt das der KI-Agent anhand deiner Vorgaben:

### Beispiel: Gezielte Baumarktsuche mit Abholung vor Ort (BAUHAUS)
> **Deine Anfrage an den Agenten:**  
> *"Ich brauche für meine Hauswand einen anthrazitfarbenen Wandbriefkasten mit integriertem Zeitungsfach. Er muss heute im BAUHAUS Köln-Kalk abholbereit sein (keine tagelange Spedition), aus wetterfestem Stahl sein und unter 60 € kosten."*

**Was der Agent im Hintergrund macht:**
1. Er sucht im BAUHAUS-Katalog nach passenden Briefkästen für die Filiale Köln-Kalk (`--store 616`).
2. Er filtert Modelle heraus, die nicht direkt im Markt liegen (z. B. Speditionsware oder Artikel, die erst bestellt werden müssen).
3. Er gleicht Preis (< 60 €) und Ausstattung (Zeitungsfach, Material) ab.
4. Er liefert direkt das passende Produkt:
   > *"Im BAUHAUS Köln-Kalk sofort zur Abholung bereit:*  
   > *• **Burg-Wächter Wandbriefkasten Lucenta** (Art.-Nr.: `26224277`) für **47,20 €** (abholbereit im BAUHAUS Köln-Kalk)."*

### Tipp: Eigene Filialen einmalig im Agenten merken
Du musst dem Agenten nicht bei jeder Frage deine Postleitzahl oder Markt-IDs mitgeben. Sag es ihm einfach einmal am Anfang:

> **Einmalige Einrichtung:**  
> *"Merk dir für meine Einkäufe: Mein ALDI SÜD ist in 50667 Köln, mein REWE der Markt am Rudolfplatz (8100134) und mein BAUHAUS Köln-Kalk (616). Speicher dir das als Standard ein."*

Danach reichen ganz kurze, natürliche Alltagsfragen:
* *"Gibt es bei ALDI diese Woche vegane Lebensmittel im Sonderangebot?"*
* *"Hat mein REWE Hafermilch im Angebot?"*
* *"Ich brauche 20 kg Flexkleber. Prüf erst Globus Baumarkt Brühl – wenn da unter 5 Sack liegen, schau im BAUHAUS Köln-Kalk."*
* *"Lies das aktuelle Wochenprospekt von CenterShop als PDF aus und such nach Werkzeug-Angeboten unter 15 €."*

---

## 🏬 Unterstützte Händler

| Skill | Händler | Typ | Was der Skill kann |
|---|---|---|---|
| **[`aldisued-search`](aldisued-search/)** | ALDI SÜD | CLI / Skill | Wochenangebote, Donnerstag-Aktionen, Angebote nach PLZ |
| **[`rewe-search`](rewe-search/)** | REWE | CLI / Skill | Filialangebote, Bestandsanzeige (`vorrätig`, `meist vorrätig`, `nicht vorrätig`) |
| **[`bauhaus-search`](bauhaus-search/)** | BAUHAUS | CLI / Skill | Abholung vor Ort, Paketversand (ab 30 € frei) vs. Spedition |
| **[`globus-search`](globus-search/)** | Globus Baumarkt | CLI / Skill | Live-Bestand in Stückzahlen für Haupt- und Ausweichfiliale |
| **[`centershop-search`](centershop-search/)** | CenterShop | CLI / Skill | Aktuelles PDF-Prospekt, Gültigkeit, "Nur in Filiale"-Kennzeichnung |
| **[`amazon-search`](amazon-search/)** | Amazon.de | MCP / Skill | Produktsuche, ASIN-Details, Prime-Status, technische Daten |

---

## ⚡ Schnellstart

### 1. Installation

```bash
# Python-Abhängigkeiten installieren:
pip install -r requirements.txt

# Optional für die Amazon-Suche (Node.js & Playwright):
cd amazon-search && npm install && cd ..
```

### 2. Einbindung in deinen Agenten

#### Google Antigravity CLI (`agy`)
Ordner einfach in das Skills-Verzeichnis kopieren:
```bash
# Global installieren:
cp -r */ ~/.gemini/skills/

# Oder direkt im Projektordner:
cp -r */ .gemini/skills/
```

#### Claude Code
In den Skills-Ordner von Claude Code kopieren:
```bash
cp -r */ ~/.claude/skills/
```
Oder direkt in deiner `CLAUDE.md` als Werkzeuge eintragen:
```markdown
- ALDI SÜD: `python3 ./aldisued-search/scripts/search.py --query "..."`
- REWE: `python3 ./rewe-search/scripts/search.py --query "..."`
- BAUHAUS: `python3 ./bauhaus-search/scripts/search.py --query "..."`
- Globus Baumarkt: `python3 ./globus-search/scripts/search.py --query "..."`
- CenterShop: `python3 ./centershop-search/scripts/search.py --prospekt`
- Amazon.de: `node ./amazon-search/scripts/search.js --query "..."`
```

#### Cursor, Codex & Terminal
Jedes Skript kann direkt im Terminal aufgerufen werden und gibt sauberes JSON aus:
```bash
python3 ./bauhaus-search/scripts/search.py --query "Wandbriefkasten"
```

---

## ⚙️ Eigene Filiale einstellen

Alle Filialen lassen sich per Umgebungsvariable oder Befehlszeilen-Parameter anpassen:

| Skill | Parameter | Umgebungsvariable | Standard-Beispiel (Köln) | Zweck |
|---|---|---|---|---|
| `aldisued-search` | `--zip <PLZ>` | `ALDI_ZIP` | `50667` | Regionale Wochenangebote |
| `rewe-search` | `--market <ID>` | `REWE_MARKET_ID` | `8100134` (Rudolfplatz) | Lokale Filialangebote |
| `bauhaus-search` | `--store <ID>` | `BAUHAUS_STORE_ID` | `616` (Köln-Kalk) | Markt für Abholung |
| `globus-search` | `--zip <PLZ>` | `GLOBUS_ZIP` | `50667` | PLZ für Umkreissuche |
| `globus-search` | – | `GLOBUS_PRIMARY_STORE_ID` | `71` (Brühl) | Hauptfiliale |
| `globus-search` | – | `GLOBUS_SECONDARY_STORE_ID` | `78` (Meerbusch) | Ausweichfiliale |

---

## 🔍 Beispiele & JSON-Ausgaben

### 1. ALDI SÜD (`aldisued-search`)
Holt aktuelle Wochenangebote oder filtert gezielt nach Artikeln für Donnerstag (`--thursday`):
```bash
python3 ./aldisued-search/scripts/search.py --thursday --max 2
```
```json
[
  {
    "title": "Garten-Klappstuhl Aluminium",
    "price": 29.99,
    "currency": "EUR",
    "campaign_date": "2026-10-15",
    "is_thursday_special": true,
    "available": true,
    "url": "https://www.aldi-sued.de/de/angebote/..."
  }
]
```

### 2. REWE (`rewe-search`)
Ruft Filialangebote ab oder sucht im Sortiment mit Bestandsstatus:
```bash
python3 ./rewe-search/scripts/search.py --offers --max 2
```
```json
[
  {
    "title": "Bio Vollmilch 3,8% 1L",
    "price": 1.49,
    "regular_price": 1.79,
    "market_id": "8100134",
    "availability": "vorrätig",
    "valid_until": "2026-10-17"
  }
]
```

### 3. BAUHAUS (`bauhaus-search`)
Prüft, ob der Artikel direkt im Markt abholbereit ist, regulär per Paket geliefert wird oder teure Speditionskosten anfallen:
```bash
python3 ./bauhaus-search/scripts/search.py --query "Wandbriefkasten" --max 1
```
```json
[
  {
    "sku": "26224277",
    "title": "Burg-Wächter Wandbriefkasten Lucenta",
    "price": 47.20,
    "store_availability": {
      "store_id": "616",
      "store_name": "BAUHAUS Köln-Kalk",
      "available_locally": true,
      "pickup_status": "Sofort verfügbar im Markt (Reservieren & Abholen bevorzugt)"
    },
    "shipping": {
      "parcel_possible": true,
      "shipping_cost": 0.00,
      "free_shipping": true
    }
  }
]
```

### 4. Globus Baumarkt (`globus-search`)
Gibt die genaue Stückzahl vor Ort im Regal für zwei Wunschmärkte aus:
```bash
python3 ./globus-search/scripts/search.py --url "https://www.globus-baumarkt.de/p/knauf-flexkleber-extra-20-kg-0779053197/"
```
```json
{
  "name": "Knauf Flexkleber extra 20 kg",
  "sku": "0779053197",
  "price": "22.00 €",
  "primary_store": {
    "name": "Brühl",
    "stock_count": 154,
    "available": true
  },
  "secondary_store": {
    "name": "Meerbusch",
    "stock_count": 155,
    "available": true
  },
  "fulfillment_type": "Sofort abholbereit (Brühl)",
  "verdict": "1. Wahl: In Brühl reservieren & abholen"
}
```

### 5. CenterShop (`centershop-search`)
Findet das aktuelle Prospekt auf der Website und gibt den PDF-Link sowie das Gültigkeitsdatum aus:
```bash
python3 ./centershop-search/scripts/search.py --prospekt
```
```json
{
  "prospekt_url": "https://www.centershop.de/wp-content/uploads/prospekte/KW42.pdf",
  "validity_text": "Gültig von Montag, 12. bis Samstag, 17. Oktober 2026",
  "status": "active"
}
```

### 6. Amazon.de (`amazon-search`)
Sucht Produkte, liest ASIN-Details aus und prüft Prime-Verfügbarkeit:
```bash
node ./amazon-search/scripts/search.js --query "Kissen 30x50 Samt" --max 2
```
```json
[
  {
    "asin": "B09XXXXXX",
    "title": "Samtkissen 30x50 cm Bezug",
    "price": 14.99,
    "prime": true,
    "rating": 4.6,
    "url": "https://www.amazon.de/dp/B09XXXXXX"
  }
]
```

---

## 🧩 Credits & Entwicklung mit KI

* **Amazon-Basis:** Das Modul `amazon-search` basiert ursprünglich auf [`amazon-scrapper-mcp`](https://github.com/BillyMRX1/amazon-scrapper-mcp) von [BillyMRX1](https://github.com/BillyMRX1) und wurde um Subagenten-Konfigurationen (`Gemini 3.8 Flash`), automatische Jitter-Pausen (1,5 bis 3 Sekunden) gegen Bot-Sperren, ein schlankes CLI-Skript (`search.js`) und DE-Lokalisierung erweitert.
* **KI-Entwicklung:** Alle Skills wurden sorgfältig konzipiert, live gegen die Shop-Websites getestet und im Pair-Programming mit KI (Google Antigravity / Gemini) erstellt. Da sich Shop-APIs und Webseiten-Layouts im Laufe der Zeit ändern können, sind Community-Verbesserungen ausdrücklich willkommen.

---

## 🤝 Mitmachen & Eigene Skills beisteuern (Contributing)

Ich freue mich sehr, wenn du auf Basis dieses Projekts eigene Sachen baust, bestehende Parser verbesserst oder neue Händler hinzufügst! Neue Shop-Skills (z. B. **Hornbach**, **OBI**, **Lidl**, **dm**, **Rossmann**, **Edeka** etc.) sind als Pull Requests herzlich willkommen.

### Richtlinien für Pull Requests (PRs):
1. **Eigener Skill-Ordner:** Jeder neue Shop bekommt einen eigenen Ordner mit `SKILL.md` (Agenten-Instruktionen) und dem Skript unter `scripts/search.py`.
2. **Standardisiertes JSON:** Jedes Tool muss bei CLI-Aufruf sauberes JSON auf `stdout` ausgeben.
3. **Schonendes Scraping:** Feste Pausen/Delays (mind. 1,5 bis 2,5 Sekunden) einbauen, um Serverlasten zu minimieren.
4. **Keine festen Privatdaten:** Niemals persönliche Adressen oder IDs fest im Code verdrahten; immer Umgebungsvariablen mit neutralen Standardwerten (z. B. Köln) verwenden.
5. **Kurze PR-Beschreibung:** Schreib kurz dazu, was du geändert hast und wie du es getestet hast.

### Fehler oder Shop-Änderungen melden:
Wenn ein Händler sein Webseiten-Layout ändert, ein Endpunkt nicht mehr antwortet oder ein Bot-Schutz greift: Öffne gerne einfach ein [GitHub Issue](https://github.com/aschwehm/german-ai-shopping-skills/issues) mit dem aufgerufenen Befehl und der Fehlermeldung.

---

## ⚖️ Rechtlicher Hinweis

Dieses Repository ist ein privates Open-Source-Projekt zu Lern- und Forschungszwecken rund um KI-Agenten.

* **Keine Verbindung zu den Händlern:** Es besteht keinerlei geschäftliche Verbindung oder Autorisierung durch **ALDI SÜD**, **REWE Markt GmbH**, **BAUHAUS AG**, **Globus Fachmärkte GmbH & Co. KG**, **Centershop Vertriebs GmbH** oder **Amazon.com, Inc.**.
* **Markenrechte:** Alle genannten Marken- und Firmennamen gehören den jeweiligen Inhabern und werden hier nur zur Beschreibung der Händler verwendet.
* **Faires Scraping:** Die Skripte arbeiten rein lesend, enthalten feste Abfragepausen zur Schonung der Server und führen keine automatisierten Käufe durch. Die Einhaltung der Nutzungsbedingungen und `robots.txt` liegt in der Verantwortung des Nutzers.
* **Lizenz:** Veröffentlicht unter der [MIT-Lizenz](LICENSE).
