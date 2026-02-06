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
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR & SAFETY ---
st.sidebar.title("👤 User Profile")
name = st.sidebar.text_input("Enter Your Name", "Guest")
age = st.sidebar.number_input("Enter Your Age", 1, 100, 18)
is_adult = age >= 18

if not is_adult:
    st.sidebar.warning("🛡️ Safe Mode Active: Adult content and mature genres are hidden.")

st.sidebar.divider()
media_type = st.sidebar.selectbox("Content Type", ["Movies", "TV Shows"])
lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta", "Malayalam": "ml", "Kannada": "kn"}
sel_lang = st.sidebar.selectbox("Preferred Language", list(lang_map.keys()))

# --- 4. DATA HELPER FUNCTIONS ---
def get_safe_val(item, key, default=None):
    """Safely get values whether item is a dict or an object."""
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)

def get_detailed_info(m_id, m_type):
    trailer, cast_list, director = None, [], "Unknown"
    ott_name, ott_link = "Check Local Apps", "#"
    try:
        res = movie_api.details(m_id, append_to_response="videos,credits,watch/providers") if m_type == "Movies" else tv_api.details(m_id, append_to_response="videos,credits,watch/providers")
        
        # Trailer
        for v in res.get('videos', {}).get('results', []):
            if v['site'] == 'YouTube' and v['type'] == 'Trailer':
                trailer = f"https://www.youtube.com/watch?v={v['key']}"
                break
        # Cast
        for actor in res.get('credits', {}).get('cast', [])[:5]:
            cast_list.append({"name": actor['name'], "pic": actor.get('profile_path')})
        # Director
        crew = res.get('credits', {}).get('crew', [])
        director = next((p['name'] for p in crew if p['job'] in ['Director', 'Executive Producer']), "N/A")
        # OTT
        providers = res.get('watch/providers', {}).get('results', {}).get('IN', {})
        if 'flatrate' in providers:
            ott_name = providers['flatrate'][0]['provider_name']
            ott_link = providers.get('link', '#')
    except: pass
    return trailer, ott_name, ott_link, cast_list, director

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

# --- 6. DISCOVERY ---
st.header("🎯 Personal Recommendations")
mood_map = {"Happy": 35, "Sad": 18, "Excited": 28, "Scared": 27, "Bored": 53}
mood = st.selectbox("How is your mood?", list(mood_map.keys()))

if st.button("Generate My List"):
    today = datetime.now().strftime('%Y-%m-%d')
    results = []
    for p in range(1, 4):
        params = {
            'with_genres': mood_map[mood], 'with_original_language': lang_map[sel_lang],
            'page': p, 'include_adult': is_adult, 
            'primary_release_date.lte': today if media_type == "Movies" else None
        }
        data = discover_api.discover_movies(params) if media_type == "Movies" else discover_api.discover_tv_shows(params)
        results.extend(data)

    if results:
        main_cols = st.columns(4)
        processed = 0
        for item in results:
            if processed >= 40: break
            
            # Safety Checks
            item_is_adult = get_safe_val(item, 'adult', False)
            g_ids = get_safe_val(item, 'genre_ids', [])
            if not is_adult and (item_is_adult or 27 in g_ids or 53 in g_ids): continue

            poster = get_safe_val(item, 'poster_path')
            if poster:
                with main_cols[processed % 4]:
                    st.image(f"https://image.tmdb.org/t/p/w500{poster}")
                    st.subheader(get_safe_val(item, 'title', get_safe_val(item, 'name', '')))
                    
                    if item_is_adult:
                        st.markdown('<div class="adult-warning">🔞 ADULT CONTENT</div>', unsafe_allow_html=True)
                    
                    with st.expander("More Details"):
                        trailer, ott_n, ott_l, cast, d_name = get_detailed_info(get_safe_val(item, 'id'), media_type)
                        st.write(f"🎬 **Directed by:** {d_name}")
                        st.write(get_safe_val(item, 'overview'))
                        
                        if cast:
                            st.write("🎭 **Cast:**")
                            c_cols = st.columns(5)
                            for idx, a in enumerate(cast):
                                with c_cols[idx]:
                                    if a['pic']: st.image(f"https://image.tmdb.org/t/p/w200{a['pic']}", use_container_width=True)
                                    st.caption(a['name'])
                        
                        if trailer: st.video(trailer)
                        if ott_l != "#":
                            st.markdown(f'<a href="{ott_l}" target="_blank" class="ott-link">Watch on {ott_n} ➔</a>', unsafe_allow_html=True)
                processed += 1
