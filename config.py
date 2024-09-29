import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
URL_LIST_FILE_PATH = os.path.join(DATA_DIR, "URL_list.csv")
URL_LIST_WITH_STATUS_FILE_PATH = os.path.join(DATA_DIR, "URL_list_with_status.csv")
NER_DATA_FILE_PATH = os.path.join(DATA_DIR, "ner_data.json")

MODEL_DIR = os.path.join(ROOT_DIR, "models")
NER_MODEL_PATH = os.path.join(MODEL_DIR, "ner_model")

MAX_PRODUCT_NAME_LENGTH = 70
PRODUCT_TAGS = ["div", "a", "h1", "h2", "h3", "button", "p", "span"]
TITLE_KEY_WORDS = ["product", "title"]
PRODUCT_KEY_CLASSES = {
    "product-title",
    "product-name",
    "product_title",
    "product_name",
    "product__title",
    "product__name",
}
