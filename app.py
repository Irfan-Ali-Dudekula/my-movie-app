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

# --- 2. PAGE SETUP & BACKGROUND (Extracted from your code) ---
st.set_page_config(page_title="Irfan Recommendation System (IRS)", layout="wide", page_icon="🎬")

def set_bg():
    # Extracted background image and video URLs
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    
    st.markdown(f"""
        <style>
        .stApp {{ 
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("{fallback_img}"); 
            background-size: cover; 
            background-attachment: fixed; 
        }}
        #bg-video {{ 
            position: fixed; right: 0; bottom: 0; 
            min-width: 100%; min-height: 100%; 
            z-index: -1; filter: brightness(25%); 
            object-fit: cover; 
        }}
        .ott-link {{ 
            background-color: #e50914; color: white !important; 
            padding: 12px; border-radius: 8px; 
            text-decoration: none; display: block; 
            text-align: center; font-weight: bold; 
            font-size: 1.1em; border: 1px solid #ff4b4b; 
        }}
        .cast-text {{ color: #f0ad4e; font-weight: bold; font-size: 0.9em; }}
        .rating-box {{
            background-color: #f5c518;
            color: #000;
            padding: 4px 8px;
            border-radius: 5px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 10px;
        }}
        /* LED Ceiling Decoration mimicking IMAX style */
        .ceiling-lights {{
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100px;
            background: radial-gradient(circle, rgba(0, 191, 255, 0.9) 1.5px, transparent 1.5px);
            background-size: 30px 30px;
            z-index: 100;
            filter: drop-shadow(0 0 5px rgba(0, 191, 255, 0.5));
            animation: twinkle 3s infinite ease-in-out;
        }}
        @keyframes twinkle {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 0.8; }}
        }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        <div class="ceiling-lights"></div>
        """, unsafe_allow_html=True)

# --- 3. LOGIN GATE (ICU) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name")
    u_age = st.number_input("Member Age", 1, 100, 18)
    if st.button("Enter ICU"):
        if u_name:
            st.session_state.logged_in = True
            st.session_state.u_name = u_name
            st.session_state.u_age = u_age
            st.rerun()
        else: st.error("Access Denied: Please enter your name.")
else:
    # --- 4. MAIN INTERFACE (IRS) ---
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    set_bg() # Background persists from extracted configuration
    
    is_adult = st.session_state.u_age >= 18
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    media_type = st.sidebar.selectbox("Content Type 📺", ["Select", "Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Korean": "ko"}
    sel_lang = st.sidebar.selectbox("Language 🌍", ["Select"] + list(lang_map.keys()))

    # --- 5. DATA HELPERS ---
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

    # --- 6. IRS DISCOVERY LOGIC ---
    st.title(f"✨ Irfan Recommendation System (IRS) ✨")
    search_query = st.text_input("🔍 Search Movies, TV Shows, Actors, or Directors...")
    mood_map = {"Happy 😊": [35, 16], "Sad 😢": [18, 10749], "Excited 🤩": [28, 12], "Scared 😨": [27, 53]}
    selected_mood = st.selectbox("🎭 Select Mood", ["Select"] + list(mood_map.keys()))

    ready = (media_type != "Select" and sel_lang != "Select" and selected_mood != "Select")

    if st.button("Generate Recommendations 🚀") or search_query:
        if not search_query and not ready:
            st.error("⚠️ ICU Protocol: Filters incomplete.")
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
                    if isinstance(item, str): continue
                    rd = getattr(item, 'release_date', getattr(item, 'first_air_date', '9999-12-31'))
                    if rd > today or (not is_adult and getattr(item, 'adult', False)): continue

                    cast, ott_n, ott_l = get_detailed_info(item.id, media_type if media_type != "Select" else "Movies")
                    
                    with main_cols[processed % 4]:
                        st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                        st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                        st.subheader(getattr(item, 'title', getattr(item, 'name', ''))[:25])
                        with st.expander("📖 Full Plot & Cast"):
                            st.write(getattr(item, 'overview', 'Plot details unavailable.'))
                            st.markdown(f"<p class='cast-text'>🎭 Cast: {cast}</p>", unsafe_allow_html=True)
                            if ott_n:
                                st.success(f"📺 Watch on: **{ott_n}**")
                                st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ OPEN {ott_n.upper()}</a>', unsafe_allow_html=True)
                    processed += 1
