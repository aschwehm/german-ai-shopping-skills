#!/usr/bin/env python3
import sys
import argparse
import json
import time
import urllib.parse
import re
from curl_cffi import requests
from bs4 import BeautifulSoup
import os

BASE_URL = "https://www.globus-baumarkt.de"
STORE_PRIMARY_ID = os.environ.get("GLOBUS_PRIMARY_STORE_ID", "71")
STORE_PRIMARY_NAME = os.environ.get("GLOBUS_PRIMARY_STORE_NAME", "Brühl")
STORE_SECONDARY_ID = os.environ.get("GLOBUS_SECONDARY_STORE_ID", "78")
STORE_SECONDARY_NAME = os.environ.get("GLOBUS_SECONDARY_STORE_NAME", "Meerbusch")
DEFAULT_ZIP = os.environ.get("GLOBUS_ZIP", "50667")

session = requests.Session(impersonate="chrome124")
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL + "/"
}


def search_globus(query, max_results=6):
    encoded = urllib.parse.quote(query)
    url = f"{BASE_URL}/widgets/search?search={encoded}"
    resp = session.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code} beim Suchen auf globus-baumarkt.de"}

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.find_all("div", class_="product-box")
    if not cards:
        cards = soup.find_all("div", class_=lambda c: c and "product" in c and "box" in c)

    results = []
    for card in cards:
        a = card.find("a", href=lambda h: h and "/p/" in h)
        if not a:
            continue

        prod_url = a.get("href")
        if not prod_url.startswith("http"):
            prod_url = f"{BASE_URL}{prod_url}"

        title_el = card.find(class_=lambda c: c and ("title" in c.lower() or "name" in c.lower()))
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)

        price_el = card.find(class_=lambda c: c and "price" in c.lower())
        price = price_el.get_text(strip=True) if price_el else "Keine Angabe"

        sku_match = re.search(r"-(\d{10})/?$", prod_url)
        sku = sku_match.group(1) if sku_match else "N/A"

        img = card.find("img")
        img_url = img.get("src") or img.get("data-src") if img else None

        results.append({
            "name": title,
            "sku": sku,
            "price": price,
            "url": prod_url,
            "image": img_url
        })

        if len(results) >= max_results:
            break

    return {"query": query, "total_found": len(results), "results": results}


def get_store_availability(sku):
    if not sku or sku == "N/A":
        return STORE_PRIMARY_NAME, 0, STORE_SECONDARY_NAME, 0

    url = f"{BASE_URL}/ianeo/get-closest-stores-and-availability/{sku}/{DEFAULT_ZIP}"
    try:
        resp = session.get(url, headers=HEADERS)
        if resp.status_code != 200:
            return STORE_PRIMARY_NAME, 0, STORE_SECONDARY_NAME, 0
        data = resp.json().get("data", [])
        p_obj = None
        s_obj = None
        for s in data:
            s_id = str(s.get("id"))
            if s_id == str(STORE_PRIMARY_ID):
                p_obj = s
            elif s_id == str(STORE_SECONDARY_ID):
                s_obj = s

        if not p_obj and len(data) > 0:
            p_obj = data[0]
        if not s_obj and len(data) > 1:
            s_obj = data[1] if data[1] != p_obj else (data[2] if len(data) > 2 else None)

        p_name = (p_obj.get("name") or p_obj.get("city") or STORE_PRIMARY_NAME) if p_obj else STORE_PRIMARY_NAME
        p_stock = int(p_obj.get("stock", 0)) if p_obj else 0
        s_name = (s_obj.get("name") or s_obj.get("city") or STORE_SECONDARY_NAME) if s_obj else STORE_SECONDARY_NAME
        s_stock = int(s_obj.get("stock", 0)) if s_obj else 0

        return p_name, p_stock, s_name, s_stock
    except Exception:
        return STORE_PRIMARY_NAME, 0, STORE_SECONDARY_NAME, 0


def inspect_product(target):
    if target.startswith("http"):
        url = target
        sku_match = re.search(r"-(\d{10})/?$", url)
        sku = sku_match.group(1) if sku_match else None
    else:
        sku = target.strip()
        # Resolve canonical URL via search widget
        search_res = search_globus(sku, max_results=1)
        if search_res.get("results"):
            url = search_res["results"][0]["url"]
        else:
            url = f"{BASE_URL}/p/{sku}/"

    resp = session.get(url)
    if resp.status_code != 200:
        return {"url": url, "error": f"HTTP {resp.status_code} beim Laden der Produktdetails"}

    soup = BeautifulSoup(resp.text, "html.parser")
    prod_data = {}
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(s.string)
            if d.get("@type") == "Product":
                prod_data = d
                break
        except Exception:
            pass

    actual_sku = prod_data.get("sku") or sku
    offers = prod_data.get("offers", {})
    price_val = 0.0
    try:
        price_val = float(offers.get("price", 0))
    except (ValueError, TypeError):
        pass

    shipping = offers.get("shippingDetails", {})
    shipping_rate = 0.0
    try:
        shipping_rate = float(shipping.get("shippingRate", {}).get("value", 0))
    except (ValueError, TypeError):
        pass

    transit = shipping.get("deliveryTime", {}).get("transitTime", {})
    min_days = transit.get("minValue")
    max_days = transit.get("maxValue")

    # Live store stock evaluation (Primary store, Secondary store)
    p_name, primary_stock, s_name, secondary_stock = get_store_availability(actual_sku)

    if primary_stock > 0:
        fulfillment_type = f"Sofort abholbereit ({p_name})"
        status_text = f"{p_name}: {primary_stock} Stück auf Lager ({s_name}: {secondary_stock} Stück)"
        verdict = f"1. Wahl: In {p_name} reservieren & abholen"
        recommended = True
    elif secondary_stock > 0:
        fulfillment_type = f"Abholbereit ({s_name})"
        status_text = f"{p_name}: 0 Stück | {s_name}: {secondary_stock} Stück auf Lager"
        verdict = f"2. Wahl: In {s_name} abholen (in {p_name} nicht vorrätig)"
        recommended = True
    elif min_days and min_days >= 7:
        fulfillment_type = "Großgerät / Sperrgut"
        status_text = f"Lieferzeit ca. {min_days}–{max_days} Werktage (Spedition)"
        verdict = "Vor-Ort-Bestellung im Markt prüfen (falls Speditionsaufschlag entfällt)"
        recommended = True
    elif price_val < 30.0 and shipping_rate > 0.0:
        fulfillment_type = "Online-Versand mit Aufpreis"
        status_text = f"Nicht vor Ort verfügbar (Versandkosten: {shipping_rate:.2f} €)"
        verdict = "Nicht vor Ort / Uninteressant für Einzelkauf (andere Quelle nutzen)"
        recommended = False
    else:
        fulfillment_type = "Nur online lieferbar"
        status_text = f"Nicht vor Ort auf Lager (Lieferzeit: {min_days or 1}–{max_days or 3} Tage, Versand: {shipping_rate:.2f} €)"
        verdict = "Online bestellen oder Alternativen vergleichen"
        recommended = False

    img_val = prod_data.get("image")
    if isinstance(img_val, dict):
        image_url = img_val.get("url")
    elif isinstance(img_val, str):
        image_url = img_val
    elif isinstance(img_val, list) and img_val:
        image_url = img_val[0].get("url") if isinstance(img_val[0], dict) else img_val[0]
    else:
        image_url = None

    return {
        "name": prod_data.get("name"),
        "sku": actual_sku,
        "brand": prod_data.get("brand", {}).get("name") if isinstance(prod_data.get("brand"), dict) else "Globus Baumarkt",
        "price": f"{price_val:.2f} €",
        "primary_store": {
            "name": p_name,
            "stock_count": primary_stock,
            "available": primary_stock > 0
        },
        "secondary_store": {
            "name": s_name,
            "stock_count": secondary_stock,
            "available": secondary_stock > 0
        },
        "shipping_fee": f"{shipping_rate:.2f} €",
        "delivery_time": f"{min_days}–{max_days} Werktage" if min_days else "1–3 Werktage",
        "fulfillment_type": fulfillment_type,
        "availability_status": status_text,
        "verdict": verdict,
        "recommended": recommended,
        "url": url,
        "image": image_url,
        "description": (prod_data.get("description", "") or "")[:500]
    }


def batch_inspect(targets, delay_seconds=2.0):
    results = []
    for i, target in enumerate(targets):
        if i > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)
        results.append(inspect_product(target))
    return results


def main():
    parser = argparse.ArgumentParser(description="Globus Baumarkt Search & Product Inspector CLI")
    parser.add_argument("--query", "-q", help="Suchbegriff für globus-baumarkt.de")
    parser.add_argument("--url", "-u", help="Produktdetail-URL")
    parser.add_argument("--sku", "-s", help="Globus Artikel-/Produktnummer (10-stellig)")
    parser.add_argument("--batch", "-b", help="Komma-separierte Liste von URLs oder SKUs")
    parser.add_argument("--max", "-m", type=int, default=6, help="Maximale Anzahl Suchtreffer (Standard: 6)")
    parser.add_argument("--delay", type=float, default=2.0, help="Pause zwischen Abfragen in Sekunden")

    args = parser.parse_args()

    if args.query:
        res = search_globus(args.query, args.max)
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
