import streamlit as st
import hashlib
import os
from datetime import datetime
import json
import secrets

# Create a secrets folder if it doesn't exist
os.makedirs('.streamlit', exist_ok=True)

# Path to store user data
USER_DB_PATH = '.streamlit/user_db.json'

# Initialize user database
def init_user_db():
    if not os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, 'w') as f:
            json.dump({}, f)

# Load user database
def load_user_db():
    init_user_db()
    try:
        with open(USER_DB_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

# Save user database
def save_user_db(user_db):
    with open(USER_DB_PATH, 'w') as f:
        json.dump(user_db, f)

# Hash password
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pw_hash, salt

# Authentication functions
def register_user(username, email, password):
    user_db = load_user_db()
    
    # Check if username already exists
    if any(user_db[user_id].get('username') == username for user_id in user_db):
        return False, "Username already exists"
    
    # Create user ID
    user_id = hashlib.md5(username.encode()).hexdigest()
    
    # Hash password with salt
    pw_hash, salt = hash_password(password)
    
    # Add user to database
    user_db[user_id] = {
        'username': username,
        'email': email,
        'password_hash': pw_hash,
        'salt': salt,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_login': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_user_db(user_db)
    return True, user_id

def login_user(username, password):
    user_db = load_user_db()
    
    # Find user by username
    user_id = None
    for uid, user_data in user_db.items():
        if user_data.get('username') == username:
            user_id = uid
            break
    
    if not user_id:
        return False, "Invalid username or password"
    
    # Check password
    salt = user_db[user_id]['salt']
    pw_hash, _ = hash_password(password, salt)
    
    if pw_hash != user_db[user_id]['password_hash']:
        return False, "Invalid username or password"
    
    # Update last login
    user_db[user_id]['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_user_db(user_db)
    
    return True, user_id

def is_authenticated():
    return 'user_id' in st.session_state

def get_current_user():
    if is_authenticated():
        user_db = load_user_db()
        user_id = st.session_state['user_id']
        if user_id in user_db:
            return user_db[user_id]
    return None

def get_username():
    user = get_current_user()
    if user:
        return user.get('username')
    return None

def get_email():
    user = get_current_user()
    if user:
        return user.get('email')
    return None

def logout_user():
    if 'user_id' in st.session_state:
        del st.session_state['user_id']

# Auth UI components
def auth_signup_form():
    with st.form("signup_form"):
        st.subheader("Create an Account")
        username = st.text_input("Username", key="signup_username")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        submit = st.form_submit_button("Sign Up")
        
        if submit:
            if password != confirm_password:
                st.error("Passwords don't match")
                return False
            
            success, message = register_user(username, email, password)
            if success:
                st.success("Account created successfully! Please log in.")
                return True
            else:
                st.error(message)
                return False

def auth_login_form():
    with st.form("login_form"):
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        submit = st.form_submit_button("Login")
        
        if submit:
            success, user_id_or_error = login_user(username, password)
            if success:
                st.session_state['user_id'] = user_id_or_error
                st.success("Logged in successfully!")
                return True
            else:
                st.error(user_id_or_error)
                return False

def auth_form():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        login_success = auth_login_form()
        if login_success:
            st.rerun()
    
    with tab2:
        signup_success = auth_signup_form()
        if signup_success:
            st.info("Account created! Please use the Login tab to sign in.")

def auth_widget():
    if is_authenticated():
        user = get_current_user()
        if user:
            st.write(f"Logged in as **{user['username']}**")
            
            if st.button("Logout", key="logout_button"):
                logout_user()
                st.rerun()
        else:
            # Handle case where user_id exists but user data doesn't
            logout_user()
            st.warning("Session expired. Please log in again.")
            auth_form()
    else:
        auth_form()

# Function to protect premium features
def premium_feature_gate():
    if not is_authenticated():
        st.warning("This is a premium feature. Please sign in to access.")
        auth_widget()
        return False
    return True