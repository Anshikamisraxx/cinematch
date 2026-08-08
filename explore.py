import pandas as pd
import ast
import pickle

movies = pd.read_csv("data/tmdb_5000_movies.csv")
credits = pd.read_csv("data/tmdb_5000_credits.csv")

movies = movies.merge(credits, on="title")
# NEW: keep vote_average (the /10 rating) on the Hollywood side too
movies = movies[["movie_id", "title", "overview", "genres",
                 "keywords", "cast", "crew", "vote_average"]].copy()
movies.dropna(inplace=True)

def get_names(text):
    return [item["name"] for item in ast.literal_eval(text)]

def get_top_cast(text):
    names = []
    for item in ast.literal_eval(text):
        if len(names) < 3:
            names.append(item["name"])
    return names

def get_director(text):
    for item in ast.literal_eval(text):
        if item["job"] == "Director":
            return [item["name"]]
    return []

movies["genres"]   = movies["genres"].apply(get_names)
movies["keywords"] = movies["keywords"].apply(get_names)
movies["cast"]     = movies["cast"].apply(get_top_cast)
movies["crew"]     = movies["crew"].apply(get_director)
movies["overview"] = movies["overview"].apply(lambda x: x.split())

def remove_spaces(word_list):
    return [word.replace(" ", "") for word in word_list]

for col in ["genres", "keywords", "cast", "crew"]:
    movies[col] = movies[col].apply(remove_spaces)

movies["tags"] = (movies["overview"] + movies["genres"] +
                  movies["keywords"] + movies["cast"] + movies["crew"])

final = movies[["movie_id", "title", "tags", "vote_average"]].copy()
final["tags"] = final["tags"].apply(lambda words: " ".join(words).lower())

# ---- Combine Hollywood + Indian (Hindi + Telugu), then save ONCE ----
indian = pickle.load(open("indian.pkl", "rb"))
combined = pd.concat([final, indian], ignore_index=True)
combined = combined.drop_duplicates(subset="title").reset_index(drop=True)

pickle.dump(combined, open("movies.pkl", "wb"))
print("Saved movies.pkl with", combined.shape[0], "movies (Hollywood + Hindi + Telugu)")
print("Columns:", list(combined.columns))