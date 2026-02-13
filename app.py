import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests
import random
import pandas as pd

# --- 1. GLOBAL SCALING & SESSIONS ---
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

# --- 2. ADMIN & USER DATABASE (Persistent for this session) ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = [] # Stores login data for Admin view

# --- 3. THEATER UI & STYLING ---
st.set_page_config(page_title="IRS - ICU Admin Control", layout="wide", page_icon="🎬")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    fallback_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{fallback_img}"); background-size: cover; background-attachment: fixed; color: white; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(20%); object-fit: cover; }}
        .play-button {{ background: linear-gradient(45deg, #e50914, #ff4b4b); color: white !important; padding: 12px; border-radius: 10px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: none; }}
        .admin-badge {{ background-color: #ff4b4b; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.8em; border: 1px solid white; }}
        .status-box {{ padding: 10px; border-radius: 10px; background: rgba(255, 255, 255, 0.1); border-left: 5px solid #00ff00; margin-bottom: 20px; }}
        h1, h2, h3, p, span, label, div {{ color: white !important; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION GATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    u_age = st.number_input("Member Age", 1, 100, 18)
    
    if st.button("Access ICU"):
        if u_name:
            # Check for Admin Role
            is_admin = (u_name.lower() == "irfan")
            st.session_state.logged_in = True
            st.session_state.u_name = u_name
            st.session_state.u_age = u_age
            st.session_state.role = "Admin" if is_admin else "Subscriber"
            
            # Save login data to DB (Confidential - Visible only to you)
            st.session_state.user_db.append({
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "User": u_name,
                "Age": u_age,
                "Role": st.session_state.role
            })
            st.rerun()
        else: st.error("Name required.")
else:
    # --- 5. SHARED SIDEBAR NAVIGATION ---
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

    # --- 6. ADMIN COMMAND CENTER (Confidential Data) ---
    if app_mode == "Admin Command Center" and st.session_state.role == "Admin":
        st.title("🛡️ Admin Command Center")
        st.write("---")
        
        tab1, tab2, tab3 = st.tabs(["👥 Member Management", "📊 System Logs", "⚙️ Site Settings"])
        
        with tab1:
            st.subheader("Confidential User Login Data")
            if st.session_state.user_db:
                df = pd.DataFrame(st.session_state.user_db)
                st.table(df) # Only you see this
            else:
                st.info("No logins recorded in this session.")

        with tab2:
            st.subheader("Live Traffic Metrics")
            st.metric("Total Logins", len(st.session_state.user_db))
            st.metric("System Health", "100%", delta="Stable")

        with tab3:
            st.subheader("Global Site Controls")
            st.checkbox("Maintenance Mode", value=False)
            st.checkbox("Disable OTT Links", value=False)
            st.success("Admin changes are local to this session.")

    # --- 7. NORMAL USER PORTAL (Locked for Subscribers) ---
    else:
        # Standard Live Status (Simulated for Subscribers)
        active_users = random.randint(1200, 5000)
        st.sidebar.markdown(f"""
        <div class="status-box">
            <span style='color: #00ff00;'>●</span> <b>Server:</b> Online<br>
            <span style='color: #00ff00;'>●</span> <b>Active Members:</b> {active_users:,}
        </div>
        """, unsafe_allow_html=True)

        media_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
        lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}
        sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))
        eras = ["Select", "2020-2030", "2010-2020", "2000-2010", "1990-2000", "1980-1990"]
        sel_era = st.sidebar.selectbox("Choose Era", eras)

        # Caching logic to bare massive traffic
        @st.cache_data(ttl=3600)
        def get_cached_details(m_id, m_type):
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

        # --- MAIN IRS DASHBOARD ---
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
                    s_year, e_year = map(int, sel_era.split('-'))
                    m_ids = mood_map.get(selected_mood.split()[0], [])
                    p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.gte': f"{s_year}-01-01", 'primary_release_date.lte': f"{e_year}-12-31", 'watch_region': 'IN', 'sort_by': 'popularity.desc', 'with_genres': "|".join(map(str, m_ids))}
                    results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

                if results:
                    cols = st.columns(4)
                    processed = 0
                    for item in results:
                        if processed >= 100: break
                        rd_str = getattr(item, 'release_date', getattr(item, 'first_air_date', ''))
                        if not rd_str: continue
                        
                        item_year = int(rd_str.split('-')[0])
                        if not search_query and (item_year < s_year or item_year > e_year): continue
                        if datetime.strptime(rd_str, '%Y-%m-%d') > today_obj: continue 

                        cast, ott_n, ott_l, trailer = get_cached_details(item.id, media_type if media_type != "Select" else "Movies")
                        if not ott_n: continue # Strict OTT Filter

                        with cols[processed % 4]:
                            st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                            st.subheader(f"{getattr(item, 'title', getattr(item, 'name', ''))[:20]} ({item_year})")
                            with st.expander("👁️ View Details & Play"):
                                st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                                if ott_n: st.markdown(f"<div class='ott-badge'>📺 {ott_n.upper()}</div>", unsafe_allow_html=True)
                                if trailer: st.video(trailer)
                                if ott_n: st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ ONE-CLICK PLAY</a>', unsafe_allow_html=True)
                        processed += 1
            except Exception as e: st.error(f"Error: {e}")
