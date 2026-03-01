"""
Weather Fetcher Plugin
======================

Get weather data for any location worldwide.

Example usage:
    >>> result = await plugin.get_current_weather("New York")
    >>> result = await plugin.get_forecast("London", days=5)
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from src.core.plugin_system import ToolPlugin


class WeatherFetcherPlugin(ToolPlugin):
    """Plugin for fetching weather data."""
    
    # Sample weather data for demo mode
    DEMO_CITIES = {
        "new york": {"temp": 15, "feels_like": 13, "humidity": 65, "description": "Partly cloudy", "icon": "⛅"},
        "london": {"temp": 12, "feels_like": 10, "humidity": 78, "description": "Light rain", "icon": "🌧️"},
        "tokyo": {"temp": 22, "feels_like": 23, "humidity": 55, "description": "Clear sky", "icon": "☀️"},
        "paris": {"temp": 14, "feels_like": 12, "humidity": 70, "description": "Cloudy", "icon": "☁️"},
        "sydney": {"temp": 25, "feels_like": 26, "humidity": 60, "description": "Sunny", "icon": "☀️"},
        "default": {"temp": 18, "feels_like": 17, "humidity": 60, "description": "Clear", "icon": "🌤️"}
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
        self.cache_file = Path("data/weather_cache.json")
        
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        
        self.api_key = self.settings.get("api_key")
        self.units = self.settings.get("default_units", "metric")
        self.cache_duration = self.settings.get("cache_duration_minutes", 15)
        
        # Load cache
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text())
            except:
                self.cache = {}
        
        self.register_tool(
            name="get_current_weather",
            func=self.get_current_weather,
            description="Get current weather for a city or location",
            parameters={
                "location": {"type": "string", "required": True, "description": "City name or coordinates"},
                "units": {"type": "string", "required": False, "description": "metric, imperial, or kelvin"}
            }
        )
        
        self.register_tool(
            name="get_forecast",
            func=self.get_forecast,
            description="Get weather forecast for upcoming days",
            parameters={
                "location": {"type": "string", "required": True},
                "days": {"type": "integer", "required": False, "description": "Number of days (1-7)"}
            }
        )
        
        self.register_tool(
            name="get_weather_alerts",
            func=self.get_weather_alerts,
            description="Get active weather alerts for a location",
            parameters={
                "location": {"type": "string", "required": True}
            }
        )
        
        self.register_tool(
            name="compare_weather",
            func=self.compare_weather,
            description="Compare weather between multiple cities",
            parameters={
                "locations": {"type": "array", "required": True, "description": "List of city names to compare"}
            }
        )
    
    async def get_current_weather(self, location: str, units: Optional[str] = None) -> Dict[str, Any]:
        """Get current weather for a location."""
        try:
            units = units or self.units
            cache_key = f"current_{location.lower()}_{units}"
            
            # Check cache
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            if self.api_key and HAS_REQUESTS:
                # Real API call
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    "q": location,
                    "appid": self.api_key,
                    "units": units
                }
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "success": True,
                        "location": data["name"],
                        "country": data.get("sys", {}).get("country"),
                        "temperature": round(data["main"]["temp"], 1),
                        "feels_like": round(data["main"]["feels_like"], 1),
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "description": data["weather"][0]["description"].title(),
                        "wind_speed": data["wind"]["speed"],
                        "clouds": data["clouds"]["all"],
                        "units": units,
                        "timestamp": datetime.now().isoformat()
                    }
                    self._set_cached(cache_key, result)
                    return result
                    
            # Demo mode
            city_key = location.lower()
            demo = self.DEMO_CITIES.get(city_key, self.DEMO_CITIES["default"])
            
            result = {
                "success": True,
                "demo_mode": True,
                "location": location.title(),
                "temperature": demo["temp"],
                "feels_like": demo["feels_like"],
                "humidity": demo["humidity"],
                "description": demo["description"],
                "icon": demo["icon"],
                "units": units,
                "timestamp": datetime.now().isoformat()
            }
            return result
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
        """Get weather forecast."""
        try:
            days = min(max(days, 1), 7)
            
            if self.api_key and HAS_REQUESTS:
                url = "https://api.openweathermap.org/data/2.5/forecast"
                params = {
                    "q": location,
                    "appid": self.api_key,
                    "units": self.units,
                    "cnt": days * 8  # 3-hour intervals
                }
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Group by day
                    daily = {}
                    for item in data["list"]:
                        date = item["dt_txt"].split()[0]
                        if date not in daily:
                            daily[date] = {
                                "date": date,
                                "temp_min": item["main"]["temp_min"],
                                "temp_max": item["main"]["temp_max"],
                                "description": item["weather"][0]["description"]
                            }
                        else:
                            daily[date]["temp_min"] = min(daily[date]["temp_min"], item["main"]["temp_min"])
                            daily[date]["temp_max"] = max(daily[date]["temp_max"], item["main"]["temp_max"])
                    
                    return {
                        "success": True,
                        "location": data["city"]["name"],
                        "forecast": list(daily.values())[:days]
                    }
            
            # Demo forecast
            forecast = []
            icons = ["☀️", "⛅", "☁️", "🌧️", "⛅", "☀️", "🌤️"]
            base_temp = self.DEMO_CITIES.get(location.lower(), self.DEMO_CITIES["default"])["temp"]
            
            for i in range(days):
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                forecast.append({
                    "date": date,
                    "temp_min": base_temp - 3 + (i % 3),
                    "temp_max": base_temp + 4 + (i % 4),
                    "icon": icons[i % len(icons)],
                    "description": ["Sunny", "Partly cloudy", "Cloudy", "Light rain", "Clear"][i % 5]
                })
            
            return {
                "success": True,
                "demo_mode": True,
                "location": location.title(),
                "days": days,
                "forecast": forecast
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_weather_alerts(self, location: str) -> Dict[str, Any]:
        """Get weather alerts for a location."""
        try:
            # Demo alerts
            return {
                "success": True,
                "demo_mode": True,
                "location": location.title(),
                "alerts": [],
                "message": "No active weather alerts for this location"
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def compare_weather(self, locations: List[str]) -> Dict[str, Any]:
        """Compare weather across multiple cities."""
        try:
            comparisons = []
            
            for loc in locations[:5]:  # Max 5 cities
                weather = await self.get_current_weather(loc)
                if weather.get("success"):
                    comparisons.append({
                        "location": weather.get("location", loc),
                        "temperature": weather.get("temperature"),
                        "feels_like": weather.get("feels_like"),
                        "humidity": weather.get("humidity"),
                        "description": weather.get("description"),
                        "icon": weather.get("icon", "🌤️")
                    })
            
            # Find extremes
            if comparisons:
                warmest = max(comparisons, key=lambda x: x.get("temperature", 0))
                coldest = min(comparisons, key=lambda x: x.get("temperature", 0))
                
                return {
                    "success": True,
                    "cities": comparisons,
                    "warmest": warmest["location"],
                    "coldest": coldest["location"],
                    "temperature_range": f"{coldest['temperature']}° - {warmest['temperature']}°"
                }
            
            return {"success": False, "error": "No valid locations found"}
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data if valid."""
        if key in self.cache:
            cached = self.cache[key]
            cached_time = datetime.fromisoformat(cached.get("timestamp", "2000-01-01"))
            if datetime.now() - cached_time < timedelta(minutes=self.cache_duration):
                cached["from_cache"] = True
                return cached
        return None
    
    def _set_cached(self, key: str, data: Dict) -> None:
        """Cache data."""
        self.cache[key] = data
        try:
            self.cache_file.parent.mkdir(exist_ok=True)
            self.cache_file.write_text(json.dumps(self.cache, indent=2))
        except:
            pass
