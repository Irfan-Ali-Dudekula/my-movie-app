import streamlit as st
from tmdbv3api import TMDb, Movie, Discover, Search
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# --- 1. SESSION INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
for key in ['role', 'u_name', 'u_age', 'user_db']:
    if key not in st.session_state:
        st.session_state[key] = [] if key == 'user_db' else (18 if key == 'u_age' else "Guest")

# --- 2. BULLETPROOF TMDB CONNECTION ---
@st.cache_resource
def get_safe_session():
    session = requests.Session()
    retries = Retry(total=10, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(pool_connections=20, pool_maxsize=100, max_retries=retries))
    return session

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.session = get_safe_session()
movie_api, discover_api, search_api = Movie(), Discover(), Search()

# --- 3. UI: STABLE DARK MODE ---
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide")

def apply_styles():
    dark_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ 
            background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{dark_img}"); 
            background-size: cover; background-attachment: fixed; color: #ffffff !important; 
        }}
        [data-testid="stSidebar"] {{ background: linear-gradient(180deg, #000000 0%, #2C2C2C 100%) !important; }}
        .movie-card {{ border: 1px solid #444; padding: 15px; border-radius: 10px; background: rgba(0, 0, 0, 0.85); margin-bottom: 20px; min-height: 600px; }}
        .play-button {{ background: #28a745 !important; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
        .ott-label {{ color: #00d4ff; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; display: block; }}
        h1, h2, h3, p, span, label, .stMarkdown {{ color: #ffffff !important; }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. DATA FETCHING (Rectified for Cast and Plot) ---
@st.cache_data(ttl=3600)
def fetch_details(m_id):
    try:
        res = movie_api.details(m_id, append_to_response="credits,watch/providers,videos")
        plot = getattr(res, 'overview', None)
        
        # RECTIFIED: Skip movies without enough info to avoid "dark screens"
        if not plot or len(plot) < 10: return None, None, None, None, None
        
        credits = getattr(res, 'credits', {})
        cast = ", ".join([c['name'] for c in credits.get('cast', [])[:5]])
        
        providers = getattr(res, 'watch/providers', {}).get('results', {}).get('IN', {})
        ott_n, ott_l = None, None
        for mode in ['flatrate', 'free', 'ads']:
            if mode in providers:
                ott_n, ott_l = providers[mode][0]['provider_name'], providers.get('link')
                break
        
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in getattr(res, 'videos', {}).get('results', []) if v['site'] == 'YouTube'), None)
        return plot, cast, ott_n, ott_l, trailer
    except: return None, None, None, None, None

# --- 5. MAIN APP FLOW ---
apply_styles()

if not st.session_state.logged_in:
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    u_age_input = st.number_input("Member Age", 1, 100, 18)
    if st.button("Enter ICU") and u_name:
        st.session_state.logged_in = True
        st.session_state.u_name, st.session_state.u_age = u_name, u_age_input
        st.rerun()
else:
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    st.sidebar.header("IRS Filters")
    mood_map = {"Happy": 35, "Sad": 18, "Adventures": 12, "Thrill": 53, "Excited": 28, "Romantic": 10749}
    sel_mood = st.sidebar.selectbox("Emotion", ["Select"] + list(mood_map.keys()))
    lang_map = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta", "Malayalam": "ml", "Kannada": "kn", "English": "en"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + sorted(list(lang_map.keys())))

    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    search_query = st.text_input("🔍 Quick Movie Search...")

    if st.button("Generate Recommendations 🚀") or search_query:
        results = []
        try:
            if search_query:
                results = [r for r in search_api.movies(search_query) if hasattr(r, 'id')]
            elif sel_mood != "Select" and sel_lang != "Select":
                p = {'with_original_language': lang_map[sel_lang], 'with_genres': mood_map[sel_mood], 'sort_by': 'popularity.desc'}
                # Multi-page scan to ensure results even with strict filters
                for page in range(1, 4):
                    p['page'] = page
                    batch = list(discover_api.discover_movies(p))
                    results.extend(batch)
                    if len(results) >= 60: break

            if results:
                cols = st.columns(3)
                processed = 0
                for item in results:
                    if processed >= 30: break 
                    poster = getattr(item, 'poster_path', None)
                    if not poster: continue # RECTIFIED: Skips Dark Screens
                    
                    plot, cast, ott_n, ott_l, trailer = fetch_details(item.id)
                    if not plot: continue 

                    with cols[processed % 3]:
                        st.markdown(f'<div class="movie-card">', unsafe_allow_html=True)
                        st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                        st.subheader(getattr(item, 'title', 'Unknown Title'))
                        
                        if ott_n: st.markdown(f"<span class='ott-label'>Available on: {ott_n}</span>", unsafe_allow_html=True)
                        else: st.markdown("<span class='ott-label'>Available on: Local Listings</span>", unsafe_allow_html=True)

                        with st.expander("📖 Story & Cast"):
                            st.write(f"**Plot:** {plot}")
                            st.write(f"**Cast:** {cast}")
                        
                        if trailer: st.video(trailer)
                        if ott_l: st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ WATCH NOW</a>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        processed += 1
            else:
                st.warning("No recommendations found. Try adjusting your Emotion or Language filters.")
        except Exception:
            st.error("Connection unstable. Please refresh.")
