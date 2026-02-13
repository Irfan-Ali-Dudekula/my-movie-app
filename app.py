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
    """Limits open files to prevent OSError(24)"""
    session = requests.Session()
    # Retries handle temporary blips without opening new connections
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    # pool_maxsize=5 is a strict limit to ensure we stay well below the server limit
    adapter = HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

# Initialize TMDB
tmdb = TMDb()
tmdb.api_key = 'a3ce43541791ff5e752a8e62ce0fcde2'

# ACTIVATION FIX: This links your safe session to the library
tmdb.session = get_bulletproof_session() 

tmdb.language = 'en'
movie_api, tv_api = Movie(), TV()
discover_api, trending_api = Discover(), Trending()
search_api = Search()
