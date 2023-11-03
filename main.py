from fastapi import FastAPI
import httpx
import Levenshtein
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()


def similarity_percentage(str1, str2):
    distance = Levenshtein.distance(str1, str2)
    max_length = max(len(str1), len(str2))

    if max_length == 0:
        return 100.0

    similarity = (1 - (distance / max_length)) * 100.0
    return similarity


async def create_token():
    headers = {
        "Accept": "application/json",
        "api-token": os.getenv("TOKEN_API"),
        "user-email": os.getenv("EMAIL_API"),
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.universal-tutorial.com/api/getaccesstoken", headers=headers
        )

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Token error", "auth_token": None}


async def get_countries(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.universal-tutorial.com/api/countries/", headers=headers
        )

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Internat Server Error"}


async def get_states(token, country):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://www.universal-tutorial.com/api/states/{country}", headers=headers
        )

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Internat Server Error"}


@app.get("/countries/{country_name}")
async def index(country_name: str):
    token = await create_token()
    if token["auth_token"] is not None:
        countries = await get_countries(token["auth_token"])

        if type(countries) is list:
            results = []
            for item in countries:
                percentage = similarity_percentage(
                    country_name.lower(), item["country_name"].lower()
                )
                if percentage >= 80:
                    if percentage == 100:
                        cities = await get_states(
                            token["auth_token"], item["country_name"]
                        )
                        item["states"] = cities
                        results.append(item)
                    else:
                        results.append(item)
            return (
                {"message": "OK", "data": results}
                if len(results) > 0
                else {"message": "no matches found"}
            )

        return {"message": "We have problems with the API of countries"}

    return {"message": "We have problems with the API of countries"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8888)
