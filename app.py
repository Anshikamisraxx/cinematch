import pickle
import requests
import streamlit as st
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="CineMatch", page_icon="🎬", layout="wide")
st.title("🎬 CineMatch")
st.write("Pick a movie you like, and I'll suggest 5 similar ones — Hollywood & Bollywood.")

API_KEY = st.secrets["TMDB_API_KEY"]

@st.cache_data
def load():
    movies = pickle.load(open("movies.pkl", "rb"))
    cv = CountVectorizer(max_features=5000, stop_words="english")
    vectors = cv.fit_transform(movies["tags"]).toarray()
    similarity = cosine_similarity(vectors)
    return movies, similarity

movies, similarity = load()

@st.cache_data
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
    try:
        data = requests.get(url, timeout=10).json()
        path = data.get("poster_path")
        if path:
            return "https://image.tmdb.org/t/p/w500" + path
    except Exception:
        pass
    return None

def recommend(title):
    index = movies[movies["title"] == title].index[0]
    distances = sorted(list(enumerate(similarity[index])), key=lambda x: x[1], reverse=True)
    results = []
    for i in distances[1:6]:
        row = movies.iloc[i[0]]
        results.append((row["title"], row["movie_id"]))
    return results

selected = st.selectbox("Choose a movie:", movies["title"].values)

if st.button("Recommend"):
    st.subheader("You might also like:")
    recs = recommend(selected)
    cols = st.columns(5)
    for col, (name, movie_id) in zip(cols, recs):
        with col:
            poster = fetch_poster(movie_id)
            if poster:
                st.image(poster, width="stretch")
            st.caption(name)