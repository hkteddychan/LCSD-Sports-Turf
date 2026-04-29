#!/usr/bin/env python3
"""Fetch LCSD turf soccer pitch booking data and save as GeoJSON."""
import urllib.request, json, sys

url = "https://data.smartplay.lcsd.gov.hk/rest/cms/api/v1/publ/contents/open-data/turf-soccer-pitch/file"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
print(f"Fetching {url}", file=sys.stderr)
with urllib.request.urlopen(req, timeout=60) as r:
    records = json.loads(r.read())

print(f"Got {len(records)} raw records", file=sys.stderr)

# Skip records without coordinates
valid = [r for r in records if r.get("Venue_Latitude") and r.get("Venue_Longitude")]
print(f"Records with coordinates: {len(valid)}", file=sys.stderr)

# Group by venue + facility
venues = {}
for r in valid:
    vid = r["Venue_Name_TC"]
    if vid not in venues:
        venues[vid] = {
            "name_tc": r["Venue_Name_TC"],
            "name_en": r["Venue_Name_EN"],
            "address": r["Venue_Address_TC"],
            "district": r["District_Name_TC"],
            "phone": r["Venue_Phone_No."],
            "lat": float(r["Venue_Latitude"]),
            "lng": float(r["Venue_Longitude"]),
            "facilities": {}
        }
    fac = r["Facility_Type_Name_TC"]
    if fac not in venues[vid]["facilities"]:
        venues[vid]["facilities"][fac] = {
            "sessions": [],
            "coords": [float(r["Venue_Latitude"]), float(r["Venue_Longitude"])]
        }
    date = r["Available_Date"]
    sessions = venues[vid]["facilities"][fac].setdefault("dates", {})
    sessions.setdefault(date, []).append([
        r["Session_Start_Time"],
        r["Session_End_Time"],
        int(r["Available_Courts"])
    ])

# Build GeoJSON
features = []
for v in venues.values():
    for fac, facdata in v["facilities"].items():
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [facdata["coords"][1], facdata["coords"][0]]},
            "properties": {
                "name_tc": v["name_tc"],
                "name_en": v["name_en"],
                "address": v["address"],
                "district": v["district"],
                "facility": fac,
                "phone": v["phone"],
                "dates": facdata.get("dates", {})
            }
        })

geojson = {"type": "FeatureCollection", "features": features}
with open("turf_data.json", "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False)
print(f"Written {len(features)} features to turf_data.json", file=sys.stderr)
