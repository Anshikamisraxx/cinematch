# 🎬 CineMatch — Movie Recommender (Hollywood + Bollywood)

A content-based movie recommendation web app. Pick a movie you like and get 5 similar ones — with posters — across both Hollywood and Bollywood.

**Live demo:** _coming soon_

## How it works
Each movie is turned into a "fingerprint" from its genres, keywords, top cast, director, and story summary. That text is vectorized with `CountVectorizer` and movies are compared using cosine similarity. The 5 closest are recommended.

## Features
- Content-based recommendations across ~6,700 Hollywood + Bollywood movies
- Live movie posters via the TMDB API
- Clean Streamlit web interface

## Tech stack
Python · pandas · scikit-learn · Streamlit · TMDB API

## Run locally
1. `pip install -r requirements.txt`
2. Add your TMDB key to `.streamlit/secrets.toml` as `TMDB_API_KEY`
3. `streamlit run app.py`

## Data
Hollywood: TMDB 5000 Movie Dataset. Bollywood: fetched live from the TMDB API.