import requests

import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import spacy

from utils.utils import (
    get_all_classes,
    get_product_name_from_url,
    get_names_by_class
)

from config import NER_MODEL_PATH, PRODUCT_TAGS


@st.cache_data
def load_ner_model() -> spacy.language.Language:
    return spacy.load(NER_MODEL_PATH)


def classify_classes(classes: set[str]) -> dict:
    product_classes = {}
    nlp = load_ner_model()
    for class_name in classes:
        prediction = nlp(class_name).cats
        if prediction["PRODUCT"] > 0.5:
            product_classes[class_name] = prediction
    return product_classes


def make_prediction(url: str):
    with st.spinner("Requesting data from url..."):
        response = requests.get(url)
        response.raise_for_status()

    product = get_product_name_from_url(url)

    if product is not None:
        st.markdown("---")
        st.write(f"Product name from url: '{product}'")
    else:
        st.markdown("---")
        st.write("Product name not found in url")

    with st.spinner("Parsing html..."):
        soup = BeautifulSoup(response.text, "html.parser")
        site_classes = get_all_classes(soup, PRODUCT_TAGS)

    with st.spinner("Classifying..."):
        product_classes_prediction = classify_classes(site_classes)

    with st.spinner("Processing result..."):
        result = {}
        for class_name in product_classes_prediction:
            products = get_names_by_class(soup, class_name)
            if len(products) > 0:
                result[class_name] = {
                    "product": products,
                    "PRODUCT": product_classes_prediction[class_name]["PRODUCT"]
                }

    return result


def render_prediction(prediction: dict) -> None:
    for class_name, info in prediction.items():
        product_list = list(info["product"])
        confidence = info["PRODUCT"]

        st.markdown("---")
        st.write(f"**{class_name}**  |  Confidence: {confidence:.7f}")

        products = pd.DataFrame({"element names": product_list})
        st.dataframe(products, use_container_width=False)
