#!/usr/bin/env python3
import sys
import argparse
import json
import time
import urllib.parse
import re
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.centershop.de"
session = requests.Session(impersonate="chrome124", verify=False)


def get_current_prospekt():
    url = f"{BASE_URL}/prospekt/"
    resp = session.get(url)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code} beim Laden von {url}"}

    soup = BeautifulSoup(resp.text, "html.parser")
    pdf_links = [a.get("href") for a in soup.find_all("a", href=True) if a.get("href").endswith(".pdf")]
    pdf_url = pdf_links[0] if pdf_links else None

    # Extract date banner
    dates = []
    for el in soup.find_all(["p", "h1", "h2", "h3", "span", "div"]):
        txt = el.get_text(strip=True)
        if any(k in txt.lower() for k in ["oktober", "november", "dezember", "januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september"]) and ("bis" in txt or "kw" in txt.lower()):
            if 5 < len(txt) < 60 and txt not in dates:
                dates.append(txt)

    validity = dates[0] if dates else "Aktuelle Woche"

    return {
        "title": "Aktueller CenterShop Wochenprospekt",
        "validity": validity,
        "pdf_url": pdf_url,
        "prospekt_page": url,
        "note": "Filialen führen alle regulären Werbepreise und Prospektartikel."
    }


def search_centershop_products(query=None, category=None, max_results=8):
    results = []

    if category:
        cat_url = f"{BASE_URL}/{category}/"
        resp = session.get(cat_url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=lambda h: h and "/produkt/" in h):
                href = a.get("href")
                title = a.get_text(strip=True)
                if not title:
                    slug = href.strip("/").split("/")[-1].replace("-", " ").title()
                    title = slug

                if query and query.lower() not in title.lower():
                    continue

                if not any(r["url"] == href for r in results):
                    results.append({
                        "name": title,
                        "category": category,
                        "url": href,
                        "status": "In Filiale verfügbar (Baumarkt-/Saisonsortiment)"
                    })
                if len(results) >= max_results:
                    break
    elif query:
        encoded = urllib.parse.quote(query)
        search_url = f"{BASE_URL}/?s={encoded}"
        resp = session.get(search_url)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=lambda h: h and "/produkt/" in h):
                href = a.get("href")
                title = a.get_text(strip=True)
                if not title:
                    slug = href.strip("/").split("/")[-1].replace("-", " ").title()
                    title = slug

                if not any(r["url"] == href for r in results):
                    results.append({
                        "name": title,
                        "url": href,
                        "status": "Filialartikel (Vor Ort in Filiale)"
                    })
                if len(results) >= max_results:
                    break

    return {
        "query": query,
        "category": category,
        "total_found": len(results),
        "results": results[:max_results]
    }


def inspect_product(url):
    resp = session.get(url)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code} für {url}"}

    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("h1")
    title_text = title.get_text(strip=True) if title else "CenterShop Produkt"

    # Check for in-store notice
    in_store_only = "nur in den filialen" in resp.text.lower()
    is_orderable = "bestellartikel" in resp.text.lower()

    if in_store_only:
        availability = "Nur in den Filialen erhältlich (Vor Ort in der Filiale kaufen)"
    elif is_orderable:
        availability = "Bestellartikel (Online oder im Markt bestellbar)"
    else:
        availability = "In Filiale erhältlich"

    return {
        "name": title_text,
        "availability": availability,
        "in_store_only": in_store_only,
        "url": url,
        "description": soup.find(class_="entry-content").get_text(" ", strip=True)[:400] if soup.find(class_="entry-content") else ""
    }


def main():
    parser = argparse.ArgumentParser(description="CenterShop Prospekt & Product Inspector CLI")
    parser.add_argument("--prospekt", "-p", action="store_true", help="Aktuellen Wochenprospekt mit PDF-Link & Gültigkeit abrufen")
    parser.add_argument("--query", "-q", help="Suchbegriff für CenterShop Sortiment")
    parser.add_argument("--category", "-c", help="Kategorie durchsuchen (z. B. baumarkt, garten, haushalt)")
    parser.add_argument("--url", "-u", help="Produktdetail-URL prüfen")
    parser.add_argument("--max", "-m", type=int, default=8, help="Maximale Trefferanzahl (Standard: 8)")
    parser.add_argument("--delay", type=float, default=1.5, help="Pause zwischen Abfragen in Sekunden")

    args = parser.parse_args()

    if args.prospekt:
        print(json.dumps(get_current_prospekt(), indent=2, ensure_ascii=False))
    elif args.url:
        print(json.dumps(inspect_product(args.url), indent=2, ensure_ascii=False))
    elif args.query or args.category:
        print(json.dumps(search_centershop_products(args.query, args.category, args.max), indent=2, ensure_ascii=False))
    else:
        # Default: Prospekt anzeigen
        print(json.dumps(get_current_prospekt(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
