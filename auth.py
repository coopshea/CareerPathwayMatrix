import os
import requests
import json
import streamlit as st
from flask import Flask, request, redirect, session
import threading
from urllib.parse import urlparse
import time
import jwt
from datetime import datetime, timedelta
import secrets

# Constants for Replit Auth
AUTH_URL = "https://replit.com/auth_with_repl_site"
REPLIT_X_DOMAIN = os.environ.get('REPLIT_X_DOMAIN', '')

# Generate a secure secret key
if "AUTH_SECRET_KEY" not in st.session_state:
    st.session_state.AUTH_SECRET_KEY = secrets.token_hex(32)

# Flask app for handling the authentication
app = Flask(__name__)
app.secret_key = st.session_state.AUTH_SECRET_KEY

# In-memory token store
tokens = {}

@app.route('/auth/login')
def login():
    """Redirect user to Replit Auth"""
    redirect_uri = f"https://{REPLIT_X_DOMAIN}/auth/callback"
    return redirect(f"{AUTH_URL}?redirect={redirect_uri}")

@app.route('/auth/callback')
def auth_callback():
    """Handle callback from Replit Auth"""
    # Get user data from query params
    user_id = request.args.get('id')
    username = request.args.get('username') 
    name = request.args.get('name', username)
    profile_image = request.args.get('profile_image', '')
    
    if not user_id or not username:
        return "Authentication failed. Missing user information.", 400
    
    # Store user data in a token
    token_data = {
        'user_id': user_id,
        'username': username,
        'name': name,
        'profileImage': profile_image,
        'exp': datetime.utcnow() + timedelta(days=7)  # Token expires in 7 days
    }
    
    # Create a signed JWT
    token = jwt.encode(token_data, app.secret_key, algorithm='HS256')
    
    # Store the token
    tokens[user_id] = token
    
    # Return to the main application
    return redirect(f"https://{REPLIT_X_DOMAIN}")

@app.route('/auth/verify')
def verify_auth():
    """Verify authentication token"""
    token = request.args.get('token')
    if not token:
        return json.dumps({'authenticated': False}), 200
    
    try:
        # Verify the token
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        # Check if token is valid and matches stored token
        if user_id and user_id in tokens and tokens[user_id] == token:
            return json.dumps({
                'authenticated': True,
                'user': {
                    'id': payload.get('user_id'),
                    'username': payload.get('username'),
                    'name': payload.get('name'),
                    'profileImage': payload.get('profileImage')
                }
            }), 200
        else:
            return json.dumps({'authenticated': False}), 200
    except:
        return json.dumps({'authenticated': False}), 200

@app.route('/auth/logout')
def logout():
    """Handle user logout"""
    user_id = request.args.get('user_id')
    if user_id and user_id in tokens:
        del tokens[user_id]
    
    return json.dumps({'success': True}), 200

# Start Flask server in a separate thread
def run_flask_server():
    app.run(host='0.0.0.0', port=8000)

flask_thread = None

def ensure_server_running():
    """Ensure Flask server is running"""
    global flask_thread
    if flask_thread is None or not flask_thread.is_alive():
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()
        time.sleep(1)  # Give it a moment to start

def check_login():
    """Check if user is logged in"""
    ensure_server_running()
    
    # Check for existing token in session state
    if "auth_token" in st.session_state:
        # Verify token validity
        try:
            response = requests.get(f"http://localhost:8000/auth/verify?token={st.session_state.auth_token}")
            result = response.json()
            return result.get('authenticated', False)
        except:
            return False
    
    # Check if we have query parameters with auth token
    try:
        query_params = st.experimental_get_query_params()
        if 'token' in query_params:
            token = query_params['token'][0]
            
            # Verify token
            response = requests.get(f"http://localhost:8000/auth/verify?token={token}")
            result = response.json()
            
            if result.get('authenticated', False):
                st.session_state.auth_token = token
                return True
    except Exception as e:
        st.error(f"Auth error: {str(e)}")
        pass
    
    return False

def get_user_info():
    """Get user information from token"""
    if "auth_token" in st.session_state:
        try:
            response = requests.get(f"http://localhost:8000/auth/verify?token={st.session_state.auth_token}")
            result = response.json()
            
            if result.get('authenticated', False):
                return result.get('user', {})
        except:
            pass
    
    return None

def logout_user():
    """Log user out"""
    ensure_server_running()
    
    if "auth_token" in st.session_state:
        try:
            # Decode token to get user ID
            payload = jwt.decode(st.session_state.auth_token, st.session_state.AUTH_SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            # Call logout API
            if user_id:
                requests.get(f"http://localhost:8000/auth/logout?user_id={user_id}")
            
            # Clear token from session state
            del st.session_state.auth_token
        except:
            pass

# Start authentication server when module is imported
ensure_server_running()