import json

from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

from utils.utils import collect_pages, get_product_name_from_url, find_matches, get_product_classes_and_names
from config import URL_LIST_WITH_STATUS_FILE_PATH, NER_DATA_FILE_PATH


def main():
    urls_df = pd.read_csv(URL_LIST_WITH_STATUS_FILE_PATH)
    urls_df = urls_df[urls_df["status_code"] == "200"]
    urls_df["product_name"] = urls_df["url"].apply(get_product_name_from_url)
    urls_df = urls_df.dropna()

    urls_list = urls_df["url"].tolist()
    results = collect_pages(urls_list)

    dataset = {}

    for result in tqdm(results):
        if result.status != 200:
            continue
        product = get_product_name_from_url(result.url)
        soup = BeautifulSoup(result.text, "html.parser")

        matches = find_matches(soup, product)
        all_classes, product_classes, product_names = get_product_classes_and_names(soup, matches)

        dataset[result.url] = {
            "product": product,
            "all_classes": list(all_classes),
            "product_classes": list(product_classes),
            "product_names": list(product_names),
        }

    with open(NER_DATA_FILE_PATH, "w", encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
