import streamlit as st
from replit import db
import os
import secrets
import json
import time
from urllib.parse import urlencode
import requests

# Configuration for Replit Auth
AUTH_URL = "https://replit.com/auth_with_repl_site"
CLIENT_ID = os.getenv("REPLIT_CLIENT_ID", "")
REDIRECT_URI = os.getenv("REPLIT_REDIRECT_URI", "")

# For production, these should be set as secrets in Replit
if not CLIENT_ID or not REDIRECT_URI:
    CLIENT_ID = "career-path-navigator"  # This would be your app ID
    REDIRECT_URI = "https://career-path-navigator.replit.app"  # Your app URL

def generate_state_token():
    """Generate a secure state token for OAuth flow"""
    return secrets.token_urlsafe(32)

def get_auth_url():
    """Generate authentication URL for Replit Auth"""
    state = generate_state_token()
    
    # Store state token in session state for verification
    st.session_state.oauth_state = state
    
    # Create authentication URL
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "read",
        "response_type": "code",
        "state": state
    }
    
    return f"{AUTH_URL}?{urlencode(params)}"

def handle_auth_callback():
    """Handle authentication callback from Replit Auth"""
    # Get query parameters from URL
    query_params = st.experimental_get_query_params()
    
    # Check if we have an authorization code and state
    if "code" in query_params and "state" in query_params:
        code = query_params["code"][0]
        state = query_params["state"][0]
        
        # Verify state matches stored state
        if "oauth_state" in st.session_state and st.session_state.oauth_state == state:
            # In a full implementation, exchange code for access token
            # For this demo, we'll simulate authentication success
            st.session_state.is_authenticated = True
            st.session_state.user = {"username": "ReplitUser", "id": "demo_user"}
            
            # Clear URL parameters
            st.experimental_set_query_params()
            return True
    
    return False

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get("is_authenticated", False)

def get_current_user():
    """Get current authenticated user information"""
    return st.session_state.get("user", None)

def logout():
    """Log out current user"""
    if "is_authenticated" in st.session_state:
        del st.session_state.is_authenticated
    if "user" in st.session_state:
        del st.session_state.user
    
    # Clear other user-specific session state
    keys_to_clear = [k for k in st.session_state.keys() if k not in ["oauth_state"]]
    for key in keys_to_clear:
        del st.session_state[key]

def auth_required(func):
    """Decorator to require authentication for specific functions"""
    def wrapper(*args, **kwargs):
        if is_authenticated():
            return func(*args, **kwargs)
        else:
            auth_url = get_auth_url()
            st.warning("Please login to access this feature")
            st.markdown(f"[Login with Replit]({auth_url})")
            return None
    return wrapper

def render_auth_ui():
    """Render authentication UI in the sidebar"""
    with st.sidebar:
        st.markdown("---")
        if is_authenticated():
            user = get_current_user()
            st.success(f"Logged in as {user.get('username', 'User')}")
            if st.button("Logout"):
                logout()
                st.rerun()
        else:
            auth_url = get_auth_url()
            st.warning("You are not logged in")
            st.markdown(f"[Login with Replit]({auth_url})")