import requests
import pandas as pd
import pickle
import time

API_KEY = "PASTE_YOUR_KEY_HERE"        # <-- paste your TMDB v3 key between the quotes    # <-- paste your TMDB v3 key between the quotes
BASE = "https://api.themoviedb.org/3"
PAGES = 100                            # 20 movies per page -> ~2000 movies. Raise for more.

def get_json(url, params):
    params["api_key"] = API_KEY
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

# 1) Collect popular Hindi (Bollywood) movie IDs
movie_ids = []
for page in range(1, PAGES + 1):
    data = get_json(f"{BASE}/discover/movie", {
        "with_original_language": "hi",
        "sort_by": "popularity.desc",
        "page": page,
    })
    for m in data.get("results", []):
        movie_ids.append(m["id"])
    print(f"Collected page {page}/{PAGES} — {len(movie_ids)} movies so far")
    time.sleep(0.05)

movie_ids = list(set(movie_ids))       # remove duplicates
print("Unique Bollywood movies to fetch:", len(movie_ids))

# small helpers (same fingerprint idea as Hollywood)
def names(items):     return [i["name"] for i in items]
def top_cast(items):  return [i["name"] for i in items[:3]]
def director(items):
    for i in items:
        if i.get("job") == "Director":
            return [i["name"]]
    return []
def squash(words):    return [w.replace(" ", "") for w in words]

# 2) For each movie, fetch full details and build its tags
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
    })
    if n % 100 == 0:
        pd.DataFrame(rows).to_pickle("bollywood.pkl")     # save progress every 100
        print(f"Processed {n}/{len(movie_ids)} — saved {len(rows)} movies so far")
    time.sleep(0.02)

pd.DataFrame(rows).to_pickle("bollywood.pkl")
print("Saved bollywood.pkl with", len(rows), "Bollywood movies")