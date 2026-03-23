import streamlit as st
from tmdbv3api import TMDb, Movie, Discover, Search
import requests

# --- 1. CORE CONFIGURATION ---
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide")

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'

movie_api, discover_api, search_api = Movie(), Discover(), Search()

# --- 2. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'u_name' not in st.session_state:
    st.session_state.u_name = "Guest"

# --- 3. PREMIUM UI STYLING (The Vault Aesthetics) ---
def apply_styles():
    bg_img = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070"
    
    st.markdown(f"""
        <style>
        @keyframes shimmer {{
            0% {{ background-position: -200% center; }}
            100% {{ background-position: 200% center; }}
        }}

        .stApp {{ 
            background: linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.45)), url("{bg_img}"); 
            background-size: cover; background-attachment: fixed; color: #ffffff; 
        }}

        /* ROYAL SHIMMER HEADING */
        .royal-title {{
            font-size: 55px !important;
            font-weight: 900 !important;
            text-align: center;
            background: linear-gradient(to right, #BF953F 20%, #FCF6BA 40%, #ffffff 50%, #FCF6BA 60%, #BF953F 80%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 4s linear infinite;
            text-shadow: 2px 4px 15px rgba(0,0,0,0.3);
            margin-bottom: 10px;
            font-family: 'Georgia', serif;
        }}

        /* GLASSMORPHISM MOVIE CARDS */
        .movie-card {{ 
            border: 1px solid rgba(255, 255, 255, 0.2); 
            padding: 20px; 
            border-radius: 20px; 
            background: rgba(0, 0, 0, 0.65); 
            backdrop-filter: blur(15px);
            margin-bottom: 25px; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
            transition: transform 0.3s ease;
            min-height: 600px;
        }}
        
        .movie-card:hover {{
            transform: translateY(-8px);
            border: 1px solid #FCF6BA;
        }}

        .rating-badge {{ 
            background: linear-gradient(45deg, #BF953F, #FCF6BA); 
            color: #000; padding: 4px 12px; border-radius: 8px; font-weight: bold; 
        }}

        .play-button {{ 
            background: linear-gradient(90deg, #BF953F, #FCF6BA) !important; 
            color: #000 !important; padding: 12px; border-radius: 10px; text-align: center; 
            font-weight: 800; display: block; text-decoration: none; margin-top: 15px;
        }}
        
        [data-testid="stSidebar"] {{ background: rgba(10, 10, 10, 0.95) !important; border-right: 1px solid #BF953F; }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_movie_data(m_id):
    try:
        res = movie_api.details(m_id, append_to_response="credits,watch/providers,videos")
        providers = getattr(res, 'watch/providers', {}).get('results', {}).get('IN', {})
        ott_n, ott_l = None, None
        for mode in ['flatrate', 'free', 'ads']:
            if mode in providers:
                ott_n = providers[mode][0]['provider_name']
                ott_l = providers.get('link')
                break
        
        videos = getattr(res, 'videos', {}).get('results', [])
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in videos if v['site'] == 'YouTube'), None)
        
        return {
            "plot": getattr(res, 'overview', "No bio available."),
            "cast": ", ".join([c['name'] for c in getattr(res, 'credits', {}).get('cast', [])[:4]]),
            "ott_n": ott_n, "ott_l": ott_l, "trailer": trailer,
            "rating": getattr(res, 'vote_average', 0.0)
        }
    except: return None

# --- 5. MAIN APP INTERFACE ---
apply_styles()

if not st.session_state.logged_in:
    st.markdown('<h1 class="royal-title">IRFAN CINEMATIC UNIVERSE (ICU)</h1>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u_name = st.text_input("Enter Member Name", placeholder="e.g. Irfan")
        if st.button("Access ICU 🔐") and u_name:
            st.session_state.logged_in, st.session_state.u_name = True, u_name
            st.rerun()
else:
    st.markdown('<h1 class="royal-title">IRFAN CINEMATIC UNIVERSE (ICU)</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown(f"### 👑 Welcome, {st.session_state.u_name}")
    mood_map = {"Happy": 35, "Sad": 18, "Adventures": 12, "Thrill": 53, "Romantic": 10749}
    lang_map = {"Telugu": "te", "Hindi": "hi", "Tamil": "ta", "English": "en", "Malayalam": "ml"}
    
    sel_mood = st.sidebar.selectbox("Your Current Vibe", ["Select"] + list(mood_map.keys()))
    sel_lang = st.sidebar.selectbox("Preferred Language", ["Select"] + list(lang_map.keys()))
    
    if st.sidebar.button("Exit ICU 🚪"):
        st.session_state.logged_in = False
        st.rerun()

    search_query = st.text_input("🔍 Search for a Masterpiece...", placeholder="Type movie name here...")

    # Logic to decide what to show
    movies = []
    header_text = "🔥 Trending Now"

    if search_query:
        movies = search_api.movies(search_query)
        header_text = f"🔍 Search Results for: {search_query}"
    elif sel_mood != "Select" and sel_lang != "Select":
        movies = discover_api.discover_movies({
            'with_genres': mood_map[sel_mood],
            'with_original_language': lang_map[sel_lang],
            'sort_by': 'popularity.desc'
        })
        header_text = f"✨ Recommended for {sel_mood} Mood"
    else:
        # Default: Show Trending Movies
        movies = movie_api.popular()

    st.markdown(f"### {header_text}")

    if movies:
        cols = st.columns(3)
        for i, movie in enumerate(movies[:15]):
            data = fetch_movie_data(movie.id)
            if not data or not movie.poster_path: continue
            
            with cols[i % 3]:
                st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                st.image(f"https://image.tmdb.org/t/p/w500{movie.poster_path}")
                st.subheader(movie.title)
                st.markdown(f"<span class='rating-badge'>⭐ {data['rating']:.1f} / 10</span>", unsafe_allow_html=True)
                
                if data['ott_n']:
                    st.write(f"📺 **Available on:** {data['ott_n']}")
                
                with st.expander("📖 Storyline & Cast"):
                    st.write(data['plot'])
                    st.caption(f"**Stars:** {data['cast']}")
                
                if data['trailer']: 
                    st.video(data['trailer'])
                
                if data['ott_l']: 
                    st.markdown(f'<a href="{data["ott_l"]}" target="_blank" class="play-button">▶️ WATCH NOW</a>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="play-button" style="background:gray !important; color:white !important;">Check Local Listings</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No matches found in the vault. Try different filters!")
