import streamlit as st
from tmdbv3api import TMDb, Movie, TV, Discover, Trending, Search
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import random

# --- 1. CORE STABILIZATION ---
@st.cache_resource
def get_bulletproof_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'
tmdb.session = get_bulletproof_session() 
tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()

# --- 2. THE FIX: SMART RECOMMENDATION ENGINE ---
def get_smart_recommendations(m_type, lang, era, mood):
    s_year, e_year = map(int, era.split('-'))
    # Base parameters
    params = {
        'with_original_language': lang,
        'primary_release_date.gte': f"{s_year}-01-01",
        'primary_release_date.lte': f"{e_year}-12-31",
        'with_genres': mood,
        'sort_by': 'popularity.desc'
    }
    
    # 1. Try: Strict OTT Availability in India
    params_strict = {**params, 'watch_region': 'IN', 'with_watch_monetization_types': 'flatrate|free|ads'}
    results = list(discover_api.discover_movies(params_strict) if m_type == "Movies" else discover_api.discover_tv_shows(params_strict))
    
    # 2. Fallback: If no results, remove OTT filter to show what exists
    if not results:
        results = list(discover_api.discover_movies(params) if m_type == "Movies" else discover_api.discover_tv_shows(params))
    
    return results

# ... (Include your existing UI, Login, and get_deep_details logic here) ...

# Inside your User Portal loop:
if st.button("Generate Recommendations 🚀"):
    if m_type != "Select" and sel_lang != "Select" and sel_era != "Select" and sel_mood != "Select":
        results = get_smart_recommendations(m_type, lang_map[sel_lang], sel_era, mood_map[sel_mood])
        # ... (display code)
