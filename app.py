import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Search
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# --- 1. SESSION INITIALIZATION ---
if 'u_age' not in st.session_state:
    st.session_state.u_age = 18
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_db' not in st.session_state:
    st.session_state.user_db = []

# --- 2. CORE STABILIZATION (Stops Connection Crashes) ---
@st.cache_resource
def get_bulletproof_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=100, max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.session = get_bulletproof_session() 
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, search_api = Discover(), Search()

# --- 3. UI: THEATER BACKGROUND & STYLING ---
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide", page_icon="🎬")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; color: white; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(20%); object-fit: cover; }}
        .play-button {{ background: #28a745 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: none; transition: 0.3s; }}
        .play-button:hover {{ background: #218838 !important; transform: scale(1.02); }}
        .ott-badge {{ background-color: #28a745; color: white; padding: 4px 10px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 8px; border: 1px solid #ffffff; }}
        .cast-text {{ color: #00ffcc; font-size: 0.9em; font-weight: bold; }}
        h1, h2, h3, p, span, label, div {{ color: white !important; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

# --- 4. DATA EXTRACTION ---
@st.cache_data(ttl=3600)
def get_deep_meta(m_id, type_str):
    try:
        obj = movie_api if type_str == "Movies" else tv_api
        res = obj.details(m_id, append_to_response="credits,watch/providers,videos")
        plot = getattr(res, 'overview', "Plot not available.")
        cast = ", ".join([c['name'] for c in getattr(res, 'credits', {}).get('cast', [])[:5]])
        providers = getattr(res, 'watch/providers', {}).get('results', {}).get('IN', {})
        ott_n, ott_l = None, None
        for mode in ['flatrate', 'free', 'ads']:
            if mode in providers:
                ott_n, ott_l = providers[mode][0]['provider_name'], providers.get('link')
                break
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in getattr(res, 'videos', {}).get('results', []) if v['site'] == 'YouTube'), None)
        return plot, cast, ott_n, ott_l, trailer
    except: return None, None, None, None, None

# --- 5. APP FLOW ---
if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    u_age_input = st.number_input("Member Age", 1, 100, 18)
    admin_key = st.text_input("Security Key", type="password") if u_name.lower() == "irfan" else ""

    if st.button("Enter ICU"):
        if u_name:
            if u_name.lower() == "irfan" and admin_key != "Irfan@1403":
                st.error("Invalid Security Key!")
                st.stop()
            st.session_state.logged_in, st.session_state.u_name, st.session_state.u_age = True, u_name, u_age_input
            st.session_state.user_db.append({"User": u_name, "Age": u_age_input, "Time": datetime.now().strftime("%H:%M")})
            st.rerun()
else:
    set_bg()
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    m_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
    mood_map = {"Laughter": 35, "Fear": 27, "Excitement": 28, "Mystery": 9648, "Emotional": 18, "Adventurous": 12}
    if st.session_state.u_age >= 18: mood_map["Love/Romantic"] = 10749
    sel_mood = st.sidebar.selectbox("Current Emotion", ["Select"] + list(mood_map.keys()))
    lang_map = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta", "English": "en", "Malayalam": "ml", "Kannada": "kn", "Korean": "ko"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + sorted(list(lang_map.keys())))
    sel_era = st.sidebar.selectbox("Era", ["Select", "2020-2030", "2010-2020", "2000-2010"])

    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    st.subheader("Mood Based Movie Recommendation System")
    search_query = st.text_input("🔍 Search Movies...") # RESTORED SEARCH BAR

    if st.button("Generate Recommendations 🚀") or search_query:
        results = []
        if search_query:
            results = [r for r in search_api.multi(search_query) if hasattr(r, 'id')]
        elif sel_mood != "Select" and sel_lang != "Select" and sel_era != "Select":
            s_year, e_year = map(int, sel_era.split('-'))
            p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.gte': f"{s_year}-01-01", 'primary_release_date.lte': f"{e_year}-12-31", 'with_genres': mood_map[sel_mood], 'sort_by': 'popularity.desc', 'include_adult': st.session_state.u_age >= 18}
            # SMART FALLBACK: Tries India OTT first, then general search
            p_strict = {**p, 'watch_region': 'IN', 'with_watch_monetization_types': 'flatrate|free|ads'}
            results = list(discover_api.discover_movies(p_strict) if m_type == "Movies" else discover_api.discover_tv_shows(p_strict))
            if not results:
                st.info("No specific India streaming links found. Showing popular titles!")
                results = list(discover_api.discover_movies(p) if m_type == "Movies" else discover_api.discover_tv_shows(p))

        if results:
            cols = st.columns(3)
            processed = 0
            for item in results:
                if processed >= 75: break
                plot, cast, ott_n, ott_l, trailer = get_deep_meta(item.id, m_type)
                if not plot: continue
                with cols[processed % 3]:
                    st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                    st.subheader(f"{getattr(item, 'title', getattr(item, 'name', ''))[:20]}")
                    with st.expander("📖 Plot & Cast"):
                        st.write(f"**Plot:** {plot}")
                        st.markdown(f"**Cast:** <span class='cast-text'>{cast}</span>", unsafe_allow_html=True)
                    if ott_n: st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                    if trailer: st.video(trailer)
                    if ott_l: st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ PLAY NOW</a>', unsafe_allow_html=True)
                    processed += 1
