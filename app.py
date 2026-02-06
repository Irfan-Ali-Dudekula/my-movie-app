import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending
from datetime import datetime

# --- 1. CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()

# --- 2. PAGE SETUP & BACKGROUND ---
st.set_page_config(page_title="CinemaPro India", layout="wide", page_icon="🎬")

def set_ui_styles():
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                        url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070&auto=format&fit=crop");
            background-attachment: fixed;
            background-size: cover;
        }}
        .ott-link {{ background-color: #28a745; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; }}
        </style>
        """, unsafe_allow_html=True)

set_ui_styles()

# --- 3. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🎬 CinemaPro India")
    tab1, tab2 = st.tabs(["Login", "Register / Forgot Password"])
    
    with tab1:
        st.write("### Welcome Back")
        u_name = st.text_input("Name")
        u_age = st.number_input("Your Age", 1, 100, 18)
        if st.button("Enter Website"):
            if u_name:
                st.session_state.logged_in = True
                st.session_state.user_name = u_name
                st.session_state.user_age = u_age
                st.rerun()
            else:
                st.error("Please enter your name.")
    with tab2:
        st.info("Registration and Password Recovery are currently under maintenance.")

else:
    # --- 4. MAIN APP CONTENT ---
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    st.sidebar.write(f"Access: {'Adult' if st.session_state.user_age >= 18 else 'Standard'}")
    is_adult = st.session_state.user_age >= 18
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.divider()
    media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}
    sel_lang = st.sidebar.selectbox("Language", list(lang_map.keys()))

    # --- 5. DATA HELPERS (Fixing the loop errors) ---
    def get_safe_val(item, key, default=None):
        if isinstance(item, dict): return item.get(key, default)
        return getattr(item, key, default)

    def get_detailed_info(m_id, m_type):
        try:
            res = movie_api.details(m_id, append_to_response="videos,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="videos,watch/providers")
            trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in res.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), None)
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            ott_n = providers.get('flatrate', [{}])[0].get('provider_name', "Theaters/
