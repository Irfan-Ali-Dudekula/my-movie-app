import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 2. PAGE SETUP & THEME ---
st.set_page_config(page_title="Irfan Recommendation System (IRS)", layout="wide", page_icon="🎬")

def set_imax_ui():
    bg_img = "http://googleusercontent.com/image_generation_content/0b8b6c4b-4395-467f-8f85-1d0413009623.png"
    overlay = "rgba(0, 0, 0, 0.85)"
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient({overlay}, {overlay}), url("{bg_img}");
            background-size: cover; background-attachment: fixed; color: #FFFFFF;
        }}
        .ceiling-lights {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100px;
            background: radial-gradient(circle, rgba(0, 191, 255, 0.9) 1.5px, transparent 1.5px);
            background-size: 30px 30px; z-index: 100; animation: twinkle 3s infinite ease-in-out;
        }}
        @keyframes twinkle {{ 0%, 100% {{ opacity: 0.3; }} 50% {{ opacity: 0.8; }} }}
        .ott-link {{ background-color: #e50914; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; }}
        .rating-box {{ background-color: #f5c518; color: #000; padding: 4px 8px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 8px; }}
        .rank-badge {{ position: absolute; top: 10px; left: 10px; background: rgba(229, 9, 20, 0.9); color: white; padding: 5px 12px; border-radius: 50%; font-weight: bold; font-size: 1.2em; z-index: 10; border: 2px solid white; }}
        h1, h2, h3, p, span, label, .stMarkdown {{ color: #FFFFFF !important; }}
        </style>
        <div class="ceiling-lights"></div>
        """, unsafe_allow_html=True)

# --- 3. SESSION INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'watchlist' not in st.session_state: st.session_state.watchlist = []

# --- 4. LOGIN GATE (ICU) ---
if not st.session_state.logged_in:
    set_imax_ui()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name")
    u_age = st.number_input("Member Age", 1, 100, 18)
    if st.button("Access ICU"):
        if u_name:
            st.session_state.logged_in, st.session_state.u_name, st.session_state.u_age = True, u_name, u_age
            st.rerun()
        else: st.error("Name required.")
else:
    # --- 5. MAIN DASHBOARD (IRS) ---
    st.sidebar.title(f"👤 {st.session_state.u_name}")
    set_imax_ui()
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.subheader("Watchlist 📌")
    if st.session_state.watchlist:
        for item in st.session_state.watchlist: st.sidebar.write(f"- {item}")
    else: st.sidebar.info("Your list is empty.")

    media_type = st.sidebar.selectbox("Content Type", ["Select", "Movies", "TV Shows"])
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Korean": "ko"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))

    def get_detailed_info(m_id, m_type):
        try:
            res = movie_api.details(m_id, append_to_response="credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="credits,watch/providers")
            cast = ", ".join([c['name'] for c in res.get('credits', {}).get('cast', [])[:5]])
            providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
            ott_n, ott_l = (providers['flatrate'][0]['provider_name'], providers.get('link')) if 'flatrate' in providers else (None, None)
            return cast, ott_n, ott_l
        except: return "N/A", None, None

    # --- 6. INTERFACE ---
    st.title(f"✨ Irfan Recommendation System (IRS)")
    search_query = st.text_input("🔍 Search Movies, TV Shows, Actors, or Directors...")
    mood_map = {"Happy 😊": [35, 16], "Sad 😢": [18, 10749], "Excited 🤩": [28, 12], "Scared 😨": [27, 53]}
    selected_mood = st.selectbox("🎭 Select Mood", ["Select"] + list(mood_map.keys()))

    ready = (media_type != "Select" and sel_lang != "Select" and selected_mood != "Select")

    if st.button("Generate IRS Report 🚀") or search_query:
        if not search_query and not ready:
            st.error("⚠️ Complete filters first.")
        else:
            results = []
            today = datetime.now()
            today_str = today.strftime('%Y-%m-%d')
            
            if search_query:
                results = list(search_api.multi(search_query))
            else:
                m_ids = mood_map.get(selected_mood.split()[0], [])
                genre_string = "|".join(map(str, m_ids)) if m_ids else None
                for page in range(1, 6):
                    p = {'with_original_language': lang_map[sel_lang], 'primary_release_date.lte': today_str, 'air_date.lte': today_str, 'watch_region': 'IN', 'sort_by': 'popularity.desc', 'with_genres': genre_string, 'page': page}
                    page_data = list(discover_api.discover_movies(p) if media_type == "Movies" else discover_api.discover_tv_shows(p))
                    results.extend(page_data)
                    if len(results) >= 100: break

            if results:
                main_cols = st.columns(4)
                processed = 0
                for i, item in enumerate(results):
                    if processed >= 100: break
                    if isinstance(item, str): continue
                    
                    rd_str = getattr(item, 'release_date', getattr(item, 'first_air_date', '9999-12-31'))
                    if rd_str > today_str or (st.session_state.u_age < 18 and getattr(item, 'adult', False)): continue

                    cast, ott_n, ott_l = get_detailed_info(item.id, media_type if media_type != "Select" else "Movies")
                    
                    with main_cols[processed % 4]:
                        st.markdown(f'<div style="position: relative;">', unsafe_allow_html=True)
                        if processed < 10: st.markdown(f'<div class="rank-badge">#{processed+1}</div>', unsafe_allow_html=True)
                        st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        vote_avg = getattr(item, 'vote_average', 0)
                        st.markdown(f"<div class='rating-box'>⭐ IMDb {vote_avg:.1f}/10</div>", unsafe_allow_html=True)
                        title = getattr(item, 'title', getattr(item, 'name', ''))
                        st.subheader(title[:25])
                        
                        # Just Arrived Check (Released in last 30 days)
                        try:
                            rd_obj = datetime.strptime(rd_str, '%Y-%m-%d')
                            if today - rd_obj < timedelta(days=30): st.warning("🆕 Just Arrived on OTT")
                        except: pass

                        with st.expander("📖 Story & Cast"):
                            st.write(getattr(item, 'overview', 'Plot unavailable.'))
                            st.write(f"🎭 **Cast:** {cast}")
                            if st.button(f"Add to Watchlist", key=f"btn_{item.id}"):
                                if title not in st.session_state.watchlist:
                                    st.session_state.watchlist.append(title)
                                    st.toast(f"Added {title} to Watchlist!")
                            if ott_n:
                                st.success(f"📺 Watch on: **{ott_n}**")
                                st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ OPEN {ott_n.upper()}</a>', unsafe_allow_html=True)
                    processed += 1
