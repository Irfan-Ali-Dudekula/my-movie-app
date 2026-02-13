import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests

# --- 1. CONFIGURATION ---import streamlit as st
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

# --- 2. PAGE SETUP & BACKGROUND ---
# Updated Title to IRFAN CINEMATIC UNIVERSE (ICU)
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide", page_icon="🎬")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(25%); object-fit: cover; }}
        .ott-link {{ background-color: #e50914; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; font-size: 1.1em; border: 1px solid #ff4b4b; }}
        .cast-text {{ color: #f0ad4e; font-weight: bold; font-size: 0.9em; }}
        .rating-box {{ background-color: #f5c518; color: #000; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 10px; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

set_bg()

# --- 3. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Name")
    u_age = st.number_input("Your Age", 1, 100, 18)
    if st.button("Enter ICU"):
        if u_name:
            st.session_state.logged_in = True
            st.session_state.u_name = u_name
            st.session_state.u_age = u_age
            st.rerun()
        else: st.error("Please enter your name.")
else:
    # --- 4. SIDEBAR ---
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    is_adult = st.session_state.u_age >= 18
    st.sidebar.markdown("<div style='font-size:0.8em; color:#ccc;'>Powered by TMDB API</div>", unsafe_allow_html=True)

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # Default is "Select" to prevent auto-recommendation
    media_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Korean": "ko"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))

    # --- 5. DATA HELPERS ---
    def get_safe_val(item, key, default=None):
        if isinstance(item, dict): return item.get(key, default)
        try: return getattr(item, key, default)
        except: return default

    def get_detailed_info(m_id, m_type):
        try:
            res = movie_api.details(m_id, append_to_response="credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="credits,watch/providers")
            cast_list = [c['name'] for c in res.get('credits', {}).get('cast', [])[:5]]
            cast_str = ", ".join(cast_list) if cast_list else "N/A"
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            ott_name, ott_link = None, None
            if 'flatrate' in providers:
                ott_name = providers['flatrate'][0]['provider_name']
                ott_link = providers.get('link') 
            elif 'ads' in providers:
                ott_name = f"{providers['ads'][0]['provider_name']} (Free)"
                ott_link = providers.get('link')
            return cast_str, ott_name, ott_link
        except: return "N/A", None, None

    # --- 6. DISCOVERY LOGIC ---
    st.title(f"🔍 ICU Discovery Portal")
    search_query = st.text_input("🔍 Search Movies, TV Shows, Actors, or Directors...")
    mood_map = {"Happy": [35, 16], "Sad": [18, 10749], "Excited": [28, 12], "Scared": [27, 53]}
    selected_mood = st.selectbox("🎭 Select Mood", ["Select"] + list(mood_map.keys()))

    # --- UPDATED GATE: Only run if all are selected ---
    ready_to_recommend = (media_type != "Select" and sel_lang != "Select" and selected_mood != "Select")

    if st.button("Generate Recommendations") or search_query:
        if not search_query and not ready_to_recommend:
            st.error("⚠️ Please select a Content Type, Language, and Mood to see recommendations!")
        else:
            results = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            if search_query:
                results = list(search_api.multi(search_query))
            else:
                p = {
                    'with_original_language': lang_map[sel_lang],
                    'primary_release_date.lte': today,
                    'air_date.lte': today,
                    'watch_region': 'IN',
                    'sort_by': 'popularity.desc'
                }
                m_ids = mood_map.get(selected_mood, [])
                if m_ids: p['with_genres'] = "|".join(map(str, m_ids))
                results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

            if results:
                main_cols = st.columns(4)
                processed = 0
                for item in list(results):
                    if processed >= 20: break
                    if isinstance(item, str): continue
                    rd = get_safe_val(item, 'release_date', get_safe_val(item, 'first_air_date', '9999-12-31'))
                    if rd > today or (not is_adult and get_safe_val(item, 'adult', False)): continue

                    cast, ott_n, ott_l = get_detailed_info(get_safe_val(item, 'id'), media_type if media_type != "Select" else "Movies")
                    
                    with main_cols[processed % 4]:
                        st.image(f"https://image.tmdb.org/t/p/w500{get_safe_val(item, 'poster_path')}")
                        vote_avg = get_safe_val(item, 'vote_average', 0)
                        st.markdown(f"<div class='rating-box'>⭐ IMDb {vote_avg:.1f}/10</div>", unsafe_allow_html=True)
                        st.subheader(get_safe_val(item, 'title', get_safe_val(item, 'name', ''))[:25])
                        with st.expander("Details & Streaming"):
                            st.write(f"📖 **Plot:** {get_safe_val(item, 'overview')[:150]}...")
                            st.markdown(f"<p class='cast-text'>🎭 Cast: {cast}</p>", unsafe_allow_html=True)
                            if ott_n:
                                st.success(f"📺 Available on: **{ott_n}**")
                                st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ WATCH ON {ott_n.upper()}</a>', unsafe_allow_html=True)
                            else:
                                st.warning("Streaming link currently unavailable.")
                    processed += 1
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 2. PAGE SETUP & BACKGROUND ---
st.set_page_config(page_title="CinemaPro India", layout="wide", page_icon="🎬")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(25%); object-fit: cover; }}
        .ott-link {{ background-color: #e50914; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; font-size: 1.1em; border: 1px solid #ff4b4b; }}
        .cast-text {{ color: #f0ad4e; font-weight: bold; font-size: 0.9em; }}
        /* Highlight for the IMDb Rating */
        .rating-box {{
            background-color: #f5c518;
            color: #000;
            padding: 4px 8px;
            border-radius: 5px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 10px;
        }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

set_bg()

# --- 3. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🎬 CinemaPro India")
    u_name = st.text_input("Name")
    u_age = st.number_input("Your Age", 1, 100, 18)
    if st.button("Enter Website"):
        if u_name:
            st.session_state.logged_in = True
            st.session_state.u_name = u_name
            st.session_state.u_age = u_age
            st.rerun()
        else: st.error("Please enter your name.")
else:
    # --- 4. SIDEBAR ---
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    is_adult = st.session_state.u_age >= 18
    st.sidebar.markdown("<div style='font-size:0.8em; color:#ccc;'>Powered by TMDB API</div>", unsafe_allow_html=True)

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Korean": "ko"}
    sel_lang = st.sidebar.selectbox("Language", list(lang_map.keys()))

    # --- 5. DATA HELPERS ---
    def get_safe_val(item, key, default=None):
        if isinstance(item, dict): return item.get(key, default)
        try: return getattr(item, key, default)
        except: return default

    def get_detailed_info(m_id, m_type):
        try:
            res = movie_api.details(m_id, append_to_response="credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="credits,watch/providers")
            cast_list = [c['name'] for c in res.get('credits', {}).get('cast', [])[:5]]
            cast_str = ", ".join(cast_list) if cast_list else "N/A"
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            ott_name, ott_link = None, None
            if 'flatrate' in providers:
                ott_name = providers['flatrate'][0]['provider_name']
                ott_link = providers.get('link') 
            elif 'ads' in providers:
                ott_name = f"{providers['ads'][0]['provider_name']} (Free)"
                ott_link = providers.get('link')
            return cast_str, ott_name, ott_link
        except: return "N/A", None, None

    # --- 6. DISCOVERY LOGIC ---
    st.title(f"🔍 OTT-Ready {sel_lang} {media_type}")
    search_query = st.text_input("🔍 Search Movies, Actors, or Directors...")
    mood_map = {"Happy": [35, 16], "Sad": [18, 10749], "Excited": [28, 12], "Scared": [27, 53]}
    selected_mood = st.selectbox("🎭 Mood Selection", ["None"] + list(mood_map.keys()))

    if st.button("Find Available Shows") or search_query:
        results = []
        today = datetime.now().strftime('%Y-%m-%d')
        p = {
            'with_original_language': lang_map[sel_lang],
            'primary_release_date.lte': today,
            'air_date.lte': today,
            'watch_region': 'IN',
            'sort_by': 'popularity.desc'
        }

        if search_query:
            results = list(search_api.multi(search_query))
        else:
            m_ids = mood_map.get(selected_mood, [])
            if m_ids: p['with_genres'] = "|".join(map(str, m_ids))
            results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

        if not results:
            st.warning("No exact matches found. Showing popular choices instead!")
            p.pop('with_genres', None)
            results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

        if results:
            main_cols = st.columns(4)
            processed = 0
            for item in list(results):
                if processed >= 20: break
                if isinstance(item, str): continue
                
                rd = get_safe_val(item, 'release_date', get_safe_val(item, 'first_air_date', '9999-12-31'))
                if rd > today or (not is_adult and get_safe_val(item, 'adult', False)): continue

                cast, ott_n, ott_l = get_detailed_info(get_safe_val(item, 'id'), media_type)
                
                with main_cols[processed % 4]:
                    st.image(f"https://image.tmdb.org/t/p/w500{get_safe_val(item, 'poster_path')}")
                    
                    # Highlighted IMDb Rating Box
                    vote_avg = get_safe_val(item, 'vote_average', 0)
                    st.markdown(f"<div class='rating-box'>⭐ IMDb {vote_avg:.1f}/10</div>", unsafe_allow_html=True)
                    
                    st.subheader(get_safe_val(item, 'title', get_safe_val(item, 'name', ''))[:25])
                    with st.expander("Details & Streaming"):
                        st.write(f"📖 **Plot:** {get_safe_val(item, 'overview')[:150]}...")
                        st.markdown(f"<p class='cast-text'>🎭 Cast: {cast}</p>", unsafe_allow_html=True)
                        if ott_n:
                            st.success(f"📺 Available on: **{ott_n}**")
                            st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ WATCH ON {ott_n.upper()}</a>', unsafe_allow_html=True)
                        else:
                            st.warning("Streaming link currently unavailable.")
                processed += 1
