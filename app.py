import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Genre
from datetime import datetime

# --- 1. CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api, genre_api = Discover(), Trending(), Genre()

# --- 2. PAGE SETUP & BACKGROUND ---
st.set_page_config(page_title="CinemaPro India", layout="wide", page_icon="🎬")

st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), 
                    url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070&auto=format&fit=crop");
        background-attachment: fixed;
        background-size: cover;
    }}
    .ott-link {{ background-color: #28a745; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
st.sidebar.title("👤 User Profile")
age = st.sidebar.number_input("Age", 1, 100, 18)
is_adult = age >= 18
media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en"}
sel_lang = st.sidebar.selectbox("Language", list(lang_map.keys()))

# --- 4. DATA HELPERS ---
def get_safe_val(item, key, default=None):
    if isinstance(item, dict): return item.get(key, default)
    return getattr(item, key, default)

def get_details(m_id, m_type):
    try:
        res = movie_api.details(m_id, append_to_response="videos,credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="videos,credits,watch/providers")
        # Extract Trailer
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in res.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), None)
        # Extract OTT
        providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
        ott_n = providers.get('flatrate', [{}])[0].get('provider_name', "Theaters/Rent")
        ott_l = providers.get('link', '#')
        # Extract Runtime
        if m_type == "Movies": rt = f"{res.get('runtime', 'N/A')} mins"
        else: rt = f"{res.get('episode_run_time', ['N/A'])[0]} mins/ep"
        return trailer, ott_n, ott_l, rt
    except: return None, "N/A", "#", "N/A"

# --- 5. TRENDING SECTION ---
st.title("🔥 Trending in India")
trending = trending_api.movie_day() if media_type == "Movies" else trending_api.tv_day()

t_cols = st.columns(6)
count = 0
for item in trending:
    if count >= 6: break
    # FIX: Safety check to ensure item is not a string
    if isinstance(item, str): continue 
    
    poster = get_safe_val(item, 'poster_path')
    if poster:
        with t_cols[count]:
            st.image(f"https://image.tmdb.org/t/p/w500{poster}")
            st.caption(get_safe_val(item, 'title', get_safe_val(item, 'name', '')))
            count += 1

st.divider()

# --- 6. EXPLORE SECTION ---
st.header("🎯 Explore Cinema")
query = st.text_input("🔍 Search by title...")

if st.button("Generate Recommendations") or query:
    results = []
    if query:
        results = movie_api.search(query) if media_type == "Movies" else tv_api.search(query)
    else:
        results = discover_api.discover_movies({'with_original_language': lang_map[sel_lang]}) if media_type == "Movies" else discover_api.discover_tv_shows({'with_original_language': lang_map[sel_lang]})

    if results:
        main_cols = st.columns(4)
        for i, item in enumerate(results[:20]):
            # Safety check
            if isinstance(item, str): continue
            
            poster = get_safe_val(item, 'poster_path')
            if poster:
                with main_cols[i % 4]:
                    st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                    st.subheader(get_safe_val(item, 'title', get_safe_val(item, 'name', '')))
                    with st.expander("Details"):
                        trailer, ott_n, ott_l, rt = get_details(get_safe_val(item, 'id'), media_type)
                        st.write(f"⏳ **Runtime:** {rt}")
                        st.write(get_safe_val(item, 'overview'))
                        if trailer: st.video(trailer)
                        if ott_l != "#": st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">Watch on {ott_n}</a>', unsafe_allow_html=True)
