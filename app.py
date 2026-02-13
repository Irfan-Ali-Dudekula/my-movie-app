import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Search
from datetime import datetime
import requests
import pandas as pd

# --- 1. SESSION INITIALIZATION ---
if 'u_age' not in st.session_state:
    st.session_state.u_age = 18
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 2. TMDB SETUP ---
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, search_api = Discover(), Search()

# --- 3. UI STYLING ---
st.set_page_config(page_title="IRFAN CINEMATIC UNIVERSE (ICU)", layout="wide")

def set_bg():
    video_url = "http://googleusercontent.com/generated_video_content/10641277448723540926"
    st.markdown(f"""
        <style>
        .stApp {{ background: rgba(0,0,0,0.85); color: white; }}
        #bg-video {{ position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -1; filter: brightness(20%); object-fit: cover; }}
        .play-button {{ background: #28a745 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; display: block; text-align: center; font-weight: bold; margin-top: 10px; border: none; }}
        .ott-badge {{ background-color: #28a745; color: white; padding: 4px 10px; border-radius: 5px; font-weight: bold; display: inline-block; margin-bottom: 8px; border: 1px solid #ffffff; }}
        </style>
        <video autoplay muted loop id="bg-video"><source src="{video_url}" type="video/mp4"></video>
        """, unsafe_allow_html=True)

# --- 4. DATA EXTRACTION (OTT, Plot, Cast, Trailers) ---
@st.cache_data(ttl=3600)
def get_movie_meta(m_id, type_str):
    try:
        obj = movie_api if type_str == "Movies" else tv_api
        # append_to_response is key for extracting OTT and Cast in one go
        res = obj.details(m_id, append_to_response="credits,watch/providers,videos")
        
        plot = getattr(res, 'overview', "Plot summary not found.")
        cast = ", ".join([c['name'] for c in getattr(res, 'credits', {}).get('cast', [])[:5]])
        
        # OTT Extraction: Checks for India specifically
        providers = getattr(res, 'watch/providers', {}).get('results', {}).get('IN', {})
        ott_n, ott_l = None, None
        for mode in ['flatrate', 'free', 'ads']:
            if mode in providers:
                ott_n = providers[mode][0]['provider_name']
                ott_l = providers.get('link')
                break
        
        # YouTube Trailer
        trailer = next((f"https://www.youtube.com/watch?v={v['key']}" for v in getattr(res, 'videos', {}).get('results', []) if v['site'] == 'YouTube'), None)
        
        return plot, cast, ott_n, ott_l, trailer
    except:
        return None, None, None, None, None

# --- 5. HUMAN EMOTION MAPPING ---
emotion_map = {
    "Laughter/Funny": 35,     # Comedy
    "Fear/Scary": 27,        # Horror
    "Excitement/Action": 28,  # Action
    "Love/Romantic": 10749,   # Romance
    "Curiosity/Mystery": 9648,# Mystery
    "Sadness/Emotional": 18,  # Drama
    "Bravery/War": 10752      # War
}

# --- 6. MAIN APP LOGIC ---
if not st.session_state.logged_in:
    set_bg()
    st.title("🎬 IRFAN CINEMATIC UNIVERSE (ICU)")
    u_name = st.text_input("Name")
    u_age = st.number_input("Age", 1, 100, 18)
    if st.button("Enter ICU"):
        st.session_state.logged_in, st.session_state.u_name, st.session_state.u_age = True, u_name, u_age
        st.rerun()
else:
    set_bg()
    st.sidebar.header("How are you feeling?")
    sel_emotion = st.sidebar.selectbox("Choose Emotion", ["Select"] + list(emotion_map.keys()))
    
    lang_map = {"Telugu": "te", "Hindi": "hi", "English": "en", "Tamil": "ta"}
    sel_lang = st.sidebar.selectbox("Language", ["Select"] + list(lang_map.keys()))
    
    era_map = {"Modern (2020-2030)": "2020-2030", "Legacy (2010-2020)": "2010-2020", "Classic (2000-2010)": "2000-2010"}
    sel_era = st.sidebar.selectbox("Era", ["Select"] + list(era_map.keys()))

    if st.button("Get Recommendations 🚀"):
        if sel_emotion != "Select" and sel_lang != "Select" and sel_era != "Select":
            s_year, e_year = map(int, era_map[sel_era].split('-'))
            p = {
                'with_original_language': lang_map[sel_lang], 
                'primary_release_date.gte': f"{s_year}-01-01", 
                'primary_release_date.lte': f"{e_year}-12-31", 
                'with_genres': emotion_map[sel_emotion],
                'watch_region': 'IN',
                'with_watch_monetization_types': 'flatrate|free|ads'
            }
            results = list(discover_api.discover_movies(p))

            if results:
                cols = st.columns(3)
                processed = 0
                for item in results:
                    if processed >= 15: break
                    plot, cast, ott_n, ott_l, trailer = get_movie_meta(item.id, "Movies")
                    
                    # Filtering: Only show if available on OTT or YouTube
                    if not ott_n and not trailer: continue

                    with cols[processed % 3]:
                        st.image(f"https://image.tmdb.org/t/p/w500{getattr(item, 'poster_path', '')}")
                        st.subheader(f"{getattr(item, 'title', '')}")
                        
                        with st.expander("📖 Plot & Cast"):
                            st.write(f"**Plot:** {plot}")
                            st.write(f"**Cast:** {cast}")
                        
                        if ott_n:
                            st.markdown(f"<div class='ott-badge'>📺 Streaming on: {ott_n.upper()}</div>", unsafe_allow_html=True)
                        elif trailer:
                            st.markdown(f"<div class='ott-badge' style='background:#f00;'>🎬 Watch on YouTube</div>", unsafe_allow_html=True)
                        
                        if trailer: st.video(trailer)
                        
                        if ott_l:
                            st.markdown(f'<a href="{ott_l}" target="_blank" class="play-button">▶️ WATCH NOW</a>', unsafe_allow_html=True)
                        processed += 1
