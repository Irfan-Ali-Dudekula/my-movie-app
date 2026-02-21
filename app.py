import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Search
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# --- 1. SESSION INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_db' not in st.session_state:
    st.session_state.user_db = [] 
if 'role' not in st.session_state:
    st.session_state.role = "Subscriber"

# --- 2. FAST & BULLETPROOF TMDB CONNECTION ---
@st.cache_resource
def get_safe_session():
    session = requests.Session()
    # Optimized to prevent buffering and "Too many open files" error
    retries = Retry(total=10, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(pool_connections=50, pool_maxsize=100, max_retries=retries))
    return session

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.session = get_safe_session()
movie_api, tv_api, discover_api, search_api = Movie(), TV(), Discover(), Search()

# --- 3. UI: STABLE DARK MODE ---
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide")

def apply_styles():
    dark_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    # RECTIFIED: Fixed CSS Braces and Syntax to prevent TokenError
    st.markdown(f"""
        <style>
        .stApp {{ 
            background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{dark_img}"); 
            background-size: cover; background-attachment: fixed; color: #ffffff !important; 
        }}
        [data-testid="stSidebar"] {{ background: linear-gradient(180deg, #000000 0%, #2C2C2C 100%) !important; }}
        .movie-card {{ border: 1px solid #444; padding: 15px; border-radius: 10px; background: rgba(0, 0, 0, 0.85); margin-bottom: 20px; min-height: 600px; }}
        .play-button {{ background: #28a745 !important; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
        .rating-badge {{ background: #f5c518; color: black; padding: 2px 8px; border-radius: 5px; font-weight: bold; margin-bottom: 5px; display: inline-block; }}
        .ott-label {{ color: #00d4ff; font-weight: bold; font-size: 1.1em; margin-top: 10px; display: block; }}
        h1, h2, h3, p, span, label, .stMarkdown {{ color: #ffffff !important; }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. DATA FETCHING (Rectified to Remove Dark Spaces) ---
@st.cache_data(ttl=3600)
def fetch_details(m_id, type_str):
    try:
        obj = movie_api if type_str == "Movies" else tv_api
        res = obj.details(m_id, append_to_response="credits,watch/providers,videos")
        rating = getattr(res, 'vote_average', 0.0)
        plot = getattr(res, 'overview', None)
        
        # RECTIFIED: Validates Plot to prevent empty cards
        if not plot or len(plot) < 10: return None, None, None, None, None, 0.0
        
        credits = getattr(res, 'credits', {})
        cast = ", ".join([c['name'] for c in credits.get('cast', [])[:5]])
        providers = getattr(res, 'watch/providers', {}).get('results', {}).get('IN', {})
        ott_n, ott_l = None, None
        for mode in ['flatrate', 'free', 'ads']:
            if mode in providers:
                ott_n = providers[mode][0]['provider_name']
                ott_l = providers.get('link')
                break
        
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in getattr(res, 'videos', {}).get('results', []) if v['site'] == 'YouTube'), None)
        return plot, cast, ott_n, ott_l, trailer, rating
    except: return None, None, None, None, None, 0.0

# --- 5. MAIN FLOW ---
apply_styles()

if not st.session_state.logged_in:
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Username").strip()
    u_age = st.number_input("Age", 1, 100, 18)
    p_word = st.text_input("Security Password", type="password") if u_name.lower() == "irfan" else ""

    if st.button("Enter ICU") and u_name:
        if u_name.lower() == "irfan":
            if p_word == "Irfan@1403": 
                st.session_state.role, st.session_state.logged_in = "Admin", True
            else: 
                st.error("Wrong Admin Pass"); st.stop()
        else:
            st.session_state.role, st.session_state.logged_in = "Subscriber", True
        
        if st.session_state.logged_in:
            st.session_state.u_name, st.session_state.u_age = u_name, u_age
            st.session_state.user_db.append({"User": u_name, "Age": u_age, "Role": st.session_state.role, "Time": datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.rerun()
else:
    if st.sidebar.button("🚪 Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    app_mode = st.sidebar.radio("Nav", ["User Portal", "Admin Center"]) if st.session_state.role == "Admin" else "User Portal"

    if app_mode == "Admin Center":
        st.title("🛡️ Admin Center")
        st.table(pd.DataFrame(st.session_state.user_db))
    else:
        st.sidebar.header("IRS Filters")
        m_type = st.sidebar.selectbox("Content", ["Movies", "TV Shows"])
        mood_map = {"Happy": 35, "Sad": 18, "Adventures": 12, "Thrill": 53, "Excited": 28, "Romantic": 10749}
        sel_mood = st.sidebar.selectbox("Emotion", ["Select"] + list(mood_map.keys()))
        
        # RECTIFIED: Fixed Syntax Error in Language Map (Quotes Added)
        lang_map = {
            "Telugu": "te", "Hindi": "hi", "Tamil": "ta", "English": "en", 
            "Malayalam": "ml", "Kannada": "kn", "Korean": "ko", "Japanese": "ja"
        }
        sel_lang = st.sidebar.selectbox("Language", ["Select"] + sorted(list(lang_map.keys())))

        if st.button("Generate Recommendations 🚀"):
            results = []
            if sel_mood != "Select" and sel_lang != "Select":
                # Smart discovery to ensure results appear
                p = {'with_original_language': lang_map[sel_lang], 'with_genres': mood_map[sel_mood], 'sort_by': 'popularity.desc'}
                for page in range(1, 6):
                    p['page'] = page
                    batch = list(discover_api.discover_movies(p) if m_type == "Movies" else discover_api.discover_tv_shows(p))
                    results.extend(batch)
                    if len(results) >= 150: break

            if results:
                cols = st.columns(3)
                processed = 0
                for item in results:
                    if processed >= 75: break 
                    poster = getattr(item, 'poster_path', None)
                    if not poster: continue # RECTIFIED: Skips Dark Spaces
                    
                    plot, cast, ott_n, ott_l, trailer, rating = fetch_details(item.id, m_type)
                    if not plot: continue 

                    with cols[processed % 3]:
                        st.markdown(f'<div class="movie-card">', unsafe_allow_html=True)
                        st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                        st.subheader(getattr(item, 'title', getattr(item, 'name', '')))
                        st.markdown(f"<span class='rating-badge'>IMDb: {rating:.1f}</span>", unsafe_allow_html=True)
                        if ott_n: st.markdown(f"<span class='ott-label'>Available on: {ott_n}</span>", unsafe_allow_html=True)
                        
                        with st.expander("📖 Bio & Cast"):
                            st.write(f"**Bio:** {plot}")
                            st.write(f"**Cast:** {cast}")
                        
                        if trailer: st.video(trailer)
                        if ott_l: st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ WATCH NOW</a>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        processed += 1
            else:
                st.warning("No recommendations found. Try adjusting your Emotion or Language filters.")
