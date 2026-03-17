import streamlit as st
from tmdbv3api import TMDb, Movie, Discover, Search
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide")

# Correctly initialize TMDb
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
tmdb.debug = True

movie_api = Movie()
discover_api = Discover()
search_api = Search()

# --- 2. SESSION STATE MANAGEMENT ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'u_name' not in st.session_state:
    st.session_state.u_name = "Guest"

# --- 3. UI STYLING ---
def apply_styles():
    dark_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    st.markdown(f"""
        <style>
        .stApp {{ 
            background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("{dark_img}"); 
            background-size: cover; background-attachment: fixed; color: #ffffff; 
        }}
        .movie-card {{ border: 1px solid #444; padding: 15px; border-radius: 10px; background: rgba(0, 0, 0, 0.85); margin-bottom: 20px; }}
        .play-button {{ background: #28a745 !important; color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; }}
        .rating-badge {{ background: #f5c518; color: #000; padding: 2px 8px; border-radius: 5px; font-weight: bold; }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_details(m_id):
    try:
        # Note: tmdbv3api handles the requests internally. 
        # Manual session injection is not required for basic use.
        res = movie_api.details(m_id, append_to_response="credits,watch/providers,videos")
        
        plot = getattr(res, 'overview', "")
        if not plot or len(plot) < 15: return None
        
        rating = getattr(res, 'vote_average', 0.0)
        cast = ", ".join([c['name'] for c in getattr(res, 'credits', {}).get('cast', [])[:5]])
        
        # Get OTT providers for India
        providers = getattr(res, 'watch/providers', {}).get('results', {}).get('IN', {})
        ott_n, ott_l = None, None
        for mode in ['flatrate', 'free', 'ads']:
            if mode in providers:
                ott_n = providers[mode][0]['provider_name']
                ott_l = providers.get('link')
                break
        
        # Find YouTube trailer
        videos = getattr(res, 'videos', {}).get('results', [])
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in videos if v['site'] == 'YouTube'), None)
        
        return {"plot": plot, "cast": cast, "ott_n": ott_n, "ott_l": ott_l, "trailer": trailer, "rating": rating}
    except:
        return None

# --- 5. MAIN APP ---
apply_styles()

if not st.session_state.logged_in:
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Member Name").strip()
    if st.button("Enter ICU") and u_name:
        st.session_state.logged_in = True
        st.session_state.u_name = u_name
        st.rerun()
else:
    st.sidebar.write(f"Welcome, **{st.session_state.u_name}**!")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # Filters
    mood_map = {"Happy": 35, "Sad": 18, "Adventures": 12, "Thrill": 53, "Romantic": 10749}
    sel_mood = st.sidebar.selectbox("Mood", ["Select"] + list(mood_map.keys()))
    lang_map = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta", "English": "en"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))

    st.title("🎬 ICU Recommendations")
    search_query = st.text_input("🔍 Search for a movie...")

    if st.button("Get Recommendations") or search_query:
        results = []
        if search_query:
            results = search_api.movies(search_query)
        elif sel_mood != "Select" and sel_lang != "Select":
            results = discover_api.discover_movies({
                'with_genres': mood_map[sel_mood],
                'with_original_language': lang_map[sel_lang],
                'sort_by': 'popularity.desc'
            })

        if results:
            cols = st.columns(3)
            for idx, item in enumerate(results[:12]): # Show top 12
                details = fetch_details(item.id)
                if not details: continue
                
                with cols[idx % 3]:
                    st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                    if item.poster_path:
                        st.image(f"https://image.tmdb.org/t/p/w500{item.poster_path}")
                    st.subheader(item.title)
                    st.markdown(f"<span class='rating-badge'>⭐ {details['rating']:.1f}</span>", unsafe_allow_html=True)
                    
                    if details['ott_n']:
                        st.caption(f"Watch on: {details['ott_n']}")
                    
                    with st.expander("Story"):
                        st.write(details['plot'])
                        st.write(f"**Cast:** {details['cast']}")
                    
                    if details['trailer']:
                        st.video(details['trailer'])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Try adjusting filters to see results.")
