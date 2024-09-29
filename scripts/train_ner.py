import random

import spacy
from spacy.training import Example

from utils.utils import extract_classes_ner_data_file, make_dataset
from config import NER_MODEL_PATH


def main():
    n_samples_with_title = 200
    n_one_word_samples = 30
    n_other_samples = 500
    n_epochs = 20
    drop = 0.5

    title_classes, all_classes, _ = extract_classes_ner_data_file()
    ner_dataset = make_dataset(all_classes, title_classes, n_samples_with_title, n_one_word_samples, n_other_samples)

    nlp = spacy.blank("en")
    text_classifier = nlp.add_pipe("textcat", last=True)

    text_classifier.add_label("PRODUCT")
    text_classifier.add_label("NOT_PRODUCT")

    print(f"Training the model with {n_epochs} epochs...")
    nlp.begin_training()
    for epoch in range(n_epochs):
        random.shuffle(ner_dataset)
        losses = {}

        for text, annotations in ner_dataset:
            example = Example.from_dict(nlp.make_doc(text), annotations)
            nlp.update([example], drop=drop, losses=losses)

        print(f"Epoch {epoch} - Losses: {losses}")

    print("Saving the model...")
    nlp.to_disk(NER_MODEL_PATH)


if __name__ == "__main__":
    main()
