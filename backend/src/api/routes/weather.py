from fastapi import APIRouter, Query
import httpx
import traceback
from src.config import settings

router = APIRouter(tags=["Weather"])

OPENWEATHER_API_KEY = settings.OPENWEATHER_API_KEY
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


@router.get("/current")
async def get_current_weather(city: str = Query(default="Moscow", max_length=100)):

    if not OPENWEATHER_API_KEY:
        return _fallback(city, "API ключ не настроен")

    try:
        print(f"Making request to {OPENWEATHER_BASE_URL}/weather")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{OPENWEATHER_BASE_URL}/weather",
                params={
                    "q": city,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                    "lang": "ru",
                },
            )

            if response.status_code != 200:
                return _fallback(city, f"HTTP {response.status_code}")

            data = response.json()

            return {
                "success": True,
                "data": {
                    "city": data.get("name", city),
                    "temperature": data.get("main", {}).get("temp"),
                    "feels_like": data.get("main", {}).get("feels_like"),
                    "description": data.get("weather", [{}])[0].get("description", ""),
                    "icon": data.get("weather", [{}])[0].get("icon"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "wind_speed": data.get("wind", {}).get("speed"),
                    "is_fallback": False,
                },
            }

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        return _fallback(city, f"{type(e).__name__}: {e}")


def _fallback(city: str, warning: str) -> dict:
    print(f"Fallback: {warning}")
    return {
        "success": True,
        "data": {
            "city": city,
            "temperature": None,
            "description": "Ошибка получения данных",
            "icon": None,
            "humidity": None,
            "wind_speed": None,
            "is_fallback": True,
            "warning": warning,
        },
    }
