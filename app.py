import streamlit as st
from tmdbv3api import TMDb, Movie, Discover
from datetime import datetime

# --- CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api = Movie()
discover_api = Discover()

# --- APP INTERFACE ---
st.set_page_config(page_title="Secure Cinema", layout="wide")
st.title("🛡️ Secure Movie Discovery")

# --- SIDEBAR FILTERS ---
st.sidebar.header("User Profile")
name = st.sidebar.text_input("Enter Name", "Guest")
age = st.sidebar.number_input("Enter Age", min_value=1, max_value=100, value=18)
is_adult = age >= 18

st.sidebar.divider()
media_type = st.sidebar.radio("Watch Type", ["Movies", "TV Shows"])
lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Kannada": "kn"}
sel_lang = st.sidebar.selectbox("Language", list(lang_map.keys()))
mood_map = {"Happy": 35, "Sad": 18, "Excited": 28, "Scared": 27, "Bored": 53}
mood = st.sidebar.selectbox("Mood", list(mood_map.keys()))

# --- DATA FETCHING ---
if st.sidebar.button("Show Recommendations"):
    today = datetime.now().strftime('%Y-%m-%d')
    results_pool = []
    
    # Fetch 5 pages to get 50 results
    for p in range(1, 6):
        params = {
            'with_genres': mood_map[mood],
            'with_original_language': lang_map[sel_lang],
            'page': p,
            'include_adult': is_adult,
            'primary_release_date.lte': today if media_type == "Movies" else None
        }
        
        data = discover_api.discover_movies(params) if media_type == "Movies" else discover_api.discover_tv_shows(params)
        results_pool.extend(data)

    # Strict Safety Filter for Minors
    final_list = []
    for m in results_pool:
        # Extra safety check: Block Horror(27) and Thriller(53) if under 18
        g_ids = getattr(m, 'genre_ids', [])
        if not is_adult and (27 in g_ids or 53 in g_ids):
            continue
        if m.poster_path: # Only show if it has a poster
            final_list.append(m)

    # Display Results in a Grid
    st.write(f"### Hello {name}, here are your top 50 recommendations:")
    
    cols = st.columns(5) # 5 posters per row
    for i, item in enumerate(final_list[:50]):
        with cols[i % 5]:
            poster_url = f"https://image.tmdb.org/t/p/w500{item.poster_path}"
            st.image(poster_url, caption=getattr(item, 'title', getattr(item, 'name', '')))
            with st.expander("View Plot"):
                st.write(item.overview)
                st.write(f"⭐ Rating: {item.vote_average}")
