#!/usr/bin/env python3
import sys
import argparse
import json
import time
import urllib.parse
import re
from datetime import datetime, timedelta
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.aldi-sued.de"
import os
DEFAULT_ZIP = os.environ.get("ALDI_ZIP", "50667")

session = requests.Session(impersonate="chrome124")


def get_available_offer_dates():
    resp = session.get(f"{BASE_URL}/angebote")
    if resp.status_code != 200:
        return []
    dates = []
    for a in BeautifulSoup(resp.text, "html.parser").find_all("a", href=True):
        m = re.search(r"/angebote/(\d{4}-\d{2}-\d{2})", a.get("href"))
        if m and m.group(1) not in dates:
            dates.append(m.group(1))
    return sorted(dates)


def fetch_offers_for_date(date_str, filter_query=None):
    url = f"{BASE_URL}/angebote/{date_str}"
    resp = session.get(url)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    products = []
    seen = set()

    for el in soup.find_all(lambda tag: tag.name in ["div", "article", "li"] and any("product" in c.lower() for c in tag.get("class", []))):
        text = el.get_text(" | ", strip=True)
        if "€" not in text:
            continue

        parts = [p.strip() for p in text.split(" | ") if p.strip() and p.strip() != "¹"]
        if len(parts) < 2:
            continue

        # Look for price
        price_match = re.search(r"(\d+[\.,]\d{2}\s*€)", text)
        if not price_match:
            continue
        price = price_match.group(1)

        # Look for availability
        avail_match = re.search(r"(Verfügbar ab \d{2}\.\d{2}\.\d{4}|Verfügbar seit \d{2}\.\d{2}\.\d{4}|Ab [A-Za-z]+, \d+.*)", text)
        avail = avail_match.group(1) if avail_match else f"Gültig ab {date_str}"

        # Extract title and brand
        # Usually format: "Verfügbar ab ... | BRAND | TITLE | PRICE"
        clean_parts = [p for p in parts if not re.search(r"(\d+[\.,]\d{2}\s*€|Verfügbar|Gültig)", p)]
        if not clean_parts:
            continue

        brand = clean_parts[0] if len(clean_parts) > 1 else "ALDI SÜD"
        title = clean_parts[1] if len(clean_parts) > 1 else clean_parts[0]

        link_el = el.find("a", href=True)
        link = f"{BASE_URL}{link_el.get('href')}" if link_el and link_el.get("href").startswith("/") else (link_el.get("href") if link_el else url)

        key = f"{title}_{price}"
        if key in seen:
            continue
        seen.add(key)

        if filter_query and filter_query.lower() not in title.lower() and filter_query.lower() not in brand.lower():
            continue

        products.append({
            "name": title,
            "brand": brand,
            "price": price,
            "availability": avail,
            "offer_date": date_str,
            "url": link
        })

    return products


def get_next_thursday():
    today = datetime.now()
    days_ahead = 3 - today.weekday()  # Thursday is 3
    if days_ahead <= 0:
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def search_aldi(query=None, thursday_only=False, max_results=8, zip_code=DEFAULT_ZIP):
    dates = get_available_offer_dates()
    results = []

    if thursday_only:
        # Match dates on Thursdays or next Thursday
        thursday_dates = [d for d in dates if datetime.strptime(d, "%Y-%m-%d").weekday() == 3]
        target_dates = thursday_dates if thursday_dates else dates[:2]
    else:
        target_dates = dates

    for d in target_dates:
        time.sleep(0.5)
        day_prods = fetch_offers_for_date(d, filter_query=query)
        results.extend(day_prods)
        if len(results) >= max_results:
            break

    return {
        "store_zip": zip_code,
        "query": query,
        "thursday_filtered": thursday_only,
        "total_found": len(results[:max_results]),
        "results": results[:max_results]
    }


def main():
    parser = argparse.ArgumentParser(description="ALDI SÜD Search & Special Offers CLI")
    parser.add_argument("--query", "-q", help="Suchbegriff für ALDI SÜD Sortiment/Angebote")
    parser.add_argument("--thursday", "-t", action="store_true", help="Nur Aktionen für Donnerstag anzeigen")
    parser.add_argument("--angebote", "-a", action="store_true", help="Alle aktuellen Wochenangebote abrufen")
    parser.add_argument("--zip", "-z", default=DEFAULT_ZIP, help="Filial-Postleitzahl (Standard: 50667 Köln / ALDI_ZIP)")
    parser.add_argument("--max", "-m", type=int, default=8, help="Maximale Trefferanzahl (Standard: 8)")
    parser.add_argument("--delay", type=float, default=1.5, help="Pause zwischen Abfragen in Sekunden")

    args = parser.parse_args()

    res = search_aldi(
        query=args.query,
        thursday_only=args.thursday,
        max_results=args.max,
        zip_code=args.zip
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
