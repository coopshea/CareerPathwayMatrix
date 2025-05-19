import streamlit as st
import hashlib
import time
import json
import os
from database import init_db, Session, User

# File to store user data if database is not available
USER_DATA_FILE = "user_data.json"

class UserAuth:
    @staticmethod
    def initialize():
        """Initialize user authentication system"""
        # Set up session state for user
        if "user" not in st.session_state:
            st.session_state.user = None
            
        if "user_data" not in st.session_state:
            # Try to load from file
            try:
                if os.path.exists(USER_DATA_FILE):
                    with open(USER_DATA_FILE, "r") as f:
                        st.session_state.user_data = json.load(f)
                else:
                    st.session_state.user_data = {}
            except Exception:
                st.session_state.user_data = {}
    
    @staticmethod
    def login_user_form():
        """Display login form and handle sign-in"""
        # Create two columns for the form
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Sign in to personalize your experience")
            
            # Create the sign-in form
            with st.form("login_form"):
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                
                submitted = st.form_submit_button("Sign In")
                
                if submitted:
                    # Simple validation
                    if not full_name or not email or "@" not in email:
                        st.error("Please enter a valid name and email address.")
                        return False
                    
                    # Create a simple hash for the user identifier
                    user_id = hashlib.md5(email.encode()).hexdigest()
                    
                    # Store user information
                    user_info = {
                        "id": user_id,
                        "name": full_name,
                        "email": email,
                        "created_at": time.time(),
                        "last_login": time.time()
                    }
                    
                    # Save to session state
                    st.session_state.user = user_info
                    
                    # Save to persistent storage
                    UserAuth._save_user(user_info)
                    
                    # Rerun to update UI
                    st.success(f"Welcome, {full_name}!")
                    st.rerun()
                    
                    return True
            
            return False
        
        with col2:
            st.markdown("""
            ### Why Sign In?
            
            Signing in allows us to:
            - Save your career preferences
            - Store your uploaded resume
            - Provide personalized recommendations
            - Remember your chat history
            
            We don't share your data with third parties.
            """)
    
    @staticmethod
    def display_user_info():
        """Display current user information and logout button"""
        if st.session_state.user is not None:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Signed in as:** {st.session_state.user['name']} ({st.session_state.user['email']})")
            
            with col2:
                if st.button("Sign Out"):
                    st.session_state.user = None
                    st.rerun()
    
    @staticmethod
    def get_current_user():
        """Get the current user information"""
        return st.session_state.user
    
    @staticmethod
    def is_authenticated():
        """Check if a user is currently authenticated"""
        return st.session_state.user is not None
    
    @staticmethod
    def logout():
        """Log out the current user"""
        st.session_state.user = None
    
    @staticmethod
    def _save_user(user_info):
        """Save user information to persistent storage"""
        try:
            # Connect to database
            session = Session()
            
            # Check if user already exists
            db_user = session.query(User).filter(User.id == user_info['id']).first()
            
            if db_user:
                # Update existing user
                db_user.name = user_info['name']
                db_user.email = user_info['email']
                db_user.last_login = time.time()
            else:
                # Create new user
                db_user = User(
                    id=user_info['id'],
                    name=user_info['name'],
                    email=user_info['email'],
                    created_at=time.time(),
                    last_login=time.time()
                )
                session.add(db_user)
            
            # Commit changes
            session.commit()
            session.close()
        except Exception as e:
            print(f"Error saving user to database: {e}")
            # If database fails, fall back to file storage
            try:
                # Update user data in session state
                st.session_state.user_data[user_info['id']] = user_info
                
                # Save to file
                with open(USER_DATA_FILE, "w") as f:
                    json.dump(st.session_state.user_data, f)
            except Exception:
                # If all fails, just keep in session state
                pass

# Initialize user auth on import
UserAuth.initialize()