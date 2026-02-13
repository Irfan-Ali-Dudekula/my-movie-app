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
st.set_page_config(page_title="Irfan Recommendation System (IRS)", layout="wide", page_icon="🎬")

def set_imax_ui():
    bg_img = "http://googleusercontent.com/image_generation_content/0b8b6c4b-4395-467f-8f85-1d0413009623.png"
    overlay = "rgba(0, 0, 0, 0.85)"
    text_color = "#FFFFFF"

    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient({overlay}, {overlay}), url("{bg_img}");
            background-size: cover; background-attachment: fixed; color: {text_color};
        }}
        .ceiling-lights {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100px;
            background: radial-gradient(circle, rgba(0, 191, 255, 0.9) 1.5px, transparent 1.5px);
            background-size: 30px 30px; z-index: 100; animation: twinkle 3s infinite ease-in-out;
        }}
        @keyframes twinkle {{ 0%, 100% {{ opacity: 0.3; }} 50% {{ opacity: 0.8; }} }}
        .ott-link {{ background-color: #e50914; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
        .rating-box {{ background-color: #f5c518; color: #000; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 8px; }}
        h1, h2, h3, p, span, label, .stMarkdown {{ color: {text_color} !important; }}
        </style>
        <div class="ceiling-lights"></div>
        """, unsafe_allow_html=True)

# --- 3. LOGIN GATE (ICU) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    set_imax_ui()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name")
    u_age = st.number_input("Member Age", 1, 100, 18)
    if st.button("Access ICU"):
        if u_name:
            st.session_state.logged_in = True
            st.session_state.u_name = u_name
            st.session_state.u_age = u_age
            st.rerun()
        else: st.error("Name required.")
else:
    # --- 4. MAIN DASHBOARD (IRS) ---
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    set_imax_ui()
    
    is_adult = st.session_state.u_age >= 18
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    media_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Korean": "ko"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))

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

    # --- 6. IRS DISCOVERY (100 Results + Fallback) ---
    st.title(f"✨ Irfan Recommendation System (IRS)")
    search_query = st.text_input("🔍 Search Movies, TV Shows, Actors, or Directors...")
    mood_map = {"Happy 😊": [35, 16], "Sad 😢": [18, 10749], "Excited 🤩": [28, 12], "Scared 😨": [27, 53]}
    selected_mood = st.selectbox("🎭 Select Mood", ["Select"] + list(mood_map.keys()))

    # Conditional logic: Must select all 3
    ready = (media_type != "Select" and sel_lang != "Select" and selected_mood != "Select")

    if st.button("Generate IRS Report 🚀") or search_query:
        if not search_query and not ready:
            st.error("⚠️ ICU Protocol: Please select Content Type, Language, and Mood!")
        else:
            results = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            try:
                if search_query:
                    results = list(search_api.multi(search_query))
                else:
                    m_ids = mood_map.get(selected_mood, [])
                    genre_string = "|".join(map(str, m_ids)) if m_ids else None
                    
                    # Fetching up to 100 movies
                    for page in range(1, 6):
                        p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.lte': today, 'air_date.lte': today, 'watch_region': 'IN', 'sort_by': 'popularity.desc', 'with_genres': genre_string, 'page': page}
                        page_data = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))
                        results.extend(page_data)
                        if len(results) >= 100: break

                # FALLBACK: If strict filters yield nothing, try a general search
                if not results:
                    st.warning("No exact matches in India. Expanding search globally...")
                    p.pop('with_genres', None)
                    p.pop('watch_region', None)
                    results = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))

                if results:
                    main_cols = st.columns(4)
                    processed = 0
                    for item in results:
                        if processed >= 100: break
                        if isinstance(item, str): continue
                        rd = getattr(item, 'release_date', getattr(item, 'first_air_date', '9999-12-31'))
                        if rd > today or (not is_adult and getattr(item, 'adult', False)): continue

                        cast, ott_n, ott_l = get_detailed_info(item.id, media_type if media_type != "Select" else "Movies")
                        
                        with main_cols[processed % 4]:
                            st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                            st.markdown(f"<div class='rating-box'>⭐ IMDb {getattr(item, 'vote_average', 0):.1f}/10</div>", unsafe_allow_html=True)
                            st.subheader(getattr(item, 'title', getattr(item, 'name', ''))[:25])
                            with st.expander("📖 Story & Cast"):
                                st.write(getattr(item, 'overview', 'Plot unavailable.'))
                                st.write(f"🎭 **Cast:** {cast}")
                                if ott_n:
                                    st.success(f"📺 Watch on: **{ott_n}**")
                                    st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ OPEN {ott_n.upper()}</a>', unsafe_allow_html=True)
                        processed += 1
                else:
                    st.error("No results found. Please check your API key or internet connection.")
            except Exception as e:
                st.error(f"IRS Error: {e}")
