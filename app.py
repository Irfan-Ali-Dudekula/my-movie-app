import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime

# --- 1. CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 2. PAGE SETUP & BACKGROUND ---
st.set_page_config(page_title="CinemaPro India", layout="wide", page_icon="🎬")

def set_bg():
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                        url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070&auto=format&fit=crop");
            background-attachment: fixed;
            background-size: cover;
        }}
        .ott-link {{ background-color: #28a745; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; }}
        .tmdb-attribution {{ font-size: 0.8em; color: #ccc; margin-top: 20px; border-top: 1px solid #444; padding-top: 10px; }}
        </style>
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
        else:
            st.error("Please enter your name.")
else:
    # --- 4. MAIN APP CONTENT ---
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    is_adult = st.session_state.u_age >= 18
    
    # --- TMDB CREDITS SECTION ---
    # This section fulfills the attribution requirement for using TMDB data
    st.sidebar.markdown("""
        <div class="tmdb-attribution">
            <img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_1-5bdc75aae11efab7ee0aa2105058f1092ec95c6453055f77118921d84012f55a.svg" width="60">
            <p style='margin-top: 10px;'>This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
        </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}
    sel_lang = st.sidebar.selectbox("Language", list(lang_map.keys()))

    # --- 5. DATA HELPERS ---
    def get_safe_val(item, key, default=None):
        if isinstance(item, dict): return item.get(key, default)
        try: return getattr(item, key, default)
        except: return default

    def get_detailed_info(m_id, m_type):
        try:
            res = movie_api.details(m_id, append_to_response="videos,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="videos,watch/providers")
            trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in res.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), None)
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            ott_n = providers.get('flatrate', [{}])[0].get('provider_name', "Theaters/Rent")
            ott_l = providers.get('link', '#')
            rt = f"{res.get('runtime')} mins" if m_type == "Movies" else f"{res.get('episode_run_time', ['N/A'])[0]} mins/ep"
            return trailer, ott_n, ott_l, rt
        except: return None, "N/A", "#", "N/A"

    # --- 6. TRENDING ---
    st.title(f"🔥 Trending in India")
    trending = list(trending_api.movie_day() if media_type == "Movies" else trending_api.tv_day())
    t_cols = st.columns(6)
    for i, item in enumerate(trending[:6]):
        if isinstance(item, str): continue
        poster = get_safe_val(item, 'poster_path')
        if poster:
            with t_cols[i]:
                st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                st.caption(get_safe_val(item, 'title', get_safe_val(item, 'name', '')))

    st.divider()

    # --- 7. UNIVERSAL SEARCH & MOOD ---
    st.header("🎯 Universal Search & Mood")
    search_query = st.text_input("🔍 Search for Movies, TV Shows, Actors, or Directors...", placeholder="e.g. Prabhas, S.S. Rajamouli, or Salaar")
    
    mood_map = {
        "Happy (Comedy/Animation)": [35, 16],
        "Sad (Drama/Romance)": [18, 10749],
        "Excited (Action/Adventure)": [28, 12],
        "Scared (Horror/Thriller)": [27, 53]
    }
    selected_mood = st.selectbox("🎭 Select your Mood", ["None"] + list(mood_map.keys()))

    if st.button("Find Content") or search_query:
        results = []
        if search_query:
            search_data = search_api.multi(search_query)
            for res in search_data:
                if get_safe_val(res, 'media_type') == 'person':
                    results.extend(get_safe_val(res, 'known_for', []))
                else:
                    results.append(res)
        else:
            mood_ids = mood_map.get(selected_mood, [])
            params = {'with_genres': ",".join(map(str, mood_ids)) if mood_ids else None, 'with_original_language': lang_map[sel_lang]}
            results = list(discover_api.discover_movies(params) if media_type == "Movies" else discover_api.discover_tv_shows(params))

        if results:
            main_cols = st.columns(4)
            for i, item in enumerate(list(results)[:20]):
                if isinstance(item, str): continue
                if not is_adult and get_safe_val(item, 'adult', False): continue
                
                poster = get_safe_val(item, 'poster_path')
                if poster:
                    with main_cols[i % 4]:
                        st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                        st.subheader(get_safe_val(item, 'title', get_safe_val(item, 'name', '')))
                        with st.expander("Details & Watch"):
                            trailer, ott_n, ott_l, rt = get_detailed_info(get_safe_val(item, 'id'), media_type)
                            st.write(f"⏳ **Runtime:** {rt} | ⭐ **Rating:** {get_safe_val(item, 'vote_average')}")
                            st.write(get_safe_val(item, 'overview'))
                            if trailer: st.video(trailer)
                            if ott_l != "#": st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">Watch on {ott_n}</a>', unsafe_allow_html=True)
