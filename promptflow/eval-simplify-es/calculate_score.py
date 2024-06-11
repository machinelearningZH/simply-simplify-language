
from promptflow.core import tool
import pandas as pd
import numpy as np
import spacy
from spacy.language import Language
import textdescriptives as td

import re


def get_word_scores():
    """Get commond word scores from the parquet file.

    This is a list of common German words in texts written in Einfache and Leichte Sprache. We use this ranking to calculate, how common the vocabulary in the text ist and therefore how easy the text is to understand.

    We have lemmatized and lower cased the words. Also note that the German `ß` has been replaced with `ss`.
    """
    word_scores = pd.read_parquet("word_scores.parq")
    word_scores = dict(zip(word_scores["lemma"], word_scores["score"]))
    return word_scores


def get_nlp_pipeline():
    """Get NLP pipeline.

    We create a spacy pipeline with a custom component to calculate the common word score. We also add the textdescriptives components for readability and descriptive statistics.
    """

    word_scores = get_word_scores()

    @Language.component("common_word_score")
    def extract_common_word_score(doc):
        """Extract common word score and add to doc.user_data."""

        # Calculate common word score.
        doc_len = len([x for x in doc if not x.is_punct and not x.like_num])
        doc_scores = 0
        for token in doc:
            lemma = token.lemma_.lower()
            if lemma in word_scores:
                doc_scores += word_scores[lemma]

        doc_scores = doc_scores / doc_len
        doc.user_data["common_word_score"] = doc_scores / 1000

        return doc

    nlp = spacy.load("de_core_news_sm")
    nlp.add_pipe("textdescriptives/descriptive_stats")
    nlp.add_pipe("textdescriptives/readability")
    nlp.add_pipe("common_word_score")
    return nlp


def extract_text_features(text):
    """Extract text features from text.

    We use the spacy pipeline to extract text features needed for the understandability formula and return them as a DataFrame.
    """
    doc = nlp(text)
    row_metrics = td.extractors.extract_dict(
        doc,
        metrics=[
            "descriptive_stats",
            "readability",
        ],
        include_text=False,
    )
    for metric in [
        "common_word_score",
    ]:
        row_metrics[0][metric] = doc.user_data[metric]
    return pd.DataFrame.from_dict(row_metrics)


def punctuate_paragraphs_and_bulleted_lists(text):
    """Add a dot to lines that do not end with a dot and do some additional clean up to correctly calculate the understandability score.

    Texts in Einfache and Leichte Sprache often do not end sentences with a dot. This function adds a dot to lines that do not end with a dot. It also removes bullet points and hyphens from the beginning of lines and removes all line breaks and multiple spaces. This is necessary to correctly calculate the understandability score.
    """

    # Add a space to the end of the text to properly process the last sentence.
    text = text + " "

    # This regex pattern matches lines that do not end with a dot and are not empty.
    pattern = r"(?<!(\.))[^\n]$"

    # Replace lines not ending with a dot with the same line plus a dot.
    # The 're.MULTILINE' flag treats each line as a separate string.
    new_text = re.sub(pattern, r"\g<0>.", text, flags=re.MULTILINE)

    # Remove bullet points and hyphens from the beginning of lines.
    new_text = re.sub(r"^[\s]*[-•]", "", new_text, flags=re.MULTILINE)

    # Remove all line breaks and multiple spaces.
    new_text = new_text.replace("\n", " ")
    new_text = re.sub(r"\s+", " ", new_text)

    return new_text.strip()


def calculate_understandability(data):
    """Calculate understandability score from text metrics.

    We derived this formula from a dataset of legal and administrative texts, as well as Einfache and Leichte Sprache. We trained a Logistic Regression model to differentiate between complex and simple texts. From the most significant model coefficients we devised this formula to estimate a text's understandability.

    It is not a perfect measure, but it gives a good indication of how easy a text is to understand.

    We do not take into account a couple of text features that are relevant to understandability, such as the use of passive voice, the use of pronouns, or the use of complex sentence structures. These features are not easily extracted from text and would require a more complex model to calculate.
    """
    cws = (data.common_word_score - 7.8) / 1.1
    rix = (data.rix - 3.9) / 1.7
    sls = (data.sentence_length_std - 6.4) / 4.2
    slm = (data.sentence_length_mean - 11.7) / 3.7
    cws = 1 - cws

    score = ((cws * 0.2 + rix * 0.325 + sls * 0.225 + slm * 0.15) + 1.3) * 3.5

    # We clip the score to a range of 0 to 20.
    score = 20 - (score.values[0])
    if score < 0:
        score = 0
    if score > 20:
        score = 20
    return score





def get_understandability(text):
    """Get understandability score from text."""
    # Replace newlines with punctuation, so that paragraphs
    # and bullet point lists are not counted as complex sentences.
    text = punctuate_paragraphs_and_bulleted_lists(text)

    features = extract_text_features(text)
    return calculate_understandability(features)



nlp = get_nlp_pipeline()

@tool
def calculate_score(text: str) -> float:
    score = get_understandability(text)
    return float(score)
