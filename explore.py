import pandas as pd
import ast
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

movies = pd.read_csv("data/tmdb_5000_movies.csv")
credits = pd.read_csv("data/tmdb_5000_credits.csv")

movies = movies.merge(credits, on="title")
movies = movies[["movie_id", "title", "overview", "genres", "keywords", "cast", "crew"]].copy()
movies.dropna(inplace=True)

def get_names(text):
    names = []
    for item in ast.literal_eval(text):
        names.append(item["name"])
    return names

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

movies["tags"] = movies["overview"] + movies["genres"] + movies["keywords"] + movies["cast"] + movies["crew"]

final = movies[["movie_id", "title", "tags"]].copy()
final["tags"] = final["tags"].apply(lambda words: " ".join(words).lower())
final = final.reset_index(drop=True)   # line up the row numbers with the similarity grid

# ---- Combine Hollywood + Bollywood, then save ----
import pickle

bollywood = pickle.load(open("bollywood.pkl", "rb"))
combined = pd.concat([final, bollywood], ignore_index=True)
combined = combined.drop_duplicates(subset="title").reset_index(drop=True)

pickle.dump(combined, open("movies.pkl", "wb"))
print("Saved movies.pkl with", combined.shape[0], "movies (Hollywood + Bollywood)")

# ---- the recommend brain ----
def recommend(title):
    index = final[final["title"] == title].index[0]           # find the movie's row
    distances = sorted(list(enumerate(similarity[index])),    # closeness to every movie
                       key=lambda x: x[1], reverse=True)
    for i in distances[1:6]:                                   # skip itself, take next 5
        print(" -", final.iloc[i[0]]["title"])

print()
print("Because you liked Avatar, you might also like:")
recommend("Avatar")

import pickle
pickle.dump(final, open("movies.pkl", "wb"))
print("Saved movies.pkl ✅")