from flask import Flask, request, render_template
import requests
import os
import pickle
from datetime import datetime, timedelta

app = Flask(__name__)

CACHE_FILENAME = 'prayer_times_cache.pkl'
CACHE_EXPIRATION_DAYS = 30  # Cache expires after 30 days

def load_cached_data():
    if os.path.exists(CACHE_FILENAME):
        with open(CACHE_FILENAME, 'rb') as f:
            return pickle.load(f)
    return None

def save_cached_data(data):
    with open(CACHE_FILENAME, 'wb') as f:
        pickle.dump(data, f)

def is_cache_valid(cache_timestamp):
    if not cache_timestamp:
        return False
    current_time = datetime.now()
    return (current_time - cache_timestamp).days < CACHE_EXPIRATION_DAYS

def get_prayer_times(city_id):
    cached_data = load_cached_data()
    if cached_data and is_cache_valid(cached_data['timestamp']):
        return cached_data['prayer_times']

    # Fetch data from the API if cache is missing or stale
    url = f"https://habous-prayer-times-api.onrender.com/api/v1/prayer-times?cityId={city_id}"
    response = requests.get(url)
    if response.status_code == 200:
        prayer_times = response.json().get('data', {}).get('timings', [])
        # Save the fetched data to cache
        save_cached_data({'prayer_times': prayer_times, 'timestamp': datetime.now()})
        return prayer_times
    return []

def get_available_cities():
    url = "https://habous-prayer-times-api.onrender.com/api/v1/available-cities"
    response = requests.get(url)
    if response.status_code == 200:
        cities = response.json().get('cities', [])
        # Ensure 'frenshCityName' exists in all city entries
        for city in cities:
            if 'frenshCityName' not in city:
                city['frenshCityName'] = city.get('name', '')  # Default to another key if available
        cities.sort(key=lambda x: x['frenshCityName'])  # Sort cities alphabetically
        return cities
    return []

@app.route('/', methods=['GET', 'POST'])
def index():
    cities = get_available_cities()
    prayer_times = []
    selected_city = None

    if request.method == 'POST':
        city_id = request.form['city']
        selected_city = next((city for city in cities if city['id'] == city_id), None)
        if selected_city:
            prayer_times = get_prayer_times(city_id)

    return render_template('index.html', cities=cities, prayer_times=prayer_times, selected_city=selected_city)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
