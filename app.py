import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Genre
from datetime import datetime

# --- 1. CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api, genre_api = Discover(), Trending(), Genre()

# --- 2. PAGE SETUP & CINEMATIC BACKGROUND ---
st.set_page_config(page_title="CinemaPro India", layout="wide", page_icon="🎬")

st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), 
                    url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070&auto=format&fit=crop");
        background-attachment: fixed;
        background-size: cover;
    }}
    .adult-warning {{ color: white; background-color: #d9534f; font-weight: bold; padding: 10px; border-radius: 5px; text-align: center; margin: 10px 0; font-size: 0.8em; }}
    .ott-link {{ background-color: #28a745; color: white !important; padding: 12px 20px; border-radius: 8px; text-decoration: none; display: block; margin-top: 15px; font-weight: bold; width: 100%; text-align: center; border: 2px solid #1e7e34; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
st.sidebar.title("👤 User Profile")
age = st.sidebar.number_input("Age", 1, 100, 18)
is_adult = age >= 18
media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}
sel_lang = st.sidebar.selectbox("Language", list(lang_map.keys()))

# --- 4. DATA HELPERS ---
def get_safe_val(item, key, default=None):
    if isinstance(item, dict): return item.get(key, default)
    return getattr(item, key, default)

@st.cache_data(ttl=3600)
def get_genres(m_type):
    g_list = genre_api.movie_list() if m_type == "Movies" else genre_api.tv_list()
    return {g['name']: g['id'] for g in g_list}

def get_detailed_info(m_id, m_type):
    try:
        res = movie_api.details(m_id, append_to_response="videos,credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="videos,credits,watch/providers")
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in res.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), None)
        providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
        ott_n = providers.get('flatrate', [{}])[0].get('provider_name', "Theaters/Rent")
        ott_l = providers.get('link', '#')
        rt = f"{res.get('runtime')} mins" if m_type == "Movies" else f"{res.get('episode_run_time', ['N/A'])[0]} mins/ep"
        return trailer, ott_n, ott_l, rt
    except: return None, "N/A", "#", "N/A"

# --- 5. TRENDING SECTION ---
st.title("🔥 Trending in India")
trending = trending_api.movie_day() if media_type == "Movies" else trending_api.tv_day()
t_cols = st.columns(6)
count = 0
for item in trending:
    if count >= 6 or isinstance(item, str): continue
    poster = get_safe_val(item, 'poster_path')
    if poster:
        with t_cols[count]:
            st.image(f"https://image.tmdb.org/t/p/w500{poster}")
            st.caption(get_safe_val(item, 'title', get_safe_val(item, 'name', '')))
            count += 1

st.divider()

# --- 6. EXPLORE: SEARCH & MOOD ---
st.header("🎯 Explore Cinema")
search_query = st.text_input("🔍 Search by title...")

col1, col2 = st.columns(2)
with col1:
    genre_dict = get_genres(media_type)
    selected_genres = st.multiselect("📂 Select Genres", list(genre_dict.keys()))
with col2:
    mood_map = {
        "Happy (Comedy/Animation)": [35, 16],
        "Sad (Drama/Romance)": [18, 10749],
        "Excited (Action/Adventure)": [28, 12],
        "Scared (Horror/Thriller)": [27, 53]
    }
    selected_mood = st.selectbox("🎭 What is your mood?", ["None"] + list(mood_map.keys()))

if st.button("Generate Recommendations") or search_query:
    results = []
    if search_query:
        results = movie_api.search(search_query) if media_type == "Movies" else tv_api.search(search_query)
    else:
        g_ids = [genre_dict[g] for g in selected_genres]
        if selected_mood != "None": g_ids.extend(mood_map[selected_mood])
        results = discover_api.discover_movies({'with_genres': ",".join(map(str, list(set(g_ids)))), 'with_original_language': lang_map[sel_lang]}) if media_type == "Movies" else discover_api.discover_tv_shows({'with_genres': ",".join(map(str, list(set(g_ids)))), 'with_original_language': lang_map[sel_lang]})

    if results:
        main_cols = st.columns(4)
        for i, item in enumerate(results[:20]):
            if isinstance(item, str): continue
            # Strict age safety check
            if not is_adult and get_safe_val(item, 'adult', False): continue
            
            poster = get_safe_val(item, 'poster_path')
            if poster:
                with main_cols[i % 4]:
                    st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                    st.subheader(get_safe_val(item, 'title', get_safe_val(item, 'name', '')))
                    with st.expander("Details & Watch"):
                        trailer, ott_n, ott_l, rt = get_detailed_info(get_safe_val(item, 'id'), media_type)
                        st.write(f"⏳ **Runtime:** {rt} | ⭐ **Rating:** {get_safe_val(item, 'vote_average')}")
                        st.write(get_safe_val(item, 'overview'))
                        if trailer: st.video(trailer)
                        st.markdown(f"**Streaming on:** {ott_n}")
                        if ott_l != "#": st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ WATCH NOW</a>', unsafe_allow_html=True)
