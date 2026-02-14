import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Search
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# --- 1. SESSION INITIALIZATION ---
if 'theme' not in st.session_state:
    st.session_state.theme = "Dark"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
for key in ['role', 'u_name', 'user_db']:
    if key not in st.session_state:
        st.session_state[key] = [] if key == 'user_db' else "Guest"

# --- 2. CORE STABILIZATION (Prevents API Connection Drops) ---
@st.cache_resource
def get_safe_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(pool_connections=20, pool_maxsize=100, max_retries=retries))
    return session

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.session = get_safe_session()
movie_api, tv_api, discover_api, search_api = Movie(), TV(), Discover(), Search()

# --- 3. UI: THEATER STYLING WITH CUSTOM THEMES ---
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide")

def apply_styles():
    dark_video = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    light_img = "http://googleusercontent.com/image_generation_content/0" # Your uploaded Light Theme Image
    dark_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    
    if st.session_state.theme == "Light":
        main_bg = f"url({light_img})"
        sidebar_color = "linear-gradient(180deg, #FFFFFF 0%, #FFFDD0 100%)" # White to Cream
        text_color = "#000000"
        card_bg = "rgba(255, 255, 255, 0.8)"
        led_style = "box-shadow: 0 0 15px #00d4ff; border: 2px solid #00d4ff;"
    else:
        main_bg = f"url({dark_img})"
        sidebar_color = "linear-gradient(180deg, #000000 0%, #2C2C2C 100%)" # Black to Gray
        text_color = "#ffffff"
        card_bg = "rgba(0, 0, 0, 0.6)"
        led_style = "border: 1px solid #444;"

    st.markdown(f"""
        <style>
        .stApp {{ background: {main_bg}; background-size: cover; background-attachment: fixed; color: {text_color} !important; }}
        [data-testid="stSidebar"] {{ background: {sidebar_color}; }}
        .movie-card {{ {led_style} padding: 15px; border-radius: 10px; background: {card_bg}; margin-bottom: 20px; transition: 0.3s; }}
        .play-button {{ background: #28a745 !important; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
        h1, h2, h3, p, span, label, div {{ color: {text_color} !important; }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. DATA LOGIC ---
@st.cache_data(ttl=3600)
def fetch_movie_data(m_id, type_str):
    try:
        obj = movie_api if type_str == "Movies" else tv_api
        res = obj.details(m_id, append_to_response="credits,watch/providers,videos")
        providers = getattr(res, 'watch/providers', {}).get('results', {}).get('IN', {})
        ott_n, ott_l = None, None
        for mode in ['flatrate', 'free', 'ads']:
            if mode in providers:
                ott_n, ott_l = providers[mode][0]['provider_name'], providers.get('link')
                break
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in getattr(res, 'videos', {}).get('results', []) if v['site'] == 'YouTube'), None)
        return res.overview, ", ".join([c['name'] for c in getattr(res, 'credits', {}).get('cast', [])[:5]]), ott_n, ott_l, trailer
    except: return None, None, None, None, None

# --- 5. MAIN FLOW ---
apply_styles()

if not st.session_state.logged_in:
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Name").strip()
    if st.button("Enter ICU") and u_name:
        st.session_state.logged_in, st.session_state.u_name = True, u_name
        st.rerun()
else:
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    st.session_state.theme = st.sidebar.radio("Theater Mode", ["Dark", "Light"])
    
    st.sidebar.header("IRS Filters")
    m_type = st.sidebar.selectbox("Content", ["Movies", "TV Shows"])
    mood_map = {"Happy": 35, "Sad": 18, "Adventures": 12, "Thrill": 53, "Excited": 28}
    sel_mood = st.sidebar.selectbox("Emotion", ["Select"] + list(mood_map.keys()))
    lang_map = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta", "English": "en"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + sorted(list(lang_map.keys())))

    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    search_query = st.text_input("🔍 Quick Search...")

    if st.button("Generate Recommendations 🚀") or search_query:
        results = []
        if search_query:
            results = [r for r in search_api.multi(search_query) if hasattr(r, 'id')]
        elif sel_mood != "Select" and sel_lang != "Select":
            p = {'with_original_language': lang_map[sel_lang], 'with_genres': mood_map[sel_mood], 'sort_by': 'popularity.desc'}
            
            # RECTIFICATION: Smart Fallback (Ensures screen is never blank)
            p_strict = {**p, 'watch_region': 'IN', 'with_watch_monetization_types': 'flatrate|free|ads'}
            results = list(discover_api.discover_movies(p_strict) if m_type == "Movies" else discover_api.discover_tv_shows(p_strict))
            
            if not results:
                st.info("Expanding search to popular global titles (Limited local OTT links found).")
                results = list(discover_api.discover_movies(p) if m_type == "Movies" else discover_api.discover_tv_shows(p))

        if results:
            cols = st.columns(3)
            for i, item in enumerate(results[:15]):
                m_title = getattr(item, 'title', getattr(item, 'name', 'Unknown Title'))
                m_id = getattr(item, 'id', None)
                if not m_id: continue

                plot, cast, ott_n, ott_l, trailer = fetch_movie_data(m_id, m_type)
                with cols[i % 3]:
                    st.markdown(f'<div class="movie-card">', unsafe_allow_html=True)
                    st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                    st.subheader(m_title)
                    with st.expander("📖 Story & Cast"):
                        st.write(f"**Plot:** {plot}")
                        st.write(f"**Cast:** {cast}")
                    if ott_n: st.info(f"📺 {ott_n.upper()}")
                    if trailer: st.video(trailer)
                    if ott_l: st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ WATCH NOW</a>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
