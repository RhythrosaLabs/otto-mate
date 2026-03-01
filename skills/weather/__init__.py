"""
Example: Weather Skill

A simple skill that provides weather information.
"""

from typing import Dict, Any
from src.core.skills import BaseSkill, SkillMetadata, SkillCategory
import logging

logger = logging.getLogger(__name__)


class WeatherSkill(BaseSkill):
    """Weather information skill"""
    
    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            id="weather",
            name="Weather",
            version="1.0.0",
            description="Get weather information for any location",
            author="Otto Team",
            category=SkillCategory.PRODUCTIVITY,
            tags=["weather", "forecast", "temperature"],
            requires=["aiohttp"],  # For API calls
            homepage="https://github.com/otto/skills-weather",
            repository="https://github.com/otto/skills-weather"
        )
    
    async def initialize(self, config: Dict[str, Any]):
        """Initialize skill with configuration"""
        self.api_key = config.get("api_key") or config.get("WEATHER_API_KEY")
        self.default_units = config.get("units", "metric")  # celsius, fahrenheit
        
        if not self.api_key:
            logger.warning("⚠️  Weather API key not configured (set WEATHER_API_KEY)")
        
        logger.info("🌤️  Weather skill initialized")
    
    async def shutdown(self):
        """Clean up resources"""
        logger.info("🌤️  Weather skill shutdown")
    
    def get_tools(self) -> Dict[str, Any]:
        """Return available tools"""
        return {
            "get_current_weather": self.get_current_weather,
            "get_forecast": self.get_forecast
        }
    
    def get_commands(self) -> Dict[str, Any]:
        """Return slash commands"""
        return {
            "/weather": self.weather_command
        }
    
    async def get_current_weather(self, location: str, units: str = None) -> Dict[str, Any]:
        """
        Get current weather for a location
        
        Args:
            location: City name or "lat,lon"
            units: Temperature units (metric/imperial)
        
        Returns:
            Weather data dict
        """
        import aiohttp
        
        if not self.api_key:
            return {
                "error": "Weather API key not configured"
            }
        
        units = units or self.default_units
        
        # Example using OpenWeatherMap API
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": units
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "location": data["name"],
                            "temperature": data["main"]["temp"],
                            "feels_like": data["main"]["feels_like"],
                            "description": data["weather"][0]["description"],
                            "humidity": data["main"]["humidity"],
                            "wind_speed": data["wind"]["speed"],
                            "units": "°C" if units == "metric" else "°F"
                        }
                    else:
                        return {
                            "error": f"API returned status {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return {
                "error": str(e)
            }
    
    async def get_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for a location
        
        Args:
            location: City name
            days: Number of days (1-7)
        
        Returns:
            Forecast data dict
        """
        import aiohttp
        
        if not self.api_key:
            return {
                "error": "Weather API key not configured"
            }
        
        # Example using OpenWeatherMap Forecast API
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": self.default_units,
            "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Group by day
                        forecast_by_day = {}
                        for item in data["list"]:
                            date = item["dt_txt"].split()[0]
                            if date not in forecast_by_day:
                                forecast_by_day[date] = []
                            forecast_by_day[date].append({
                                "time": item["dt_txt"].split()[1],
                                "temp": item["main"]["temp"],
                                "description": item["weather"][0]["description"]
                            })
                        
                        return {
                            "location": data["city"]["name"],
                            "forecast": forecast_by_day
                        }
                    else:
                        return {
                            "error": f"API returned status {response.status}"
                        }
        
        except Exception as e:
            logger.error(f"Forecast API error: {e}")
            return {
                "error": str(e)
            }
    
    async def weather_command(self, args: str) -> str:
        """Handle /weather slash command"""
        if not args:
            return "Usage: /weather <location>"
        
        weather = await self.get_current_weather(args)
        
        if "error" in weather:
            return f"❌ {weather['error']}"
        
        return (
            f"🌤️ **Weather in {weather['location']}**\n\n"
            f"Temperature: {weather['temperature']}{weather['units']}\n"
            f"Feels like: {weather['feels_like']}{weather['units']}\n"
            f"Conditions: {weather['description']}\n"
            f"Humidity: {weather['humidity']}%\n"
            f"Wind: {weather['wind_speed']} m/s"
        )
