import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import random

# --- 1. CRITICAL INITIALIZATION (Fixes image_dc3040.png) ---
if 'u_age' not in st.session_state:
    st.session_state.u_age = 18
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_db' not in st.session_state:
    st.session_state.user_db = []
if 'u_name' not in st.session_state:
    st.session_state.u_name = "Guest"

# --- 2. CORE STABILIZATION ---
@st.cache_resource
def get_bulletproof_session():
    session = requests.Session()
    retries = Retry(total=10, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=40, max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.session = get_bulletproof_session() 
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 3. UI & BACKGROUND ---
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

# --- 4. LOGIN & SECURITY ---
if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    u_age_input = st.number_input("Member Age", 1, 100, 18)
    admin_key = st.text_input("Security Key", type="password") if u_name.lower() == "irfan" else ""

    if st.button("Enter ICU"):
        if u_name:
            if u_name.lower() == "irfan":
                if admin_key == "Irfan@1403": 
                    st.session_state.role = "Admin"
                else:
                    st.error("Invalid Security Key!")
                    st.stop()
            else:
                st.session_state.role = "Subscriber"
            
            st.session_state.logged_in, st.session_state.u_name, st.session_state.u_age = True, u_name, u_age_input
            st.session_state.user_db.append({"Time": datetime.now().strftime("%H:%M:%S"), "User": u_name, "Age": u_age_input, "Role": st.session_state.role})
            st.rerun()
else:
    set_bg()
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    if st.session_state.role == "Admin":
        app_mode = st.sidebar.radio("Navigation", ["User Portal", "Admin Command Center"])
    else:
        app_mode = "User Portal"

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    if app_mode == "Admin Command Center":
        st.title("🛡️ Admin Command Center")
        if st.button("🚀 FULL SYSTEM REBOOT"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("System Cleaned!")
        st.table(pd.DataFrame(st.session_state.user_db))
    
    else:
        st.sidebar.header("Filter Content")
        m_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
        mood_map = {"Happy/Feel Good": 35, "Scary/Horror": 27, "Action/Thrilling": 28, "Mysterious": 9648, "Emotional/Sad": 18, "Adventurous": 12}
        if st.session_state.u_age >= 18: mood_map["Romantic"] = 10749
        
        sel_mood = st.sidebar.selectbox("Current Mood", ["Select"] + list(mood_map.keys()))
        lang_map = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta", "English": "en"}
        sel_lang = st.sidebar.selectbox("Language", ["Select"] + sorted(list(lang_map.keys())))
        sel_era = st.sidebar.selectbox("Choose Era", ["Select", "2020-2030", "2010-2020", "2000-2010"])

        @st.cache_data(ttl=3600)
        def get_real_details(m_id, type_str):
            try:
                obj = movie_api if type_str == "Movies" else tv_api
                res = obj.details(m_id, append_to_response="credits,watch/providers,videos")
                plot = res.overview if hasattr(res, 'overview') and res.overview else "No summary available."
                cast_data = getattr(res, 'credits', {}).get('cast', [])
                cast = ", ".join([c['name'] for c in cast_data[:5]]) if cast_data else "Cast not listed."
                providers = getattr(res, 'watch/providers', {}).get('results', {}).get('IN', {})
                ott_n, ott_l = None, None
                for mode in ['flatrate', 'free', 'ads']:
                    if mode in providers:
                        ott_n, ott_l = providers[mode][0]['provider_name'], providers.get('link')
                        break
                trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in getattr(res, 'videos', {}).get('results', []) if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)
                return plot, cast, ott_n, ott_l, trailer
            except: return None, None, None, None, None

        st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
        st.subheader("Mood Based Movie Recommendation System")

        search_query = st.text_input("🔍 Search Movies...")

        if st.button("Generate Recommendations 🚀") or search_query:
            results = []
            try:
                if search_query:
                    # FIX: Handle search objects correctly to avoid 'str' errors
                    search_results = search_api.multi(search_query)
                    results = [r for r in search_results if hasattr(r, 'id')]
                elif m_type != "Select" and sel_lang != "Select" and sel_era != "Select" and sel_mood != "Select":
                    s_year, e_year = map(int, sel_era.split('-'))
                    p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.gte': f"{s_year}-01-01", 'primary_release_date.lte': f"{e_year}-12-31", 'with_genres': mood_map[sel_mood], 'sort_by': 'popularity.desc', 'include_adult': False if st.session_state.u_age < 18 else True}
                    results = list(discover_api.discover_movies(p) if m_type == "Movies" else discover_api.discover_tv_shows(p))

                if results:
                    cols = st.columns(3)
                    processed = 0
                    for item in results:
                        if processed >= 12: break 
                        # RECTIFIED: Ensure item is an object with an ID
                        m_id = getattr(item, 'id', None)
                        if not m_id: continue

                        plot, cast, ott_n, ott_l, trailer = get_real_details(m_id, m_type if m_type != "Select" else "Movies")
                        if not plot: continue

                        with cols[processed % 3]:
                            st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                            st.subheader(f"{getattr(item, 'title', getattr(item, 'name', ''))[:20]}")
                            with st.expander("📖 View Real Plot & Cast"):
                                st.markdown(f"**Plot:** {plot}")
                                st.markdown(f"**Cast:** <span class='cast-text'>{cast}</span>", unsafe_allow_html=True)
                            if ott_n: st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                            if trailer: st.video(trailer)
                            if ott_l: st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ PLAY NOW</a>', unsafe_allow_html=True)
                            processed += 1
            except Exception as e:
                st.warning("Connection unstable. Please refresh the page.")
