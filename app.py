import pickle
from datetime import datetime

import requests
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="CineMatch", page_icon="🎬", layout="wide")

st.title("🎬 CineMatch")
st.write("Pick a movie you like, and I'll suggest 5 similar ones — Hollywood, Bollywood & Tollywood.")

API_KEY = st.secrets["TMDB_API_KEY"]

@st.cache_resource
def load():
    movies = pickle.load(open("movies.pkl", "rb"))
    cv = CountVectorizer(max_features=5000, stop_words="english")
    vectors = cv.fit_transform(movies["tags"])   # keep sparse — uses very little memory
    return movies, vectors

movies, vectors = load()
st.caption(f"Searching across {len(movies):,} movies 🍿")

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

def rating_label(v):
    return f"⭐ {v:.1f}/10" if v and v > 0 else "⭐ Not rated"

def recommend(title):
    index = movies[movies["title"] == title].index[0]
    # similarity of just the picked movie against all movies (1 row, not a full grid)
    sims = cosine_similarity(vectors[index], vectors).flatten()
    order = sims.argsort()[::-1]
    results = []
    for i in order[1:6]:
        row = movies.iloc[int(i)]
        results.append((row["title"], row["movie_id"], row["vote_average"]))
    return results

# ---- Google Sheet connection for feedback ----
@st.cache_resource
def get_feedback_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["sheet_id"]).sheet1

# ---- Recommender UI ----
selected = st.selectbox("Choose a movie:", movies["title"].values)
selected_rating = movies[movies["title"] == selected]["vote_average"].values[0]
st.caption(rating_label(selected_rating))

if st.button("Recommend", type="primary"):
    with st.spinner("Finding movies you'll love..."):
        recs = recommend(selected)
    st.subheader("You might also like:")
    cols = st.columns(5)
    for col, (name, movie_id, rating) in zip(cols, recs):
        with col:
            poster = fetch_poster(movie_id)
            if poster:
                st.image(poster, width="stretch")
            st.caption(name)
            st.caption(rating_label(rating))

# ---- Feedback block (visible to every visitor) ----
st.markdown("---")
st.subheader("💬 Enjoying CineMatch? Leave feedback")
with st.form("feedback_form", clear_on_submit=True):
    fb_rating = st.slider("Rate your experience", 1, 5, 4)
    fb_comment = st.text_area(
        "Comments or suggestions (optional)",
        placeholder="What did you like? What could be better?",
    )
    submitted = st.form_submit_button("Submit feedback")
    if submitted:
        try:
            sheet = get_feedback_sheet()
            sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                fb_rating,
                fb_comment,
            ])
            st.success("Thanks for your feedback! 🎉")
        except Exception as e:
            st.error(f"Save failed: {e}")

with st.expander("ℹ️ How does CineMatch work?"):
    st.write(
        "Each movie is turned into a 'fingerprint' from its genres, keywords, top cast, "
        "director, and story summary. Those are converted into numbers and compared using "
        "cosine similarity — the 5 closest movies become your recommendations, across "
        "Hollywood, Bollywood, and Tollywood."
    )

st.markdown("---")
st.caption("Built by Anshika Misra · Data & posters from TMDB")