import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Search
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# --- INITIALIZATION ---
for key in ['logged_in', 'role', 'u_age', 'u_name', 'user_db']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'logged_in' else (18 if key == 'u_age' else ("Guest" if key == 'u_name' else ( [] if key == 'user_db' else "Subscriber")))

# --- API STABILIZATION ---
@st.cache_resource
def get_bulletproof_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.session = get_bulletproof_session() 
movie_api, tv_api, discover_api, search_api = Movie(), TV(), Discover(), Search()

# --- UI STYLING ---
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide")

def set_bg():
    st.markdown("""<style>
        .stApp { background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"); background-size: cover; background-attachment: fixed; color: white; }
        .play-button { background: #28a745 !important; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }
        .ott-badge { background-color: #28a745; color: white; padding: 4px 10px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 8px; }
        h1, h2, h3, p, span, label, div { color: white !important; }
        </style>""", unsafe_allow_html=True)

# --- LOGIN & FLOW ---
if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    u_age_in = st.number_input("Age", 1, 100, 18)
    admin_key = st.text_input("Security Key", type="password") if u_name.lower() == "irfan" else ""

    if st.button("Enter ICU"):
        if u_name:
            if u_name.lower() == "irfan" and admin_key == "Irfan@1403": st.session_state.role = "Admin"
            else: st.session_state.role = "Subscriber"
            st.session_state.logged_in, st.session_state.u_name, st.session_state.u_age = True, u_name, u_age_in
            st.rerun()
else:
    set_bg()
    app_mode = st.sidebar.radio("Nav", ["User Portal", "Admin Command Center"]) if st.session_state.role == "Admin" else "User Portal"

    if app_mode == "Admin Command Center":
        st.title("🛡️ Admin Center")
        if st.button("🚀 FULL SYSTEM REBOOT"): 
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("API Cache Cleared!")
        st.table(pd.DataFrame(st.session_state.user_db))
    else:
        st.sidebar.header("IRS Filters")
        m_type = st.sidebar.selectbox("Content", ["Movies", "TV Shows"])
        mood_map = {"Laughter": 35, "Fear": 27, "Excitement": 28, "Mystery": 9648, "Emotional": 18}
        sel_mood = st.sidebar.selectbox("Emotion", ["Select"] + list(mood_map.keys()))
        lang_map = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta", "English": "en"}
        sel_lang = st.sidebar.selectbox("Language", ["Select"] + sorted(list(lang_map.keys())))

        if st.button("Generate Recommendations 🚀"):
            if sel_mood != "Select" and sel_lang != "Select":
                p = {'with_original_language': lang_map[sel_lang], 'with_genres': mood_map[sel_mood], 'sort_by': 'popularity.desc'}
                
                # API Call with Fallback
                try:
                    results = list(discover_api.discover_movies(p) if m_type == "Movies" else discover_api.discover_tv_shows(p))
                    if not results:
                        st.warning("No movies found for this filter. The API is connected but the database is empty for this selection.")
                    else:
                        cols = st.columns(3)
                        for i, item in enumerate(results[:12]):
                            with cols[i % 3]:
                                st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                                st.subheader(getattr(item, 'title', getattr(item, 'name', '')))
                except Exception as e:
                    st.error(f"API Error: {e}. Please check your TMDB API Key in the code.")
