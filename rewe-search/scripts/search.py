#!/usr/bin/env python3
import sys
import argparse
import json
import time
import urllib.parse
import re
from curl_cffi import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.rewe.de"
import os
DEFAULT_MARKET_ID = os.environ.get("REWE_MARKET_ID", "8100134")
DEFAULT_MARKET_NAME = os.environ.get("REWE_MARKET_NAME", "REWE Markt Köln Rudolfplatz")

session = requests.Session(impersonate="safari17_0")
HEADERS = {
    "Referer": "https://www.rewe.de/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
}


def fetch_market_offers(market_id=DEFAULT_MARKET_ID, filter_query=None):
    if market_id:
        url = f"{BASE_URL}/angebote/?market={market_id}"
    else:
        url = f"{BASE_URL}/angebote/"
    resp = session.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    offers = []
    seen = set()

    for el in soup.find_all(lambda tag: tag.name in ["div", "article", "li"] and "€" in tag.get_text()):
        text = el.get_text(" | ", strip=True)
        if not (15 < len(text) < 150):
            continue

        price_match = re.search(r"(\d+[\.,]\d{2}\s*€)", text)
        if not price_match:
            continue
        price = price_match.group(1)

        parts = [p.strip() for p in text.split(" | ") if p.strip()]
        # Product title is usually the first part
        title = parts[0]
        if title in ["Aktion", "App", "Rabatt"] and len(parts) > 1:
            title = parts[1]

        if filter_query and filter_query.lower() not in text.lower():
            continue

        key = f"{title}_{price}"
        if key in seen:
            continue
        seen.add(key)

        offers.append({
            "name": title,
            "price": price,
            "type": "Wochenangebot / Aktion",
            "market_id": market_id,
            "availability": "Vorrätig (Aktuelles Prospektangebot)",
            "url": url
        })

    return offers


def search_rewe_shop(query, market_id=DEFAULT_MARKET_ID, max_results=8):
    encoded = urllib.parse.quote(query)
    url = f"https://shop.rewe.de/productList?search={encoded}&wwIdent={market_id}"
    resp = session.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code} beim Laden von shop.rewe.de"}

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    links = soup.find_all("a", href=lambda h: h and "/shop/p/" in h)

    seen = set()
    for a in links:
        title = a.get_text(strip=True)
        if not title or title in seen:
            continue
        seen.add(title)

        href = a.get("href")
        card = a
        for _ in range(4):
            if card.parent:
                card = card.parent

        card_text = card.get_text(" | ", strip=True)
        price_match = re.search(r"(\d+[\.,]\d{2}\s*€)", card_text)
        price = price_match.group(1) if price_match else "Sortimentspreis im Markt"

        # Check availability text
        if "nicht vorrätig" in card_text.lower():
            avail = "Nicht vorrätig"
            status = "Im Markt derzeit vergriffen"
        elif "meist vorrätig" in card_text.lower():
            avail = "Meist vorrätig"
            status = "Sehr wahrscheinlich im Markt verfügbar"
        else:
            avail = "Vorrätig"
            status = "Im Markt gelistet"

        full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
        results.append({
            "name": title,
            "price": price,
            "availability": avail,
            "status": status,
            "market_id": market_id,
            "url": full_url
        })

        if len(results) >= max_results:
            break

    return results


def search_rewe(query=None, offers_only=False, market_id=DEFAULT_MARKET_ID, max_results=8):
    offers = fetch_market_offers(market_id, filter_query=query)

    if offers_only or not query:
        return {
            "market_id": market_id,
            "query": query,
            "total_found": len(offers[:max_results]),
            "results": offers[:max_results]
        }

    # If query provided, search shop and combine with matched offers
    shop_results = search_rewe_shop(query, market_id, max_results)
    combined = offers + (shop_results if isinstance(shop_results, list) else [])

    return {
        "market_id": market_id,
        "query": query,
        "total_found": len(combined[:max_results]),
        "results": combined[:max_results]
    }


def main():
    parser = argparse.ArgumentParser(description="REWE Search & Market Offers CLI")
    parser.add_argument("--query", "-q", help="Suchbegriff für REWE Sortiment oder Angebote")
    parser.add_argument("--offers", "-o", action="store_true", help="Nur aktuelle Wochenangebote des Markts anzeigen")
    parser.add_argument("--market", "-m", default=DEFAULT_MARKET_ID, help=f"REWE Markt-ID / wwIdent (Standard: {DEFAULT_MARKET_ID} / REWE_MARKET_ID)")
    parser.add_argument("--max", type=int, default=8, help="Maximale Trefferanzahl (Standard: 8)")
    parser.add_argument("--delay", type=float, default=1.5, help="Pause zwischen Abfragen in Sekunden")

    args = parser.parse_args()

    res = search_rewe(
        query=args.query,
        offers_only=args.offers,
        market_id=args.market,
        max_results=args.max
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
