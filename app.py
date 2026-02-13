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

# --- 2. PAGE SETUP & UI ---
st.set_page_config(page_title="Irfan Recommendation System (IRS)", layout="wide", page_icon="🎬")
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

# RECTIFY ERROR: Use a session to prevent "Too many open files"
if 'http_session' not in st.session_state:
    st.session_state.http_session = requests.Session()

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
                ott_n = providers['flatrate'][0]['provider_name']
                ott_l = providers.get('link') 
            elif 'ads' in providers:
                ott_n = f"{providers['ads'][0]['provider_name']} (Free)"
                ott_l = providers.get('link')
            
            trailer_url = None
            for v in res.get('videos', {}).get('results', []):
                if v['type'] == 'Trailer' and v['site'] == 'YouTube':
                    trailer_url = f"https://www.youtube.com/watch?v={v['key']}"
                    break
            return cast, ott_n, ott_l, trailer_url
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
                    rd_str = getattr(item, 'release_date', getattr(item, 'first_air_date', '9999-12-31'))
                    if not rd_str or datetime.strptime(rd_str, '%Y-%m-%d') > today_obj: continue

                    cast, ott_n, ott_l, trailer = get_detailed_info(item.id, media_type)
                    with cols[processed % 4]:
                        st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                        st.subheader(getattr(item, 'title', getattr(item, 'name', ''))[:20])
                        with st.expander("Details & Watch"):
                            st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                            if ott_n: st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                            if trailer: st.video(trailer)
                            if ott_n: st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ ONE-CLICK PLAY</a>', unsafe_allow_html=True)
                    processed += 1
        except Exception as e:
            st.error(f"Error: {e}")
def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; color: white; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(20%); object-fit: cover; }}
        .play-button {{ 
            background: linear-gradient(45deg, #e50914, #ff4b4b); color: white !important; 
            padding: 12px; border-radius: 10px; text-decoration: none; display: block; 
            text-align: center; font-weight: bold; margin-top: 10px; border: none;
        }}
        .rating-box {{ background-color: #f5c518; color: #000; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 5px; }}
        .ott-badge {{ background-color: #28a745; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; }}
        .ceiling-lights {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100px;
            background: radial-gradient(circle, rgba(0, 191, 255, 0.9) 1.5px, transparent 1.5px);
            background-size: 30px 30px; z-index: 100; animation: twinkle 3s infinite ease-in-out;
        }}
        @keyframes twinkle {{ 0%, 100% {{ opacity: 0.3; }} 50% {{ opacity: 0.8; }} }}
        h1, h2, h3, p, span, label, div {{ color: white !important; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        <div class="ceiling-lights"></div>
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
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Korean": "ko"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))
    
    eras = ["Select", "2020-2030", "2010-2020", "2000-2010", "1990-2000", "1980-1990", "1970-1980"]
    sel_era = st.sidebar.selectbox("Choose Era", eras)

    def get_detailed_info(m_id, m_type):
        try:
            res = movie_api.details(m_id, append_to_response="credits,watch/providers,videos") if m_type == "Movies" else tv_api.details(m_id, append_to_response="credits,watch/providers,videos")
            cast = ", ".join([c['name'] for c in res.get('credits', {}).get('cast', [])[:5]])
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            
            ott_n, ott_l = None, None
            if 'flatrate' in providers:
                ott_n = providers['flatrate'][0]['provider_name']
                ott_l = providers.get('link') 
            elif 'ads' in providers:
                ott_n = f"{providers['ads'][0]['provider_name']} (Free)"
                ott_l = providers.get('link')
            
            trailer_url = None
            for video in res.get('videos', {}).get('results', []):
                if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                    trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
                    break
            return cast, ott_n, ott_l, trailer_url
        except: return "N/A", None, None, None

    # --- 5. IRS DASHBOARD ---
    set_bg()
    st.title("✨ Irfan Recommendation System (IRS)")
    search_query = st.text_input("🔍 Search Movies, TV Shows, or Actors...")
    mood_map = {"Happy 😊": [35, 16], "Sad 😢": [18, 10749], "Excited 🤩": [28, 12], "Scared 😨": [27, 53]}
    selected_mood = st.selectbox("🎭 Select Mood", ["Select"] + list(mood_map.keys()))

    ready = (media_type != "Select" and sel_lang != "Select" and selected_mood != "Select" and sel_era != "Select")

    if st.button("Generate Recommendations 🚀") or search_query:
        if not search_query and not ready:
            st.error("⚠️ ICU Protocol: Filters incomplete.")
        else:
            results = []
            today_obj = datetime.now()
            today_str = today_obj.strftime('%Y-%m-%d')
            
            try:
                if search_query:
                    results = list(search_api.multi(search_query))
                else:
                    start_year, end_year = sel_era.split('-')
                    m_ids = mood_map.get(selected_mood.split()[0], [])
                    
                    # Ensure end_date for API is either the era end or "today"
                    api_end_date = today_str if int(end_year) >= today_obj.year else f"{end_year}-12-31"
                    
                    p = {
                        'with_original_language': lang_map[sel_lang], 
                        'primary_release_date.gte': f"{start_year}-01-01", 
                        'primary_release_date.lte': api_end_date, 
                        'watch_region': 'IN', 'sort_by': 'popularity.desc', 
                        'with_genres': "|".join(map(str, m_ids))
                    }
                    
                    for page in range(1, 6):
                        p['page'] = page
                        page_data = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))
                        results.extend(page_data)
                        if len(results) >= 100: break

                if results:
                    main_cols = st.columns(4)
                    processed = 0
                    for item in results:
                        if processed >= 100: break
                        if isinstance(item, str): continue
                        
                        # STRICT RELEASE FILTER: Ignore everything with a future date
                        rd_str = getattr(item, 'release_date', getattr(item, 'first_air_date', '9999-12-31'))
                        if rd_str == "" or rd_str == "9999-12-31": continue # Discard placeholder dates
                        
                        try:
                            rd_obj = datetime.strptime(rd_str, '%Y-%m-%d')
                            if rd_obj > today_obj: continue # Skip unreleased movies/episodes
                        except: continue

                        if not search_query:
                            if rd_str < f"{start_year}-01-01" or rd_str > api_end_date: continue

                        cast, ott_n, ott_l, trailer = get_detailed_info(item.id, media_type if media_type != "Select" else "Movies")
                        
                        with main_cols[processed % 4]:
                            st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                            st.subheader(getattr(item, 'title', getattr(item, 'name', ''))[:20])
                            
                            with st.expander("👁️ View Details & Play"):
                                st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                                if ott_n:
                                    st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                                
                                if trailer: st.video(trailer)
                                else: st.info("Trailer not available.")
                                    
                                st.write(f"🎭 **Cast:** {cast}")
                                st.write(getattr(item, 'overview', ''))
                                
                                if ott_n:
                                    st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ ONE-CLICK PLAY ON {ott_n.upper()}</a>', unsafe_allow_html=True)
                                else:
                                    st.warning("Theater Only or Not on major Indian OTT apps.")
                        processed += 1
            except Exception as e: st.error(f"Error: {e}")
