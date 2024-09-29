import aiohttp
import asyncio
import pandas as pd

from config import URL_LIST_FILE_PATH, URL_LIST_WITH_STATUS_FILE_PATH


async def fetch_status(session: aiohttp.ClientSession, url: str):
    try:
        async with session.get(url, timeout=30, max_redirects=10) as response:
            return response.status, url
    except Exception as e:
        return str(e), url


async def check_urls_async(urls: list[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_status(session, url) for url in urls]
        return await asyncio.gather(*tasks)


def check_urls(urls: list[str]):
    return asyncio.run(check_urls_async(urls))


def main():
    urls_df = pd.read_csv(URL_LIST_FILE_PATH)
    urls_df.rename(columns={"max(page)": "url"}, inplace=True)

    urls_list = urls_df["url"].tolist()
    results = check_urls(urls_list)

    urls_df["status_code"] = [result[0] for result in results]

    urls_df.to_csv(URL_LIST_WITH_STATUS_FILE_PATH, index=False)


if __name__ == "__main__":
    main()
