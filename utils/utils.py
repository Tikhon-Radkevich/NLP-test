import json
import random
from dataclasses import dataclass

import aiohttp
import asyncio
from bs4 import BeautifulSoup, Tag

from config import PRODUCT_TAGS, TITLE_KEY_WORDS, PRODUCT_KEY_CLASSES, MAX_PRODUCT_NAME_LENGTH, NER_DATA_FILE_PATH


@dataclass
class Response:
    text: str
    url: str
    status: int


async def get_html(session: aiohttp.ClientSession, url: str) -> Response:
    try:
        async with session.get(url, timeout=7, max_redirects=10) as response:
            response.raise_for_status()
            response_obj = Response(await response.text(), url, response.status)
            return response_obj
    except Exception as e:
        response_obj = Response(str(e), url, 0)
        return response_obj


async def get_html_async(urls: list[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [get_html(session, url) for url in urls]
        return await asyncio.gather(*tasks)


def collect_pages(urls: list[str]):
    return asyncio.run(get_html_async(urls))


def get_product_name_from_url(url: str) -> None | str:
    url_items = url.split("/")
    if len(url_items) < 2:
        return

    if url_items[-2] != "products":
        return None

    product = url_items[-1]
    if product == "":
        return None

    if "?" in product:
        product = product.split("?")[0]

    if any(char.isdigit() for char in product):
        return None

    product = product.replace("-", " ").lower()
    return product


def find_matches(html_soup: BeautifulSoup, product_name: str):
    def tag_filter(tag):
        tag_text = tag.get_text().lower()
        tag_striped_text = tag.get_text(strip=True).lower()

        is_same_name = tag_striped_text in product_name or product_name in tag_striped_text
        name_length_con = (len(tag_text) < MAX_PRODUCT_NAME_LENGTH) and (
                    len(tag_striped_text) < MAX_PRODUCT_NAME_LENGTH)
        no_empty_text_con = tag_striped_text != ""
        tag_mane_in_product_tags_con = tag.name in PRODUCT_TAGS

        return all((tag_mane_in_product_tags_con, name_length_con, no_empty_text_con, is_same_name))

    return html_soup.find_all(tag_filter)


def class_filter(tag: Tag):
    tag_text = tag.get_text().lower()
    tag_striped_text = tag.get_text(strip=True).lower()

    name_length_con = (len(tag_text) < MAX_PRODUCT_NAME_LENGTH) and (len(tag_striped_text) < MAX_PRODUCT_NAME_LENGTH)
    no_empty_text_con = tag_striped_text != ""
    tag_mane_in_product_tags_con = tag.name in PRODUCT_TAGS

    return all((tag_mane_in_product_tags_con, name_length_con, no_empty_text_con))


def get_all_classes(soup: BeautifulSoup, tags=True):
    all_classes = set()

    for element in soup.find_all(tags):
        classes = element.get("class", [])
        for class_name in classes:
            all_classes.add(class_name)

    return all_classes


def get_names_by_class(soup: BeautifulSoup, class_name: str):
    elements = soup.find_all(class_=class_name)
    names = set()

    for element in elements:
        product_name = element.get_text()
        striped_text = element.get_text(strip=True).strip("\n")
        if product_name != "" and len(product_name) < MAX_PRODUCT_NAME_LENGTH and striped_text != "":
            names.add(element.get_text(strip=True).strip("\n"))
    return names


def get_product_classes_and_names(soup: BeautifulSoup, matches: list[Tag]):
    product_key_classes = PRODUCT_KEY_CLASSES.copy()
    all_classes = get_all_classes(soup)
    product_classes = set()
    product_names = set()

    for match in matches:
        product_names.add(match.get_text(strip=True).strip("\n").lower())

        for class_name in match.get("class", []):
            if any(key_word in class_name.lower() for key_word in TITLE_KEY_WORDS):
                product_key_classes.add(class_name)

        for page_class in all_classes:
            if any(key_class in page_class.lower() for key_class in product_key_classes):
                product_classes.add(page_class)

    for class_ in product_classes:
        elements = soup.find_all(name=class_filter, class_=class_)
        for element in elements:
            product_names.add(element.get_text(strip=True).strip("\n").lower())

    return all_classes, product_classes, product_names


def load_ner_data_file() -> dict:
    with open(NER_DATA_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_classes_ner_data_file() -> tuple[set[str], set[str], set[str]]:
    dataset = load_ner_data_file()

    title_classes = set()
    used_urls = set()
    all_classes = set()

    for url, data in dataset.items():
        if len(data["product_classes"]) < 0:
            continue

        used_urls.add(url)

        for product_class in data["product_classes"]:
            title_classes.add(product_class)

        for class_ in data["all_classes"]:
            all_classes.add(class_)

    return title_classes, all_classes, used_urls


def make_dataset(all_classes, title_classes, n_samples_with_title_or_name_words, n_one_word_samples, n_other_samples):
    all_classes = all_classes.difference(title_classes)

    product_or_title_or_name_in_class = set()
    for class_ in all_classes:
        if "product" in class_ or "title" in class_ or "name" in class_:
            product_or_title_or_name_in_class.add(class_)

    all_classes = all_classes.difference(product_or_title_or_name_in_class)

    one_word_classes = set()
    for class_ in all_classes:
        if len(class_.split("-")) == 1:
            one_word_classes.add(class_)

    all_classes = all_classes.difference(one_word_classes)

    no_product_data = (
            random.sample(list(product_or_title_or_name_in_class), n_samples_with_title_or_name_words)
            + random.sample(list(one_word_classes), n_one_word_samples)
            + random.sample(list(all_classes), n_other_samples)
            + ["title", "product", "name", "page-title"]
    )

    ner_dataset = []

    for class_ in title_classes:
        ner_dataset.append((class_, {"cats": {"PRODUCT": 1, "NOT_PRODUCT": 0}}))

    for class_ in no_product_data:
        ner_dataset.append((class_, {"cats": {"PRODUCT": 0, "NOT_PRODUCT": 1}}))

    return ner_dataset
