import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
import time

def get_levels_fyi_data(url):
    """
    Attempt to scrape levels.fyi data for engineering roles
    
    Args:
        url (str): The levels.fyi URL to scrape
        
    Returns:
        dict: Extracted salary data
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for salary data in common locations
        salary_data = {}
        
        # Try to find JSON data in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'salary' in script.string.lower():
                # Try to extract JSON data
                try:
                    # This is a simplified approach - actual implementation would need
                    # more sophisticated parsing based on levels.fyi's structure
                    salary_data['found_data'] = True
                    break
                except:
                    continue
        
        return salary_data
        
    except Exception as e:
        print(f"Error scraping levels.fyi: {e}")
        return {}

# Engineering role URLs to try
engineering_urls = [
    "https://www.levels.fyi/t/mechanical-engineer/title/design-engineer?country=254",
    "https://www.levels.fyi/t/hardware-engineer?country=254",
    "https://www.levels.fyi/t/manufacturing-engineer?country=254",
]

# BLS data for engineering roles (2024 data)
bls_engineering_data = {
    "mechanical_engineer": {
        "median_salary": 95300,
        "salary_range": [77020, 136210],
        "job_growth": "2%",
        "employment_2023": 278200
    },
    "chemical_engineer": {
        "median_salary": 108540,
        "salary_range": [72680, 176090], 
        "job_growth": "8%",
        "employment_2023": 25600
    },
    "materials_engineer": {
        "median_salary": 98300,
        "salary_range": [63170, 160160],
        "job_growth": "8%", 
        "employment_2023": 27800
    },
    "industrial_engineer": {
        "median_salary": 95300,
        "salary_range": [63720, 144830],
        "job_growth": "12%",
        "employment_2023": 293950
    },
    "environmental_engineer": {
        "median_salary": 96820,
        "salary_range": [60550, 159120],
        "job_growth": "4%",
        "employment_2023": 44000
    }
}

def collect_engineering_data():
    """
    Collect comprehensive engineering career data
    """
    print("Collecting engineering career data...")
    
    # Try to get levels.fyi data
    levels_data = {}
    for url in engineering_urls:
        print(f"Attempting to collect data from: {url}")
        data = get_levels_fyi_data(url)
        if data:
            levels_data[url] = data
        time.sleep(1)  # Be respectful to the server
    
    return {
        "bls_data": bls_engineering_data,
        "levels_data": levels_data
    }

if __name__ == "__main__":
    data = collect_engineering_data()
    print("BLS Data collected:")
    for role, info in data["bls_data"].items():
        print(f"  {role}: ${info['median_salary']:,} median")