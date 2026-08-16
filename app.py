"""
Weather API Wrapper - Main Flask Application
Uses FREE wttr.in API - NO API KEY REQUIRED!
"""
from flask import Flask, render_template, request, jsonify
from flask_caching import Cache
import requests
import json
from datetime import datetime
from config import Config

# Create Flask application instance
app = Flask(__name__)

# Load configuration from config.py
app.config.from_object(Config)

# Initialize cache
cache = Cache(app)

# Get API settings from config
WEATHER_API_URL = app.config['WEATHER_API_URL']


def get_weather_from_api(city_name):
    """
    Fetch weather data from FREE wttr.in API
    
    Parameters:
        city_name (str): Name of the city to get weather for
        
    Returns:
        dict: Weather data or error message
    """
    try:
        # Prepare the API request URL
        # wttr.in returns JSON data for any city
        url = f"{WEATHER_API_URL}/{city_name}?format=j1"
        
        # Make the API request
        response = requests.get(url, timeout=10)
        
        # Check if request was successful (status code 200)
        if response.status_code == 200:
            # Parse JSON response
            weather_data = response.json()
            
            # Extract only the information we need from the complex JSON
            current_data = weather_data.get('current_condition', [{}])[0]
            location_data = weather_data.get('nearest_area', [{}])[0]
            
            # Get temperature in Celsius
            temp_c = current_data.get('temp_C', 'N/A')
            feels_like = current_data.get('FeelsLikeC', temp_c)
            
            return {
                'success': True,
                'city': location_data.get('areaName', [{}])[0].get('value', city_name),
                'country': location_data.get('country', [{}])[0].get('value', ''),
                'temperature': temp_c,
                'feels_like': feels_like,
                'humidity': current_data.get('humidity', 'N/A'),
                'description': current_data.get('weatherDesc', [{}])[0].get('value', ''),
                'icon': current_data.get('weatherCode', '113'),  # Weather code for icon
                'wind_speed': current_data.get('windspeedKmph', 'N/A'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            # API returned an error
            return {
                'success': False,
                'error': f'Error: {response.status_code} - City not found or API error'
            }
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out. Please try again.'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Connection error. Please check your internet.'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Request failed: {str(e)}'}
    except json.JSONDecodeError:
        return {'success': False, 'error': 'Invalid response from weather API'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}


def get_cached_or_fresh_weather(city_name):
    """
    Get weather data from cache if available, otherwise fetch from API
    
    Parameters:
        city_name (str): Name of the city
        
    Returns:
        dict: Weather data with cache status
    """
    # Create a unique cache key for this city (lowercase to avoid duplicates)
    cache_key = f"weather_{city_name.lower()}"
    
    # Try to get data from cache
    cached_data = cache.get(cache_key)
    
    if cached_data:
        # Data found in cache - add cache information
        cached_data['source'] = 'Cache'
        cached_data['cached_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cached_data['cache_note'] = '✅ Data from cache (updated within last 10 minutes)'
        return cached_data
    
    # Not in cache - fetch from API
    weather_data = get_weather_from_api(city_name)
    
    if weather_data.get('success'):
        # Store successful result in cache
        cache.set(cache_key, weather_data)
        weather_data['source'] = 'API (Fresh)'
        weather_data['cached_time'] = 'Not cached yet'
        weather_data['cache_note'] = '🔄 Fresh data from API (now cached for 10 minutes)'
        return weather_data
    else:
        # Return error
        return weather_data


# Main route - handles both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Home page - shows the weather form and results
    """
    weather_data = None
    error_message = None
    searched_city = None
    
    if request.method == 'POST':
        # Get city name from form
        searched_city = request.form.get('city', '').strip()
        
        if searched_city:
            # Get weather data (from cache or API)
            result = get_cached_or_fresh_weather(searched_city)
            
            if result.get('success'):
                weather_data = result
            else:
                error_message = result.get('error', 'Something went wrong')
        else:
            error_message = 'Please enter a city name'
    
    # Render the HTML template
    return render_template('index.html', 
                         weather=weather_data, 
                         error=error_message,
                         city=searched_city)


# API endpoint - returns weather data as JSON
@app.route('/api/weather/<city>')
def api_weather(city):
    """
    API endpoint to get weather data in JSON format
    Example: /api/weather/London
    """
    result = get_cached_or_fresh_weather(city)
    return jsonify(result)


# Route to clear cache for a specific city
@app.route('/clear-cache/<city>')
def clear_cache(city):
    """
    Clear cached data for a specific city
    """
    cache_key = f"weather_{city.lower()}"
    cache.delete(cache_key)
    return f"✅ Cache cleared for {city}"


# Route to clear all cache
@app.route('/clear-all-cache')
def clear_all_cache():
    """
    Clear all cached data
    """
    cache.clear()
    return "✅ All cache cleared"


# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)