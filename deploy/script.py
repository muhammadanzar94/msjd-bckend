"""
Find UK mosques/masjids with a phone number but no website, export to Excel.
Sorted by distance from Bolton, UK.

Usage:
    export GOOGLE_MAPS_API_KEY=""
    python deploy/script.py --output mosques_no_website.xlsx
"""

import os
import time
import argparse
import requests
import pandas as pd
from geopy.distance import geodesic

PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

BOLTON_COORDS = (53.5769, -2.4282)

# Bounding box roughly covering mainland UK (lat_min, lat_max, lon_min, lon_max)
# UK_BOUNDS = (49.9, 58.7, -6.5, 1.8)
# UK_BOUNDS = (53.30, 53.65, -2.75, -1.90)  # greater manchester

SEARCH_RADIUS_M = 20000   # 20km per grid cell
GRID_STEP_DEG = 0.35      # ~35-40km spacing between grid points


def build_grid(bounds, step):
    lat_min, lat_max, lon_min, lon_max = bounds
    points = []
    lat = lat_min
    while lat <= lat_max:
        lon = lon_min
        while lon <= lon_max:
            points.append((round(lat, 4), round(lon, 4)))
            lon += step
        lat += step
    return points


def nearby_search(api_key, lat, lon, radius, session, place_type=None, keyword=None):
    params = {
        "location": f"{lat},{lon}",
        "radius": radius,
        "key": api_key,
    }
    if place_type:
        params["type"] = place_type
    if keyword:
        params["keyword"] = keyword

    place_ids = set()
    while True:
        resp = session.get(PLACES_NEARBY_URL, params=params, timeout=15)
        data = resp.json()
        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            print(f"  [warn] nearby_search status={status} at ({lat},{lon}): {data.get('error_message', '')}")
            break
        for result in data.get("results", []):
            place_ids.add(result["place_id"])
        next_token = data.get("next_page_token")
        if not next_token:
            break
        time.sleep(2)
        params = {"pagetoken": next_token, "key": api_key}
    return place_ids

def get_place_details(api_key, place_id, session):
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,international_phone_number,"
                   "website,geometry,address_components,url",   # fixed: plural
        "key": api_key,
    }
    resp = session.get(PLACES_DETAILS_URL, params=params, timeout=15)
    data = resp.json()
    if data.get("status") != "OK":
        print(f"  [warn] details status={data.get('status')} for {place_id}: {data.get('error_message', '')}")
        return None
    return data.get("result")


def extract_address_component(components, target_types):
    for comp in components or []:
        if any(t in comp["types"] for t in target_types):
            return comp["long_name"]
    return ""

SEARCH_KEYWORDS = ["masjid", "mosque"]


def collect_place_ids(api_key):
    session = requests.Session()
    grid = build_grid(UK_BOUNDS, GRID_STEP_DEG)
    print(f"Scanning {len(grid)} grid points across the UK...")
    all_ids = set()
    for i, (lat, lon) in enumerate(grid, 1):
        found = nearby_search(api_key, lat, lon, SEARCH_RADIUS_M, session, place_type="mosque")
        for kw in SEARCH_KEYWORDS:
            found |= nearby_search(api_key, lat, lon, SEARCH_RADIUS_M, session, keyword=kw)

        all_ids.update(found)
        print(f"  [{i}/{len(grid)}] ({lat},{lon}) -> {len(found)} results this point, "
              f"total unique so far: {len(all_ids)}")
        time.sleep(0.2)
    return all_ids

def build_rows(api_key, place_ids):
    session = requests.Session()
    rows = []
    total = len(place_ids)
    for i, place_id in enumerate(place_ids, 1):
        details = get_place_details(api_key, place_id, session)
        time.sleep(0.05)
        if not details:
            continue

        website = details.get("website", "").strip()
        phone = details.get("formatted_phone_number") or details.get("international_phone_number") or ""
        phone = phone.strip()

        # Keep all mosques with no website, regardless of whether a phone number exists
        if website:
            continue

        components = details.get("address_components", [])
        postcode = extract_address_component(components, ["postal_code"])
        city = extract_address_component(components, ["postal_town", "locality"])

        lat = details.get("geometry", {}).get("location", {}).get("lat")
        lng = details.get("geometry", {}).get("location", {}).get("lng")
        distance_km = None
        if lat is not None and lng is not None:
            distance_km = round(geodesic(BOLTON_COORDS, (lat, lng)).km, 2)

        gmaps_link = details.get("url") or (
            f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        )

        rows.append({
            "Name": details.get("name", ""),
            "Address": details.get("formatted_address", ""),
            "Postcode": postcode,
            "City": city,
            "Google Maps Link": gmaps_link,
            "Phone Number": phone,  # blank if Google has none listed
            "Website": website,     # always blank here since we filtered on no-website
            "Distance from Bolton (km)": distance_km,
        })

        if i % 20 == 0:
            print(f"  [{i}/{total}] processed, {len(rows)} matches so far")

    return rows

def main():
    parser = argparse.ArgumentParser(description="Find UK mosques with phone but no website.")
    parser.add_argument("--api-key", default=os.environ.get("GOOGLE_MAPS_API_KEY"),
                         help="Google Maps API key (or set GOOGLE_MAPS_API_KEY env var)")
    parser.add_argument("--output", default="mosques_no_website.xlsx", help="Output Excel file path")
    parser.add_argument("--sort-by-distance", action="store_true", default=True,
                         help="Sort results by distance from Bolton (default: on)")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("No API key provided. Use --api-key or set GOOGLE_MAPS_API_KEY.")

    place_ids = collect_place_ids(args.api_key)
    print(f"\nFound {len(place_ids)} unique mosque place IDs. Fetching details...")

    rows = build_rows(args.api_key, place_ids)
    print(f"\n{len(rows)} mosques matched (have phone, no website).")

    df = pd.DataFrame(rows)
    if args.sort_by_distance and not df.empty:
        df = df.sort_values("Distance from Bolton (km)", na_position="last")

    df.to_excel(args.output, index=False, engine="openpyxl")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()