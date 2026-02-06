import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Genre
from datetime import datetime

# --- 1. CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api, genre_api = Discover(), Trending(), Genre()

# --- 2. PAGE SETUP & CINEMATIC BACKGROUND ---
st.set_page_config(page_title="CinemaPro India", layout="wide", page_icon="🎬")

def set_bg_hack():
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), 
                         url("https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070&auto=format&fit=crop");
             background-attachment: fixed;
             background-size: cover;
         }}
         [data-testid="stSidebar"] {{
             background-color: rgba(20, 20, 20, 0.85);
         }}
         .adult-warning {{ color: white; background-color: #d9534f; font-weight: bold; padding: 10px; border-radius: 5px; text-align: center; margin: 10px 0; font-size: 0.8em; }}
         .info-label {{ color: #f0ad4e; font-weight: bold; font-size: 0.9em; margin-top: 5px; }}
         .ott-label {{ color: #00d4ff; font-weight: bold; font-size: 1em; margin-top: 10px; }}
         .ott-link {{ background-color: #28a745; color: white !important; padding: 12px 20px; border-radius: 8px; text-decoration: none; display: block; margin-top: 15px; font-weight: bold; width: 100%; text-align: center; border: 2px solid #1e7e34; }}
         .ott-link:hover {{ background-color: #218838; border-color: #1c7430; color: white !important; }}
         </style>
         """,
         unsafe_allow_html=True
     )

set_bg_hack()

# --- 3. SIDEBAR & FILTERS ---
st.sidebar.title("👤 User Profile")
name = st.sidebar.text_input("Enter Your Name", "Guest")
age = st.sidebar.number_input("Enter Your Age", 1, 100, 18)
is_adult = age >= 18

st.sidebar.divider()
media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Kannada": "kn"}
sel_lang = st.sidebar.selectbox("Preferred Language", list(lang_map.keys()))
min_rating = st.sidebar.slider("Minimum Rating (⭐)", 0.0, 10.0, 5.0)

# --- 4. DATA HELPER FUNCTIONS ---
def get_safe_val(item, key, default=None):
    if isinstance(item, dict): return item.get(key, default)
    return getattr(item, key, default)

@st.cache_data(ttl=3600)
def get_genres(m_type):
    g_list = genre_api.movie_list() if m_type == "Movies" else genre_api.tv_list()
    return {g['name']: g['id'] for g in g_list}

def get_detailed_info(m_id, m_type):
    trailer, cast_list, director, runtime = None, [], "Unknown", "N/A"
    ott_name, ott_link = "Rent/Theaters", "#"
    try:
        res = movie_api.details(m_id, append_to_response="videos,credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="videos,credits,watch/providers")
        if m_type == "Movies":
            r = res.get('runtime')
            runtime = f"{r} mins" if r else "N/A"
        else:
            r = res.get('episode_run_time', [])
            runtime = f"{r[0]} mins/ep" if r else "N/A"
        for v in res.get('videos', {}).get('results', []):
            if v['site'] == 'YouTube' and v['type'] == 'Trailer':
                trailer = f"https://www.youtube.com/watch?v={v['key']}"
                break
        for actor in res.get('credits', {}).get('cast', [])[:5]:
            cast_list.append({"name": actor['name'], "pic": actor.get('profile_path')})
        crew = res.get('credits', {}).get('crew', [])
        director = next((p['name'] for p in crew if p['job'] in ['Director', 'Executive Producer']), "N/A")
        providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
        if 'flatrate' in providers:
            ott_name = providers['flatrate'][0]['provider_name']
            ott_link = providers.get('link', '#')
    except: pass
    return trailer, ott_name, ott_link, cast_list, director, runtime

# --- 5. TRENDING SECTION ---
st.title("🔥 Trending in India")
trending_results = trending_api.movie_day() if media_type == "Movies" else trending_api.tv_day()
t_cols = st.columns(6)
count = 0
for item in trending_results:
    if count >= 6: break
    if not is_adult and get_safe_val(item, 'adult', False): continue
    poster = get_safe_val(item, 'poster_path')
    if poster:
        with t_cols[count]:
            st.image(f"https://image.tmdb.org/t/p/w500{poster}", use_container_width=True)
            st.caption(get_safe_val(item, 'title', get_safe_val(item, 'name', ''))[:20])
            count += 1
st.divider()

# --- 6. SEARCH, GENRE & MOOD SELECTION ---
st.header("🎯 Explore Cinema")
search_query = st.text_input("🔍 Search by title...", placeholder="e.g. Kalki 2898 AD")

m_col1, m_col2 = st.columns(2)
with m_col1:
    genre_dict = get_genres(media_type)
    selected_genres = st.multiselect("📂 Select Genres", list(genre_dict.keys()))

with m_col2:
    mood_map = {
        "Happy (Comedy/Animation)": [35, 16],
        "Sad (Drama/Romance)": [18, 10749],
        "Excited (Action/Adventure)": [28, 12],
        "Scared (Horror/Thriller)": [27, 53],
        "Bored (Mystery/Sci-Fi)": [96, 878]
    }
    selected_mood = st.selectbox("🎭 Mood Based Recommendations", ["None"] + list(mood_map.keys()))

if st.button("Generate Recommendations") or search_query:
    today = datetime.now().strftime('%Y-%m-%d')
    results = []
    
    if search_query:
        results = movie_api.search(search_query) if media_type == "Movies" else tv_api.search(search_query)
    else:
        genre_ids = [genre_dict[g] for g in selected_genres]
        if selected_mood != "None": genre_ids.extend(mood_map[selected_mood])
        genre_ids = list(set(genre_ids))

        for p in range(1, 4):
            params = {
                'with_genres': ",".join(map(str, genre_ids)) if genre_ids else None,
                'with_original_language': lang_map[sel_lang],
                'page': p, 'include_adult': is_adult, 'vote_average.gte': min_rating,
                'primary_release_date.lte': today if media_type == "Movies" else None
            }
            data = discover_api.discover_movies(params) if media_type == "Movies" else discover_api.discover_tv_shows(params)
            results.extend(data)

    # --- 7. DISPLAY GRID ---
    if results:
        main_cols = st.columns(4)
        processed = 0
        for item in results:
            if processed >= 40: break
            item_is_adult = get_safe_val(item, 'adult', False)
            g_ids = get_safe_val(item, 'genre_ids', [])
            if not is_adult and (item_is_adult or 27 in g_ids or 53 in g_ids): continue
            poster = get_safe_val(item, 'poster_path')
            if poster:
                with main_cols[processed % 4]:
                    st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                    st.subheader(get_safe_val(item, 'title', get_safe_val(item, 'name', '')))
                    if item_is_adult: st.markdown('<div class="adult-warning">🔞 ADULT CONTENT</div>', unsafe_allow_html=True)
                    with st.expander("Show Details & Runtime"):
                        trailer, ott_n, ott_l, cast, d_name, r_time = get_detailed_info(get_safe_val(item, 'id'), media_type)
                        st.markdown(f'<p class="info-label">⏳ Runtime: {r_time}</p>', unsafe_allow_html=True)
                        st.write(f"🎬 **Director:** {d_name} | ⭐ **Rating:** {get_safe_val(item, 'vote_average')}/10")
                        st.write(get_safe_val(item, 'overview'))
                        if cast:
                            st.write("🎭 **Top Cast:**")
                            c_cols = st.columns(5)
                            for idx, a in enumerate(cast):
                                with c_cols[idx]:
                                    if a['pic']: st.image(f"https://image.tmdb.org/t/p/w200{a['pic']}", use_container_width=True)
                                    st.caption(a['name'])
                        if trailer: st.video(trailer)
                        st.markdown(f'<p class="ott-label">📺 Streaming on: {ott_n}</p>', unsafe_allow_html=True)
                        if ott_l != "#": st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">▶️ WATCH NOW ON {ott_n.upper()}</a>', unsafe_allow_html=True)
                processed += 1
