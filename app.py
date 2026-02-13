import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests
import random
import pandas as pd

# --- 1. THE PERMANENT FIX: CONNECTION POOLING ---
# We use st.cache_resource to create ONE session that lives forever.
# This prevents the "Too many open files" error.
@st.cache_resource
def get_tmdb_session():
    session = requests.Session()
    # Allowing up to 500 simultaneous connections without crashing
    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=500)
    session.mount('https://', adapter)
    return session

# Initialize TMDB
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 2. ADMIN DATABASE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = []

# --- 3. UI & BACKGROUND ---
st.set_page_config(page_title="IRS - ICU Lifetime Edition", layout="wide", page_icon="🎬")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; color: white; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(20%); object-fit: cover; }}
        .play-button {{ background: linear-gradient(45deg, #e50914, #ff4b4b); color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: none; }}
        .admin-badge {{ background-color: #ff4b4b; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.8em; border: 1px solid white; }}
        .rating-box {{ background-color: #f5c518; color: #000; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 5px; }}
        .ott-badge {{ background-color: #28a745; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; }}
        h1, h2, h3, p, span, label, div {{ color: white !important; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

# --- 4. SECURE ADMIN LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    u_age = st.number_input("Member Age", 1, 100, 18)
    
    admin_key = ""
    if u_name.lower() == "irfan":
        admin_key = st.text_input("Security Key (Admin Only)", type="password")

    if st.button("Access ICU"):
        if u_name:
            if u_name.lower() == "irfan":
                if admin_key == "irfan@123": # Your secure password
                    st.session_state.role = "Admin"
                else:
                    st.error("Invalid Security Key!")
                    st.stop()
            else:
                st.session_state.role = "Subscriber"

            st.session_state.logged_in = True
            st.session_state.u_name = u_name
            st.session_state.user_db.append({"Time": datetime.now().strftime("%H:%M:%S"), "User": u_name, "Role": st.session_state.role})
            st.rerun()
else:
    # --- 5. DASHBOARD NAVIGATION ---
    set_bg()
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    
    if st.session_state.role == "Admin":
        st.sidebar.markdown("<span class='admin-badge'>SYSTEM ADMIN</span>", unsafe_allow_html=True)
        app_mode = st.sidebar.radio("Navigation", ["User Portal", "Admin Command Center"])
    else:
        app_mode = "User Portal"

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # --- 6. ADMIN CENTER (Confidential Data) ---
    if app_mode == "Admin Command Center" and st.session_state.role == "Admin":
        st.title("🛡️ Admin Command Center")
        st.subheader("Confidential Login Registry")
        st.table(pd.DataFrame(st.session_state.user_db))
        st.metric("Total Visitors", len(st.session_state.user_db))

    # --- 7. USER PORTAL ---
    else:
        st.sidebar.markdown(f"**Live Members:** {random.randint(1200, 5000):,}")
        media_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
        lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}
        sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))
        sel_era = st.sidebar.selectbox("Choose Era", ["Select", "2020-2030", "2010-2020", "2000-2010", "1990-2000", "1980-1990"])

        # Caching data to prevent repeat API calls
        @st.cache_data(ttl=3600)
        def get_details(m_id, m_type):
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

        st.title("✨ Irfan Recommendation System (IRS)")
        search_query = st.text_input("🔍 Search Movies...")

        if st.button("Generate Recommendations 🚀") or search_query:
            today = datetime.now()
            results = []
            try:
                if search_query:
                    results = list(search_api.multi(search_query))
                elif media_type != "Select" and sel_lang != "Select" and sel_era != "Select":
                    s_year, e_year = map(int, sel_era.split('-'))
                    p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.gte': f"{s_year}-01-01", 'primary_release_date.lte': f"{e_year}-12-31", 'watch_region': 'IN', 'sort_by': 'popularity.desc'}
                    results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

                if results:
                    cols = st.columns(4)
                    processed = 0
                    for item in results:
                        if processed >= 20: break
                        rd_str = getattr(item, 'release_date', getattr(item, 'first_air_date', ''))
                        if not rd_str: continue
                        
                        # ERA VALIDATION
                        item_year = int(rd_str.split('-')[0])
                        if not search_query and (item_year < s_year or item_year > e_year): continue
                        if datetime.strptime(rd_str, '%Y-%m-%d') > today: continue 

                        cast, ott_n, ott_l, trailer = get_details(item.id, media_type)
                        if not ott_n: continue 

                        with cols[processed % 4]:
                            st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                            st.subheader(f"{getattr(item, 'title', getattr(item, 'name', ''))[:20]} ({item_year})")
                            with st.expander("Details & Watch"):
                                st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                                if trailer: st.video(trailer)
                                st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ ONE-CLICK PLAY</a>', unsafe_allow_html=True)
                        processed += 1
            except Exception as e: st.error(f"IRS Processing Error: {e}")import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests
import random
import pandas as pd

# --- 1. GLOBAL SESSION FIX (Stops Errno 24) ---
@st.cache_resource
def get_tmdb_session():
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=500)
    session.mount('https://', adapter)
    return session

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 2. CONFIDENTIAL DATABASE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = []

# --- 3. THEATER UI & STYLING ---
st.set_page_config(page_title="IRS - Secured Admin Edition", layout="wide", page_icon="🎬")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; color: white; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(20%); object-fit: cover; }}
        .play-button {{ background: linear-gradient(45deg, #e50914, #ff4b4b); color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: none; }}
        .admin-badge {{ background-color: #ff4b4b; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.8em; border: 1px solid white; }}
        .rating-box {{ background-color: #f5c518; color: #000; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 5px; }}
        .ott-badge {{ background-color: #28a745; color: white; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; }}
        h1, h2, h3, p, span, label, div {{ color: white !important; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

# --- 4. SECURE AUTHENTICATION GATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    u_age = st.number_input("Member Age", 1, 100, 18)
    
    # NEW: Admin Password Protection
    admin_key = ""
    if u_name.lower() == "irfan":
        admin_key = st.text_input("Security Key (Admin Only)", type="password")

    if st.button("Access ICU"):
        if u_name:
            # Validate Admin Credentials
            if u_name.lower() == "irfan":
                if admin_key == "irfan@123": # Change this to your preferred password!
                    st.session_state.role = "Admin"
                else:
                    st.error("Invalid Security Key!")
                    st.stop()
            else:
                st.session_state.role = "Subscriber"

            st.session_state.logged_in = True
            st.session_state.u_name = u_name
            st.session_state.user_db.append({
                "Time": datetime.now().strftime("%H:%M:%S"),
                "User": u_name,
                "Role": st.session_state.role
            })
            st.rerun()
        else: st.error("Please enter a name.")
else:
    # --- 5. REALM RECOGNITION ---
    set_bg()
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    
    if st.session_state.role == "Admin":
        st.sidebar.markdown("<span class='admin-badge'>SYSTEM ADMIN</span>", unsafe_allow_html=True)
        app_mode = st.sidebar.radio("Navigation", ["User Portal", "Admin Command Center"])
    else:
        app_mode = "User Portal"

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    # --- 6. ADMIN REALM (Confidential Data) ---
    if app_mode == "Admin Command Center" and st.session_state.role == "Admin":
        st.title("🛡️ Admin Command Center")
        st.subheader("Member Login Registry")
        st.table(pd.DataFrame(st.session_state.user_db))
        st.metric("Total Visitors", len(st.session_state.user_db))
        st.success("You are viewing confidential data hidden from subscribers.")

    # --- 7. SUBSCRIBER PORTAL ---
    else:
        st.sidebar.markdown(f"**Live Members:** {random.randint(1200, 5000):,}")
        media_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
        lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}
        sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))
        sel_era = st.sidebar.selectbox("Choose Era", ["Select", "2020-2030", "2010-2020", "2000-2010", "1990-2000"])

        @st.cache_data(ttl=3600)
        def get_details(m_id, m_type):
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

        st.title("✨ Irfan Recommendation System (IRS)")
        search_query = st.text_input("🔍 Search Movies...")

        if st.button("Generate Recommendations 🚀") or search_query:
            today = datetime.now()
            results = []
            try:
                if search_query:
                    results = list(search_api.multi(search_query))
                elif media_type != "Select" and sel_lang != "Select" and sel_era != "Select":
                    s_year, e_year = map(int, sel_era.split('-'))
                    p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.gte': f"{s_year}-01-01", 'primary_release_date.lte': f"{e_year}-12-31", 'watch_region': 'IN', 'sort_by': 'popularity.desc'}
                    results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

                if results:
                    cols = st.columns(4)
                    processed = 0
                    for item in results:
                        if processed >= 20: break
                        rd_str = getattr(item, 'release_date', getattr(item, 'first_air_date', ''))
                        if not rd_str: continue
                        
                        item_year = int(rd_str.split('-')[0])
                        if not search_query and (item_year < s_year or item_year > e_year): continue
                        if datetime.strptime(rd_str, '%Y-%m-%d') > today: continue 

                        cast, ott_n, ott_l, trailer = get_details(item.id, media_type)
                        if not ott_n: continue 

                        with cols[processed % 4]:
                            st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                            st.subheader(f"{getattr(item, 'title', getattr(item, 'name', ''))[:20]} ({item_year})")
                            with st.expander("Details & Watch"):
                                st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                                if trailer: st.video(trailer)
                                st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ ONE-CLICK PLAY</a>', unsafe_allow_html=True)
                        processed += 1
            except Exception as e: st.error(f"Error: {e}")
