import requests

base_url = "https://api.mangadex.org"


async def search_mangas(text: str) -> dict:
    url = f"{base_url}/manga"
    response = requests.get(url, params={"title": text})
    data = response.json()["data"]
    mangas = {manga["attributes"]["title"]["en"]: manga["id"] for manga in data}
    print(f"mangas received from search {text}: {mangas}")
    return mangas
