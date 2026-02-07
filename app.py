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
        .ott-link:hover {{ background-color: #b20710; transition: 0.3s; }}
        .cast-text {{ color: #f0ad4e; font-weight: bold; font-size: 0.9em; }}
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
    
    st.sidebar.markdown("""<div style='font-size:0.8em; color:#ccc;'><img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_square_1-5bdc75aae11efab7ee0aa2105058f1092ec95c6453055f77118921d84012f55a.svg" width="50"><br>Powered by TMDB API</div>""", unsafe_allow_html=True)

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Korean": "ko", "Chinese": "zh"}
    sel_lang = st.sidebar.selectbox("Language", list(lang_map.keys()))

    # --- 5. DATA HELPERS ---
    def get_safe_val(item, key, default=None):
        if isinstance(item, dict): return item.get(key, default)
        try: return getattr(item, key, default)
        except: return default

    def get_detailed_info(m_id, m_type):
        """Fetches Cast, OTT Providers, and Trailer."""
        try:
            res = movie_api.details(m_id, append_to_response="videos,credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="videos,credits,watch/providers")
            
            # 1. Cast Details (First 5 members)
            cast_list = [c['name'] for c in res.get('credits', {}).get('cast', [])[:5]]
            cast_str = ", ".join(cast_list) if cast_list else "Not Available"
            
            # 2. OTT Detection (Strictly streaming apps/YouTube)
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            ott_name, ott_link = "Not Available for Streaming", None
            
            # Preference: Flatrate (Subscriptions like Netflix/Hotstar) then Ads (YouTube)
            if 'flatrate' in providers:
                ott_name = providers['flatrate'][0]['provider_name']
                # TMDB 'link' goes to TMDB. We try to find the direct provider link if available, 
                # but API usually provides a TMDB deep link. We use the TMDB link as it redirects to the app.
                ott_link = providers.get('link') 
            elif 'ads' in providers:
                ott_name = f"{providers['ads'][0]['provider_name']} (Free with Ads)"
                ott_link = providers.get('link')
                
            rt = f"{res.get('runtime', 'N/A')} mins" if m_type == "Movies" else f"Episodes available"
            return cast_str, ott_name, ott_link, rt
        except: return "N/A", "N/A", None, "N/A"

    # --- 6. TRENDING & DISCOVERY ---
    st.title(f"🔥 Trending {sel_lang} {media_type}")
    
    search_query = st.text_input("🔍 Search Movies, TV Shows, Actors, or Directors...")
    mood_map = {"Happy": [35, 16], "Sad": [18, 10749], "Excited": [28, 12], "Scared": [27, 53]}
    selected_mood = st.selectbox("🎭 Mood Selection", ["None"] + list(mood_map.keys()))

    if st.button("Generate Recommendations") or search_query:
        results = []
        if search_query:
            search_data = search_api.multi(search_query)
            for res in search_data:
                if get_safe_val(res, 'media_type') == 'person': results.extend(get_safe_val(res, 'known_for', []))
                else: results.append(res)
        else:
            m_ids = mood_map.get(selected_mood, [])
            g_str = "|".join(map(str, m_ids)) if m_ids else None
            p = {'with_genres': g_str, 'with_original_language': lang_map[sel_lang], 'sort_by': 'popularity.desc'}
            results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

        if results:
            main_cols = st.columns(4)
            processed = 0
            for item in list(results):
                if processed >= 20: break
                if isinstance(item, str): continue
                if not is_adult and get_safe_val(item, 'adult', False): continue
                
                poster = get_safe_val(item, 'poster_path')
                if poster:
                    with main_cols[processed % 4]:
                        st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                        title = get_safe_val(item, 'title', get_safe_val(item, 'name', ''))
                        st.subheader(title[:25])
                        
                        # Requirement 1 & 2: Cast & OTT in Expander
                        with st.expander("Description & Cast"):
                            cast, ott_n, ott_l, rt = get_detailed_info(get_safe_val(item, 'id'), media_type)
                            st.write(f"📖 **Plot:** {get_safe_val(item, 'overview')[:200]}...")
                            st.markdown(f"<p class='cast-text'>🎭 Cast: {cast}</p>", unsafe_allow_html=True)
                            st.info(f"📺 Available on: **{ott_n}**")
                            
                            # Requirement 3: Watch Button with Redirect
                            if ott_l:
                                st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ WATCH NOW ON {ott_n.upper()}</a>', unsafe_allow_html=True)
                            else:
                                st.warning("Direct watch link unavailable")
                    processed += 1
