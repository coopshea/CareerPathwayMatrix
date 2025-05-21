import os
from functools import wraps
import requests
from flask import Flask, session, redirect, request, Response
from urllib.parse import urlencode

# Check if we're running on Replit
REPLIT_ENVIRONMENT = os.environ.get('REPL_ID') and os.environ.get('REPL_OWNER')

def is_authenticated():
    """
    Check if the current user is authenticated via Replit Auth.
    Returns True if authenticated, False otherwise.
    """
    # If not running on Replit, return True for development
    if not REPLIT_ENVIRONMENT:
        return True
    
    # Get authentication header
    auth_header = request.headers.get('X-Replit-User-Id')
    
    # If the header exists, user is authenticated
    return auth_header is not None

def get_user_info():
    """
    Get information about the currently authenticated user.
    Returns a dictionary with user information or None if not authenticated.
    """
    # If not running on Replit, return dummy user for development
    if not REPLIT_ENVIRONMENT:
        return {
            'id': 'dev_user',
            'name': 'Development User',
            'roles': []
        }
    
    # Get authentication headers
    user_id = request.headers.get('X-Replit-User-Id')
    username = request.headers.get('X-Replit-User-Name')
    user_roles = request.headers.get('X-Replit-User-Roles', '')
    
    # If not authenticated, return None
    if not user_id:
        return None
    
    # Parse roles from comma-separated string
    roles = user_roles.split(',') if user_roles else []
    
    return {
        'id': user_id,
        'name': username,
        'roles': roles
    }

def auth_required(f):
    """
    Decorator to require authentication for a route.
    If the user is not authenticated, they will be redirected to the login page.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            # Build login URL with redirect back to current page
            login_url = f"https://replit.com/auth_with_repl_site?domain={request.host}"
            return redirect(login_url)
        return f(*args, **kwargs)
    return decorated

def set_auth_cookie():
    """
    Sets an authentication cookie for the current user.
    This is useful for Streamlit apps that can't access the request headers directly.
    """
    user_info = get_user_info()
    if user_info:
        # Use Flask's session to store user info as cookie
        session['user_id'] = user_info['id']
        session['username'] = user_info['name']
        session['roles'] = user_info['roles']

def create_auth_wrapper(streamlit_app):
    """
    Create a Flask wrapper around a Streamlit app with Replit authentication.
    
    Args:
        streamlit_app: The function to run the Streamlit app
    
    Returns:
        Flask app with authentication
    """
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    
    @app.route('/')
    @auth_required
    def index():
        # Set authentication cookie and redirect to Streamlit app
        set_auth_cookie()
        return redirect('/streamlit')
    
    @app.route('/streamlit')
    def streamlit_proxy():
        # Run the Streamlit app
        streamlit_app()
        return "Streamlit app is running"
    
    return app

def get_current_username():
    """
    Get the username of the currently authenticated user.
    Returns the username or None if not authenticated.
    """
    user_info = get_user_info()
    return user_info['name'] if user_info else None