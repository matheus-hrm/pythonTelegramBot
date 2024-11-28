import requests

base_url = "https://api.mangadex.org"


async def search_mangas(text: str) -> dict:
    url = f"{base_url}/manga"
    try:
        response = requests.get(url, params={"title": text})
        data = response.json()["data"]

        mangas = {manga["attributes"]["title"]["en"]: manga["id"] for manga in data}

        return mangas
    except Exception as e:
        print(f"Error searching mangas: {e}")
        return {}


async def get_manga_chapters(manga_id: str, lang: str, offset: int = 0) -> dict:
    url = f"{base_url}/manga/{manga_id}/feed"
    try:
        response = requests.get(
            url,
            params={
                "translatedLanguage[]": lang,
                "order[chapter]": "desc",
                "limit": 10,
                "offset": offset,
            },
        )
        data = response.json()["data"]

        chapters = {
            f"{chapter['attributes']['chapter']}"
            f"- {chapter['attributes']['title']}": chapter["id"]
            for chapter in data
        }

        return chapters
    except Exception as e:
        print(f"Error getting manga chapters: {e}")
        return {}


async def get_chapter_pages(chapter_id: str, quality: bool) -> list:
    url = f"{base_url}/at-home/server/{chapter_id}"
    try:
        response = requests.get(url)
        data = response.json()
        if not quality:
            quality = "dataSaver"
        else:
            quality = "data"
        pages = data["chapter"][quality]
        hash = data["chapter"]["hash"]
        page_url = data["baseUrl"]

        if not pages:
            return []

        return [f"{page_url}/data/{hash}/{page}" for page in pages]

    except Exception as e:
        print(f"Error getting chapter pages: {e}")
        return []
