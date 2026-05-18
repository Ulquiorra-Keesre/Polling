import httpx
from typing import Optional, Dict
from src.config import settings
import asyncio


class WeatherService:
    def __init__(self):
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.api_key = settings.OPENWEATHER_API_KEY
        self.timeout = httpx.Timeout(5.0)
        self.cache: Dict[str, dict] = {}
        self.cache_ttl = settings.WEATHER_CACHE_TTL

    async def get_weather(self, city: str = "Moscow") -> Optional[Dict]:

        cache_key = f"weather:{city}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if (
                asyncio.get_event_loop().time() - cached_data["timestamp"]
                < self.cache_ttl
            ):
                return cached_data["data"]

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.base_url}/weather",
                        params={
                            "q": city,
                            "appid": self.api_key,
                            "units": "metric",
                            "lang": "ru",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    self.cache[cache_key] = {
                        "data": self._normalize(data),
                        "timestamp": asyncio.get_event_loop().time(),
                    }

                    return self.cache[cache_key]["data"]

            except httpx.TimeoutException:
                if attempt == 2:
                    return self._get_fallback_data(city)
                await asyncio.sleep(1 * (attempt + 1))

            except httpx.HTTPError:
                if attempt == 2:
                    return self._get_fallback_data(city)

        return self._get_fallback_data(city)

    def _normalize(self, data: Dict) -> Dict:
        return {
            "city": data.get("name", "Unknown"),
            "temperature": data.get("main", {}).get("temp", 0),
            "feels_like": data.get("main", {}).get("feels_like", 0),
            "description": data.get("weather", [{}])[0].get("description", ""),
            "icon": data.get("weather", [{}])[0].get("icon", ""),
            "humidity": data.get("main", {}).get("humidity", 0),
            "wind_speed": data.get("wind", {}).get("speed", 0),
        }

    def _get_fallback_data(self, city: str) -> Dict:

        # (graceful degradation)
        return {
            "city": city,
            "temperature": None,
            "feels_like": None,
            "description": "Данные недоступны",
            "icon": None,
            "humidity": None,
            "wind_speed": None,
            "is_fallback": True,
        }


weather_service = WeatherService()
