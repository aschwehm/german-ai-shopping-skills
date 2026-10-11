#!/usr/bin/env python3
import sys
import argparse
import json
import time
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup

import os
STORE_ID = os.environ.get("BAUHAUS_STORE_ID", "616")
STORE_NAME = os.environ.get("BAUHAUS_STORE_NAME", "BAUHAUS Köln-Kalk")
BASE_URL = "https://www.bauhaus.info"

session = requests.Session(impersonate="chrome124")

def search_bauhaus(query, max_results=6):
    encoded = urllib.parse.quote(query)
    url = f"{BASE_URL}/suche/produkte?text={encoded}"
    resp = session.get(url)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code} beim Suchen auf Bauhaus.info"}
    
    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    
    for s in soup.find_all("script", type="application/ld+json"):
        if s.string and ('"@type":"ItemList"' in s.string or '"@type": "ItemList"' in s.string):
            try:
                data = json.loads(s.string)
                for entry in data.get("itemListElement", []):
                    prod = entry.get("item", {})
                    if prod and prod.get("name"):
                        price_raw = prod.get("offers", {}).get("price", 0)
                        try:
                            price_val = f"{float(price_raw):.2f} €"
                        except (ValueError, TypeError):
                            price_val = f"{price_raw} €"

                        rating_info = prod.get("aggregateRating", {})
                        items.append({
                            "name": prod.get("name"),
                            "sku": prod.get("sku"),
                            "price": price_val,
                            "rating": rating_info.get("ratingValue", "Keine"),
                            "reviews": rating_info.get("reviewCount", 0),
                            "url": prod.get("url"),
                            "image": prod.get("image")
                        })
                        if len(items) >= max_results:
                            break
            except Exception:
                pass
            if items:
                break

    return {"query": query, "total_found": len(items), "results": items}


def inspect_product(target):
    if target.startswith("http"):
        url = target
    else:
        url = f"{BASE_URL}/p/{target}"

    resp = session.get(url)
    if resp.status_code != 200:
        return {"url": url, "error": f"HTTP {resp.status_code} beim Laden der Produktdetails"}

    soup = BeautifulSoup(resp.text, "html.parser")
    prod = {}
    for s in soup.find_all("script", type="application/ld+json"):
        if s.string and ('"@type":"Product"' in s.string or '"@type": "Product"' in s.string):
            try:
                prod = json.loads(s.string)
                break
            except Exception:
                pass

    if not prod:
        return {"url": url, "error": "Produktdaten konnten nicht ausgelesen werden"}

    offers = prod.get("offers", {})
    price_val = 0.0
    try:
        price_val = float(offers.get("price", 0))
    except (ValueError, TypeError):
        pass

    shipping = offers.get("shippingDetails", {})
    shipping_rate = shipping.get("shippingRate", {}).get("value", "0.00")
    try:
        shipping_fee_float = float(shipping_rate)
    except (ValueError, TypeError):
        shipping_fee_float = 0.0

    transit = shipping.get("deliveryTime", {}).get("transitTime", {})
    min_days = transit.get("minValue")
    max_days = transit.get("maxValue")

    # Evaluation logic for local store availability
    is_freight = (min_days is not None and min_days >= 7) or shipping_fee_float > 30.0
    is_small_unfavorable = price_val < 30.0 and shipping_fee_float > 0.0

    if is_freight:
        fulfillment_type = "Bestellbar vor Ort / Spedition"
        status_text = "Großgerät / Sperrgut (Lieferzeit ca. 7–10 Werktage)"
        store_verdict = "Bestellung im Markt prüfen (sinnvoll falls Speditionsgebühren entfallen)"
        recommended = True
    elif is_small_unfavorable:
        fulfillment_type = "Online-Versand mit Aufpreis"
        status_text = f"Versandkosten {shipping_fee_float:.2f} € (unter 30 € Frei-Grenze)"
        store_verdict = "Nicht vor Ort / Uninteressant für Einzelkauf (andere Quelle nutzen)"
        recommended = False
    else:
        fulfillment_type = "Sofort abholbereit / Reguläre Lagerware"
        status_text = f"Lieferzeit 1–3 Werktage, versandkostenfrei ({shipping_fee_float:.2f} €)"
        store_verdict = "Sofort verfügbar im Markt (Reservieren & Abholen bevorzugt)"
        recommended = True

    return {
        "name": prod.get("name"),
        "sku": prod.get("sku"),
        "brand": prod.get("brand", {}).get("name", "BAUHAUS"),
        "price": f"{price_val:.2f} €",
        "shipping_fee": f"{shipping_fee_float:.2f} €",
        "delivery_time": f"{min_days}–{max_days} Werktage" if min_days else "1–3 Werktage",
        "fulfillment_type": fulfillment_type,
        "store_availability": {
            "store_id": STORE_ID,
            "store_name": STORE_NAME,
            "available_locally": recommended,
            "pickup_status": store_verdict
        },
        "store_status": status_text,
        "store_verdict": store_verdict,
        "recommended": recommended,
        "url": url,
        "image": prod.get("image") if isinstance(prod.get("image"), str) else (prod.get("image", [None])[0] if isinstance(prod.get("image"), list) else None),
        "description": (prod.get("description", "") or "")[:500]
    }


def batch_inspect(targets, delay_seconds=2.0):
    results = []
    for i, target in enumerate(targets):
        if i > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)
        results.append(inspect_product(target))
    return results


def main():
    parser = argparse.ArgumentParser(description="BAUHAUS Search & Product Inspector CLI")
    parser.add_argument("--query", "-q", help="Suchbegriff für Bauhaus.info")
    parser.add_argument("--url", "-u", help="Produktdetail-URL")
    parser.add_argument("--sku", "-s", help="Bauhaus Artikel-/Produktnummer")
    parser.add_argument("--batch", "-b", help="Komma-separierte Liste von URLs oder SKUs")
    parser.add_argument("--max", "-m", type=int, default=6, help="Maximale Anzahl Suchtreffer (Standard: 6)")
    parser.add_argument("--delay", type=float, default=2.0, help="Pause zwischen Abfragen in Sekunden")

    args = parser.parse_args()

    if args.query:
        res = search_bauhaus(args.query, args.max)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.url or args.sku:
        target = args.url or args.sku
        res = inspect_product(target)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.batch:
        targets = [t.strip() for t in args.batch.split(",") if t.strip()]
        res = batch_inspect(targets, args.delay)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
