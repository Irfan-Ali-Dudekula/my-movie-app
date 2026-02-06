import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending
from datetime import datetime

# --- 1. CONFIGURATION ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api = Movie()
tv_api = TV()
discover_api = Discover()
trending_api = Trending()

# --- 2. PAGE SETUP & STYLING ---
st.set_page_config(page_title="CinemaPro India", layout="wide", page_icon="🎬")

st.markdown("""
    <style>
    .adult-warning { color: white; background-color: #d9534f; font-weight: bold; padding: 10px; border-radius: 5px; text-align: center; margin: 10px 0; font-size: 0.8em; }
    .ott-link { background-color: #28a745; color: white !important; padding: 10px 20px; border-radius: 8px; text-decoration: none; display: inline-block; margin-top: 10px; font-weight: bold; width: 100%; text-align: center; }
    .ott-link:hover { background-color: #218838; color: white !important; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #0068c9; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR & SAFETY CONTROLS ---
st.sidebar.title("👤 User Profile")
name = st.sidebar.text_input("Enter Your Name", "Guest")
age = st.sidebar.number_input("Enter Your Age", 1, 100, 18)
is_adult = age >= 18

if not is_adult:
    st.sidebar.warning("🛡️ Safe Mode: Adult content and mature genres (Horror/Thriller) are strictly hidden.")

st.sidebar.divider()
media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Kannada": "kn"}
sel_lang = st.sidebar.selectbox("Preferred Language", list(lang_map.keys()))

# --- 4. DATA FUNCTIONS ---
def get_detailed_info(m_id, m_type):
    """Fetches trailer, OTT providers, Cast, and Director details."""
    trailer, cast_list, director = None, [], "Unknown"
    ott_name, ott_link = "Check Local Apps", "#"
    
    try:
        res = movie_api.details(m_id, append_to_response="videos,credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="videos,credits,watch/providers")
        
        # Trailer
        for v in res.get('videos', {}).get('results', []):
            if v['site'] == 'YouTube' and v['type'] == 'Trailer':
                trailer = f"https://www.youtube.com/watch?v={v['key']}"
                break
        
        # Cast (Top 5)
        cast_data = res.get('credits', {}).get('cast', [])
        for actor in cast_data[:5]:
            cast_list.append({
                "name": actor['name'],
                "char": actor['character'],
                "pic": f"https://image.tmdb.org/t/p/w200{actor['profile_path']}" if actor['profile_path'] else None
            })
            
        # Director/Producer
        crew_data = res.get('credits', {}).get('crew', [])
        if m_type == "Movies":
            director = next((person['name'] for person in crew_data if person['job'] == 'Director'), "N/A")
        else:
            director = next((person['name'] for person in crew_data if person['job'] == 'Executive Producer'), "N/A")

        # OTT Link (India)
        providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
        if 'flatrate' in providers:
            ott_name = providers['flatrate'][0]['provider_name']
            ott_link = providers.get('link', '#')
            
    except: pass
    return trailer, ott_name, ott_link, cast_list, director

# --- 5. TRENDING SECTION ---
st.title(f"🔥 Trending in India")
trending_results = trending_api.movie_day() if media_type == "Movies" else trending_api.tv_day()

t_cols = st.columns(6)
count = 0
for item in trending_results:
    if count >= 6: break
    if not is_adult and getattr(item, 'adult', False): continue
    
    with t_cols[count]:
        if item.poster_path:
            st.image(f"https://image.tmdb.org/t/p/w500{item.poster_path}", use_container_width=True)
            st.caption(f"**{getattr(item, 'title', getattr(item, 'name', ''))[:20]}...**")
            count += 1

st.divider()

# --- 6. SEARCH & DISCOVERY ---
st.header("🎯 Discover Something New")
search_query = st.text_input("Search by name...", placeholder="e.g. Baahubali")

results = []
if search_query:
    results = movie_api.search(search_query) if media_type == "Movies" else tv_api.search(search_query)
else:
    mood_map = {"Happy": 35, "Sad": 18, "Excited": 28, "Scared": 27, "Bored": 53}
    mood = st.selectbox("How is your mood?", list(mood_map.keys()))
    if st.button("Generate My List"):
        today = datetime.now().strftime('%Y-%m-%d')
        for p in range(1, 5):
            params = {
                'with_genres': mood_map[mood], 'with_original_language': lang_map[sel_lang],
                'page': p, 'include_adult': is_adult, 
                'primary_release_date.lte': today if media_type == "Movies" else None
            }
            page_data = discover_api.discover_movies(params) if media_type == "Movies" else discover_api.discover_tv_shows(params)
            results.extend(page_data)

# --- 7. DISPLAY GRID ---
if results:
    st.write(f"### Handpicked for {name}")
    main_cols = st.columns(4)
    processed_count = 0
    
    for item in results:
        if processed_count >= 48: break
        
        # Strict Age Filters
        item_is_adult = getattr(item, 'adult', False)
        genre_ids = getattr(item, 'genre_ids', [])
        if not is_adult and (item_is_adult or 27 in genre_ids or 53 in genre_ids):
            continue

        with main_cols[processed_count % 4]:
            if item.poster_path:
                st.image(f"https://image.tmdb.org/t/p/w500{item.poster_path}")
                m_title = getattr(item, 'title', getattr(item, 'name', 'Unknown'))
                st.subheader(m_title)
                
                if item_is_adult:
                    st.markdown('<div class="adult-warning">🔞 ADULT CONTENT - VIEWER DISCRETION</div>', unsafe_allow_html=True)
                
                with st.expander("Details, Cast & Trailer"):
                    trailer, ott_name, ott_link, cast, director = get_detailed_info(item.id, media_type)
                    
                    st.write(f"🎬 **Directed by:** {director}")
                    st.write(f"📅 **Released:** {getattr(item, 'release_date', getattr(item, 'first_air_date', 'N/A'))}")
                    st.write(item.overview)
                    
                    if cast:
                        st.write("🎭 **Top Cast:**")
                        c_cols = st.columns(5)
                        for idx, actor in enumerate(cast):
                            with c_cols[idx]:
                                if actor['pic']: st.image(actor['pic'], use_container_width=True)
                                st.caption(actor['name'])
                    
                    if trailer: st.video(trailer)
                    
                    st.write(f"📺 **Available on:** {ott_name}")
                    if ott_link != "#":
                        st.markdown(f'<a href="{ott_link}" target="_blank" class="ott-link">Open in {ott_name} ➔</a>', unsafe_allow_html=True)
                
                processed_count += 1
