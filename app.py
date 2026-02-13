import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests

# --- 1. GLOBAL SESSION FIX (Stops Script Execution Error) ---
# This reuses one connection for all requests, preventing [Errno 24]
if 'http_session' not in st.session_state:
    st.session_state.http_session = requests.Session()

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 2. PAGE SETUP & UI ---
st.set_page_config(page_title="Irfan Recommendation System (IRS)", layout="wide", page_icon="🎬")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; color: white; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(20%); object-fit: cover; }}
        .play-button {{ background: linear-gradient(45deg, #e50914, #ff4b4b); color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: none; }}
        .rating-box {{ background-color: #f5c518; color: #000; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 5px; }}
        .ott-badge {{ background-color: #28a745; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; }}
        h1, h2, h3, p, span, label, div {{ color: white !important; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

# --- 3. LOGIN GATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name")
    u_age = st.number_input("Member Age", 1, 100, 18)
    if st.button("Enter ICU"):
        if u_name:
            st.session_state.logged_in, st.session_state.u_name, st.session_state.u_age = True, u_name, u_age
            st.rerun()
else:
    # --- 4. MAIN INTERFACE ---
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    media_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))
    sel_era = st.sidebar.selectbox("Choose Era", ["Select", "2020-2030", "2010-2020", "2000-2010", "1990-2000"])

    def get_detailed_info(m_id, m_type):
        try:
            res = movie_api.details(m_id, append_to_response="credits,watch/providers,videos") if m_type == "Movies" else tv_api.details(m_id, append_to_response="credits,watch/providers,videos")
            cast = ", ".join([c['name'] for c in res.get('credits', {}).get('cast', [])[:5]])
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            ott_n, ott_l = None, None
            if 'flatrate' in providers:
                ott_n, ott_l = providers['flatrate'][0]['provider_name'], providers.get('link') 
            elif 'ads' in providers:
                ott_n, ott_l = f"{providers['ads'][0]['provider_name']} (Free)", providers.get('link')
            
            trailer = None
            for v in res.get('videos', {}).get('results', []):
                if v['type'] == 'Trailer' and v['site'] == 'YouTube':
                    trailer = f"https://www.youtube.com/watch?v={v['key']}"
                    break
            return cast, ott_n, ott_l, trailer
        except: return "N/A", None, None, None

    # --- 5. IRS DASHBOARD ---
    set_bg()
    st.title("✨ Irfan Recommendation System (IRS)")
    search_query = st.text_input("🔍 Search Movies...")
    mood_map = {"Happy 😊": [35, 16], "Sad 😢": [18, 10749], "Excited 🤩": [28, 12], "Scared 😨": [27, 53]}
    selected_mood = st.selectbox("🎭 Select Mood", ["Select"] + list(mood_map.keys()))

    if st.button("Generate Recommendations 🚀") or search_query:
        today_obj = datetime.now()
        results = []
        try:
            if search_query:
                results = list(search_api.multi(search_query))
            elif media_type != "Select" and sel_lang != "Select" and sel_era != "Select":
                s_year, e_year = sel_era.split('-')
                m_ids = mood_map.get(selected_mood.split()[0], [])
                p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.gte': f"{s_year}-01-01", 'primary_release_date.lte': f"{e_year}-12-31", 'watch_region': 'IN', 'sort_by': 'popularity.desc', 'with_genres': "|".join(map(str, m_ids))}
                results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

            if results:
                cols = st.columns(4)
                processed = 0
                for item in results:
                    if processed >= 20: break
                    rd_str = getattr(item, 'release_date', getattr(item, 'first_air_date', ''))
                    if not rd_str or datetime.strptime(rd_str, '%Y-%m-%d') > today_obj: continue

                    cast, ott_n, ott_l, trailer = get_detailed_info(item.id, media_type)
                    if not ott_n: continue # Strict OTT-Only Filter

                    with cols[processed % 4]:
                        st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                        st.subheader(getattr(item, 'title', getattr(item, 'name', ''))[:20])
                        with st.expander("Details & Watch"):
                            st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                            if trailer: st.video(trailer)
                            st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ ONE-CLICK PLAY</a>', unsafe_allow_html=True)
                    processed += 1
        except Exception as e: st.error(f"Error: {e}")
