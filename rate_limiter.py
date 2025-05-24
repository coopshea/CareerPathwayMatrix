import os
import json
from datetime import datetime, date
import streamlit as st

# Rate limiting configuration
DAILY_LIMIT = 50
RATE_LIMIT_FILE = "openai_usage.json"

def get_usage_data():
    """Load current usage data from file or create new if doesn't exist."""
    try:
        if os.path.exists(RATE_LIMIT_FILE):
            with open(RATE_LIMIT_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        
        # Clean up old dates (keep only current date)
        today = date.today().isoformat()
        if today not in data:
            data = {today: 0}  # Reset for new day
        else:
            # Keep only today's data
            data = {today: data.get(today, 0)}
            
        return data
    except Exception as e:
        print(f"Error loading usage data: {e}")
        return {date.today().isoformat(): 0}

def save_usage_data(data):
    """Save usage data to file."""
    try:
        with open(RATE_LIMIT_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving usage data: {e}")
        return False

def check_rate_limit():
    """Check if we're within the daily rate limit."""
    usage_data = get_usage_data()
    today = date.today().isoformat()
    current_usage = usage_data.get(today, 0)
    
    return current_usage < DAILY_LIMIT, current_usage

def increment_usage():
    """Increment the daily usage counter."""
    usage_data = get_usage_data()
    today = date.today().isoformat()
    
    usage_data[today] = usage_data.get(today, 0) + 1
    save_usage_data(usage_data)
    
    return usage_data[today]

def get_remaining_calls():
    """Get the number of remaining API calls for today."""
    usage_data = get_usage_data()
    today = date.today().isoformat()
    current_usage = usage_data.get(today, 0)
    
    return max(0, DAILY_LIMIT - current_usage)

def rate_limit_warning():
    """Display rate limit information to user."""
    can_call, current_usage = check_rate_limit()
    remaining = get_remaining_calls()
    
    if not can_call:
        st.error(f"🚫 Daily OpenAI API limit reached ({DAILY_LIMIT} calls). Please try again tomorrow.")
        return False
    elif remaining <= 5:
        st.warning(f"⚠️ Only {remaining} AI analysis calls remaining today.")
    else:
        st.info(f"💡 {remaining} AI analysis calls remaining today.")
    
    return True

def openai_api_call_wrapper(api_function, *args, **kwargs):
    """
    Wrapper function for OpenAI API calls that enforces rate limiting.
    
    Args:
        api_function: The OpenAI API function to call
        *args, **kwargs: Arguments to pass to the API function
    
    Returns:
        The API response or None if rate limited
    """
    can_call, current_usage = check_rate_limit()
    
    if not can_call:
        st.error(f"🚫 Daily OpenAI API limit reached ({DAILY_LIMIT} calls). Please try again tomorrow.")
        return None
    
    try:
        # Make the API call
        result = api_function(*args, **kwargs)
        
        # Increment usage counter on successful call
        new_usage = increment_usage()
        
        # Show remaining calls
        remaining = DAILY_LIMIT - new_usage
        if remaining <= 5:
            st.warning(f"⚠️ {remaining} AI analysis calls remaining today.")
        
        return result
        
    except Exception as e:
        st.error(f"Error making AI request: {str(e)}")
        return None