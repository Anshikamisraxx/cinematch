import requests
import pandas as pd
import time
import datetime

import tomllib   # reads .toml files; built into Python 3.11+

# Read the key from the same secrets file your app uses (git-ignored, never committed)
with open(".streamlit/secrets.toml", "rb") as f:
    API_KEY = tomllib.load(f)["TMDB_API_KEY"]

BASE = "https://api.themoviedb.org/3"

LANGUAGES = ["hi", "te"]               # hi = Hindi (Bollywood), te = Telugu (Tollywood)
POPULAR_PAGES = 100                    # popular movies per language (20 per page -> ~2000)
RECENT_PAGES  = 25                     # newest releases per language (~500)

def get_json(url, params):
    params["api_key"] = API_KEY
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

# 1) Collect movie IDs: popular + recent, for each language
today = datetime.date.today().isoformat()
movie_ids = set()                      # a set auto-removes duplicates

for lang in LANGUAGES:
    # 1a) popular
    for page in range(1, POPULAR_PAGES + 1):
        data = get_json(f"{BASE}/discover/movie", {
            "with_original_language": lang,
            "sort_by": "popularity.desc",
            "page": page,
        })
        for m in data.get("results", []):
            movie_ids.add(m["id"])
        time.sleep(0.05)
    print(f"[{lang}] popular done — {len(movie_ids)} unique IDs so far")

    # 1b) recent releases (newest first, skip unreleased / unrated junk)
    for page in range(1, RECENT_PAGES + 1):
        data = get_json(f"{BASE}/discover/movie", {
            "with_original_language": lang,
            "sort_by": "primary_release_date.desc",
            "primary_release_date.lte": today,   # only already-released
            "vote_count.gte": 5,                 # skip movies with almost no ratings
            "page": page,
        })
        for m in data.get("results", []):
            movie_ids.add(m["id"])
        time.sleep(0.05)
    print(f"[{lang}] recent done — {len(movie_ids)} unique IDs so far")

movie_ids = list(movie_ids)
print("Total unique Indian movies to fetch:", len(movie_ids))

# small helpers (same fingerprint idea as Hollywood)
def names(items):     return [i["name"] for i in items]
def top_cast(items):  return [i["name"] for i in items[:3]]
def director(items):
    for i in items:
        if i.get("job") == "Director":
            return [i["name"]]
    return []
def squash(words):    return [w.replace(" ", "") for w in words]

# 2) For each movie, fetch full details and build its tags (saving progress as we go)
rows = []
for n, mid in enumerate(movie_ids, 1):
    try:
        d = get_json(f"{BASE}/movie/{mid}", {"append_to_response": "credits,keywords"})
    except Exception:
        continue
    overview = (d.get("overview") or "").split()
    genres   = squash(names(d.get("genres", [])))
    keywords = squash(names(d.get("keywords", {}).get("keywords", [])))
    cast     = squash(top_cast(d.get("credits", {}).get("cast", [])))
    crew     = squash(director(d.get("credits", {}).get("crew", [])))
    tags = overview + genres + keywords + cast + crew
    if not tags:
        continue
    rows.append({
        "movie_id": d["id"],
        "title": d.get("title") or d.get("original_title"),
        "tags": " ".join(tags).lower(),
        "vote_average": d.get("vote_average", 0.0),   # NEW: the /10 rating
    })
    if n % 100 == 0:
        pd.DataFrame(rows).to_pickle("indian.pkl")     # save progress every 100
        print(f"Processed {n}/{len(movie_ids)} — saved {len(rows)} movies so far")
    time.sleep(0.02)

pd.DataFrame(rows).to_pickle("indian.pkl")
print("Saved indian.pkl with", len(rows), "movies (Hindi + Telugu)")