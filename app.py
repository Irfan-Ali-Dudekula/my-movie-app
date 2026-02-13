import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import random

# --- 1. CORE STABILIZATION ---
@st.cache_resource
def get_bulletproof_session():
    """Prevents OSError(24) and keeps the connection stable"""
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=retries)
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

# --- 2. ADMIN DATABASE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = []

st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide", page_icon="🎬")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; color: white; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(20%); object-fit: cover; }}
        .play-button {{ background: linear-gradient(45deg, #e50914, #ff4b4b); color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: none; }}
        .ott-badge {{ background-color: #28a745; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 5px; }}
        .cast-text {{ color: #cccccc; font-size: 0.9em; font-style: italic; }}
        h1, h2, h3, p, span, label, div {{ color: white !important; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

# --- 3. LOGIN & SECURITY ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    u_age = st.number_input("Member Age", 1, 100, 18)
    admin_key = st.text_input("Security Key (Admin Only)", type="password") if u_name.lower() == "irfan" else ""

    if st.button("Enter ICU"):
        if u_name:
            if u_name.lower() == "irfan":
                if admin_key == "Irfan@1403": # Updated Security Key
                    st.session_state.role = "Admin"
                else:
                    st.error("Invalid Security Key!")
                    st.stop()
            else:
                st.session_state.role = "Subscriber"
            st.session_state.logged_in, st.session_state.u_name = True, u_name
            st.session_state.user_db.append({"Time": datetime.now().strftime("%H:%M:%S"), "User": u_name, "Role": st.session_state.role})
            st.rerun()
else:
    # --- 4. NAVIGATION ---
    set_bg()
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    if st.session_state.role == "Admin":
        app_mode = st.sidebar.radio("Navigation", ["User Portal", "Admin Command Center"])
    else:
        app_mode = "User Portal"

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # --- 5. ADMIN CENTER ---
    if app_mode == "Admin Command Center":
        st.title("🛡️ Admin Command Center")
        if st.button("🚀 FULL SYSTEM REBOOT"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("System Rebooted!")
        st.table(pd.DataFrame(st.session_state.user_db))
    
    # --- 6. USER PORTAL ---
    else:
        st.sidebar.header("Filter Content")
        m_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
        
        mood_map = {
            "Happy/Feel Good": 35, "Scary/Horror": 27, "Action/Thrilling": 28,
            "Romantic": 10749, "Mysterious": 9648, "Emotional/Sad": 18, "Adventurous": 12
        }
        sel_mood = st.sidebar.selectbox("Current Mood", ["Select"] + list(mood_map.keys()))

        lang_map = {
            "Telugu": "te", "Hindi": "hi", "Tamil": "ta", "Malayalam": "ml", 
            "Kannada": "kn", "English": "en", "Spanish": "es", "Korean": "ko", "Japanese": "ja"
        }
        sel_lang = st.sidebar.selectbox("Language", ["Select"] + sorted(list(lang_map.keys())))
        sel_era = st.sidebar.selectbox("Choose Era", ["Select", "2020-2030", "2010-2020", "2000-2010", "1990-2000"])

        @st.cache_data(ttl=3600)
        def get_deep_details(m_id, type_str):
            try:
                res = movie_api.details(m_id, append_to_response="credits,watch/providers,videos") if type_str == "Movies" else tv_api.details(m_id, append_to_response="credits,watch/providers,videos")
                plot = res.overview if res.overview else "No plot available."
                cast = ", ".join([c['name'] for c in res.credits['cast'][:5]]) if 'credits' in res else "N/A"
                providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
                ott_n, ott_l = None, None
                if 'flatrate' in providers:
                    ott_n, ott_l = providers['flatrate'][0]['provider_name'], providers.get('link')
                elif 'free' in providers:
                    ott_n, ott_l = f"{providers['free'][0]['provider_name']} (Free)", providers.get('link')
                elif 'ads' in providers:
                    ott_n, ott_l = f"{providers['ads'][0]['provider_name']} (With Ads)", providers.get('link')
                
                trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in res.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), None)
                return plot, cast, ott_n, ott_l, trailer
            except: return "N/A", "N/A", None, None, None

        st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
        st.subheader("Mood Based Movie Recommendation System")
        search_query = st.text_input("🔍 Search Movies...")

        if st.button("Generate Recommendations 🚀") or search_query:
            results = []
            try:
                if search_query:
                    results = list(search_api.multi(search_query))
                elif m_type != "Select" and sel_lang != "Select" and sel_era != "Select" and sel_mood != "Select":
                    s_year, e_year = map(int, sel_era.split('-'))
                    # RECTIFIED PARAMETERS: Expanded monetization types to avoid empty results
                    p = {
                        'with_original_language': lang_map[sel_lang], 
                        'primary_release_date.gte': f"{s_year}-01-01", 
                        'primary_release_date.lte': f"{e_year}-12-31", 
                        'with_genres': mood_map[sel_mood],
                        'watch_region': 'IN',
                        'with_watch_monetization_types': 'flatrate|free|ads',
                        'sort_by': 'popularity.desc'
                    }
                    results = list(discover_api.discover_movies(p) if m_type == "Movies" else discover_api.discover_tv_shows(p))

                if results:
                    cols = st.columns(3)
                    processed = 0
                    for item in results:
                        if processed >= 12: break 
                        rd_str = getattr(item, 'release_date', getattr(item, 'first_air_date', ''))
                        if not rd_str: continue
                        
                        item_year = int(rd_str.split('-')[0])
                        if not search_query and (item_year < s_year or item_year > e_year): continue

                        plot, cast, ott_n, ott_l, trailer = get_deep_details(item.id, m_type)
                        
                        # Show result if we found OTT details
                        if ott_n:
                            with cols[processed % 3]:
                                st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                                st.subheader(f"{getattr(item, 'title', getattr(item, 'name', ''))[:20]} ({item_year})")
                                with st.expander("📖 Plot & Details"):
                                    st.write(f"**Plot:** {plot}")
                                    st.markdown(f"**Cast:** <span class='cast-text'>{cast}</span>", unsafe_allow_html=True)
                                st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                                if trailer: st.video(trailer)
                                if ott_l: st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ WATCH NOW</a>', unsafe_allow_html=True)
                            processed += 1
                    
                    if processed == 0:
                        st.warning("No streaming results found for this specific Era/Language combo. Try a different Era!")
                else:
                    st.info("No content found. Try adjusting your mood or language!")
            except Exception as e: st.warning("Connection busy. Please wait 5 seconds and click again.")
