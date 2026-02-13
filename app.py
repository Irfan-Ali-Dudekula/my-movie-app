import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests

# --- 1. CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 2. PAGE SETUP & THEME LOGIC ---
st.set_page_config(page_title="Irfan Recommendation System (IRS)", layout="wide", page_icon="🎬")

# Theme Toggle in Sidebar
if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark'

def set_imax_ui(theme):
    # LED Ceiling Animation & Theater Styling
    bg_color = "rgba(0,0,0,0.9)" if theme == 'Dark' else "rgba(255,255,255,0.9)"
    text_color = "white" if theme == 'Dark' else "black"
    led_color = "rgba(0, 150, 255, 0.5)" # Cyan IMAX style
    
    st.markdown(f"""
        <style>
        .stApp {{
            background: {bg_color};
            color: {text_color};
        }}
        /* LED Ceiling Decoration Logic */
        .ceiling-lights {{
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100px;
            background: radial-gradient(circle, {led_color} 1px, transparent 1px);
            background-size: 20px 20px;
            z-index: 99;
            filter: blur(1px);
            opacity: 0.6;
            animation: twinkle 3s infinite;
        }}
        @keyframes twinkle {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 0.7; }}
        }}
        .ott-link {{ background-color: #e50914; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
        .rating-box {{ background-color: #f5c518; color: #000; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 5px; }}
        .plot-box {{ line-height: 1.6; font-size: 0.95em; margin-bottom: 10px; }}
        </style>
        <div class="ceiling-lights"></div>
        """, unsafe_allow_html=True)

# --- 3. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🍿 Irfan Recommendation System (IRS)")
    u_name = st.text_input("Name")
    u_age = st.number_input("Your Age", 1, 100, 18)
    if st.button("Enter IRS"):
        if u_name:
            st.session_state.logged_in = True
            st.session_state.u_name = u_name
            st.session_state.u_age = u_age
            st.rerun()
        else: st.error("Please enter your name.")
else:
    # Sidebar Controls
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    st.session_state.theme = st.sidebar.radio("Theater Mode", ["Dark", "Light"])
    set_imax_ui(st.session_state.theme)
    
    is_adult = st.session_state.u_age >= 18
    st.sidebar.markdown("<div style='font-size:0.8em;'>Powered by TMDB API</div>", unsafe_allow_html=True)

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    media_type = st.sidebar.selectbox("Content Type 📺", ["Select", "Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Korean": "ko"}
    sel_lang = st.sidebar.selectbox("Language 🌍", ["Select"] + list(lang_map.keys()))

    # --- 4. DATA HELPERS ---
    def get_detailed_info(m_id, m_type):
        try:
            res = movie_api.details(m_id, append_to_response="credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="credits,watch/providers")
            cast = ", ".join([c['name'] for c in res.get('credits', {}).get('cast', [])[:5]])
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            ott_n, ott_l = None, None
            if 'flatrate' in providers:
                ott_n = providers['flatrate'][0]['provider_name']
                ott_l = providers.get('link') 
            elif 'ads' in providers:
                ott_n = f"{providers['ads'][0]['provider_name']} (Free)"
                ott_l = providers.get('link')
            return cast, ott_n, ott_l
        except: return "N/A", None, None

    # --- 5. IRS DISCOVERY LOGIC ---
    st.title(f"✨ Irfan Recommendation System (IRS) ✨")
    search_query = st.text_input("🔍 Search Movies, Actors, or Directors...")
    mood_map = {"Happy 😊": [35, 16], "Sad 😢": [18, 10749], "Excited 🤩": [28, 12], "Scared 😨": [27, 53]}
    selected_mood = st.selectbox("🎭 Select Your Vibe", ["Select"] + list(mood_map.keys()))

    ready = (media_type != "Select" and sel_lang != "Select" and selected_mood != "Select")

    if st.button("Generate Recommendations 🚀") or search_query:
        if not search_query and not ready:
            st.error("⚠️ Set your Content, Language, and Mood first!")
        else:
            results = []
            today = datetime.now().strftime('%Y-%m-%d')
            if search_query:
                results = list(search_api.multi(search_query))
            else:
                p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.lte': today, 'air_date.lte': today, 'watch_region': 'IN', 'sort_by': 'popularity.desc'}
                m_ids = mood_map.get(selected_mood.split()[0], [])
                if m_ids: p['with_genres'] = "|".join(map(str, m_ids))
                results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

            if results:
                main_cols = st.columns(4)
                processed = 0
                for item in list(results):
                    if processed >= 20: break
                    rd = getattr(item, 'release_date', getattr(item, 'first_air_date', '9999-12-31'))
                    if rd > today or (not is_adult and getattr(item, 'adult', False)): continue

                    cast, ott_n, ott_l = get_detailed_info(item.id, media_type if media_type != "Select" else "Movies")
                    
                    with main_cols[processed % 4]:
                        st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                        st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                        st.subheader(getattr(item, 'title', getattr(item, 'name', ''))[:25])
                        with st.expander("📖 Read Full Plot & Cast"):
                            st.markdown(f"<div class='plot-box'>{getattr(item, 'overview', 'Plot details unavailable.')}</div>", unsafe_allow_html=True)
                            st.write(f"🎭 **Cast:** {cast}")
                            if ott_n:
                                st.success(f"📺 Available on: **{ott_n}**")
                                st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ WATCH ON {ott_n.upper()}</a>', unsafe_allow_html=True)
                            else: st.warning("Streaming unavailable currently.")
                    processed += 1
