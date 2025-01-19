import pandas as pd
from statistics import mean
import os
import re
import spacy
from spacy.language import Language
from pickle import load
import warnings

FEATURES = {
    "sentence_length_mean": None,
    "rix": None,
    "vocab_a1": None,
    "vocab_a2": None,
    "vocab_b1": None,
    "common_word_score": None,
    "rix_cws": None,
    "rix_vocab_a1": None,
    "rix_vocab_a2": None,
    "rix_vocab_b1": None,
    "slm_cws": None,
    "slm_vocab_a1": None,
    "slm_vocab_a2": None,
    "slm_vocab_b1": None,
}

cefr_vocab = pd.read_parquet("data/cefr_vocab.parq")

# If you want to adapt to High German and the use of `ß` rather than `ss`,
# change "lemma_ch" to "lemma" in the following lines.
vocab_a1 = cefr_vocab[cefr_vocab["level"] == "A1"]["lemma_ch"].values
vocab_a2 = cefr_vocab[cefr_vocab["level"] == "A2"]["lemma_ch"].values
vocab_b1 = cefr_vocab[cefr_vocab["level"] == "B1"]["lemma_ch"].values

# Load the common word scores. This list contains the lemmas
# of around ~8k most common German words.
word_scores = pd.read_parquet("data/word_scores_final_0728.parq")
word_scores = dict(zip(word_scores["lemma"], word_scores["score"]))

# Load the fitted scaler and Ridge regressor model.
with open("data/standard_scaler.pkl", "rb") as f:
    scaler = load(f)
with open("data/ridge_regressor.pkl", "rb") as f:
    clf = load(f)


@Language.component("additional_metrics")
def _additional_metrics(doc):
    """Add all necessary linguistic metrics to doc.user_data.

    Args:
        doc (Doc): A spaCy Doc object.

    Returns:
        Doc: The spaCy Doc object with additional metrics in doc.user_data.

    """

    # Calculate ratio of words that are in CEFR vocabularies.
    doc_len = len([token for token in doc if not token.is_punct and not token.like_num])

    if doc_len == 0:
        for feature in FEATURES:
            doc.user_data[feature] = None
        return doc

    # Counters for B1, A2, A1 vocabularies.
    vocab_scores = [0, 0, 0]

    # Counter for common word score.
    doc_word_scores = 0

    for token in doc:
        lemma = token.lemma_.lower()

        # A word in vocab A1 is also part of the vocabulary of A2 and B1.
        if lemma in vocab_a1:
            vocab_scores[0] += 1  # B1
            vocab_scores[1] += 1  # A2
            vocab_scores[2] += 1  # A1
        elif lemma in vocab_a2:
            vocab_scores[0] += 1  # B1
            vocab_scores[1] += 1  # A2
        elif lemma in vocab_b1:
            vocab_scores[0] += 1  # B1

        if lemma in word_scores:
            doc_word_scores += word_scores[lemma]

    # Normalize scores by document length.
    vocab_scores = list(map(lambda x: x / doc_len, vocab_scores))
    doc_word_scores = doc_word_scores / doc_len

    doc.user_data["vocab_b1"] = vocab_scores[0]
    doc.user_data["vocab_a2"] = vocab_scores[1]
    doc.user_data["vocab_a1"] = vocab_scores[2]
    doc.user_data["common_word_score"] = doc_word_scores / 1000

    # Calculate sentence length mean.
    sentences_clean = [
        [token.text for token in sent if not token.is_punct] for sent in doc.sents
    ]
    sentence_lengths = [len(sentence) for sentence in sentences_clean]
    doc.user_data["sentence_length_mean"] = mean(sentence_lengths)

    # Calculate RIX readability index.
    # Reference: https://github.com/HLasse/TextDescriptives/blob/main/src/textdescriptives/components/readability.py#L146
    long_words = len([token for token in doc if len(token) > 6])
    n_sentences = len(list(doc.sents))
    rix = long_words / n_sentences
    doc.user_data["rix"] = rix

    # Create interaction terms.
    doc.user_data["rix_cws"] = doc.user_data["rix"] * doc.user_data["common_word_score"]
    doc.user_data["rix_vocab_a1"] = doc.user_data["rix"] * doc.user_data["vocab_a1"]
    doc.user_data["rix_vocab_a2"] = doc.user_data["rix"] * doc.user_data["vocab_a2"]
    doc.user_data["rix_vocab_b1"] = doc.user_data["rix"] * doc.user_data["vocab_b1"]
    doc.user_data["slm_cws"] = (
        doc.user_data["sentence_length_mean"] * doc.user_data["common_word_score"]
    )
    doc.user_data["slm_vocab_a1"] = (
        doc.user_data["sentence_length_mean"] * doc.user_data["vocab_a1"]
    )
    doc.user_data["slm_vocab_a2"] = (
        doc.user_data["sentence_length_mean"] * doc.user_data["vocab_a2"]
    )
    doc.user_data["slm_vocab_b1"] = (
        doc.user_data["sentence_length_mean"] * doc.user_data["vocab_b1"]
    )

    return doc


# Make sure that the language model is installed.
# Loading only the necessary components into the pipeline
# speeds up the process substantially.
try:
    nlp_pipeline = spacy.load(
        "de_core_news_sm", exclude=["ner", "attribute_ruler", "morphologizer", "tagger"]
    )
except OSError:
    print("Downloading language model...")
    os.system(
        "pip install https://github.com/explosion/spacy-models/releases/download/de_core_news_sm-3.7.0/de_core_news_sm-3.7.0-py3-none-any.whl"
    )
    nlp_pipeline = spacy.load(
        "de_core_news_sm", exclude=["ner", "attribute_ruler", "morphologizer", "tagger"]
    )

nlp_pipeline.add_pipe("additional_metrics")


def _extract_features(text):
    """Extract syntactical and semantic features from text.

    Args:
        text (str): The text to be analyzed.

    Returns:
        pd.DataFrame: A DataFrame containing the linguistic features of the text.

    """
    doc = nlp_pipeline(text)
    row_features = {}
    for feature in FEATURES:
        row_features[feature] = doc.user_data[feature]
    return pd.DataFrame.from_dict(row_features, orient="index").T


def _punctuate_lines(text):
    """Add a dot to lines that do not end with a dot.
    Remove bullet points, multiple spaces and line breaks.

    Args:
        text (str): The text to be fixed.

    Returns:
        str: The fixed text with proper punctuation.
    """
    lines = text.splitlines()
    lines = [x.strip() for x in lines]
    lines = [x for x in lines if x != ""]
    lines_punct = []
    for line in lines:
        # Properly punctuate lines.
        if line[-1] not in [".", "?", "!"]:
            line = line + "."
        # Remove bullet points.
        if line[0] in ["-", "•"]:
            line = line[1:].strip()
        # Remove multiple spaces.
        line = re.sub(r"\s+", " ", line)
        lines_punct.append(line)

    return " ".join(lines_punct)



def _calculate_score(data):
    """Calculate the understandability of a text based on its features."""
    # Scale data and predict understandability.
    X = scaler.transform(data)
    understandability = 1 - clf.predict(X)[0]

    # Spread the score and shift it to a range from -10 to 10.
    score = understandability * 2.5 + 6.6
    
    # Clip to range -10 to 10.
    if score > 10:
        score = 10
    elif score < -10:
        score = -10
    return score


def get_zix(text):
    """Get an understandability score from a text.

    Args:
        text (str): The text to be analyzed.

    Returns:
        float: The understandability score of the text.
    """

    # If text is not a string, raise an error.
    if not isinstance(text, str):
        warnings.warn("The given value is not of type text. Returning None.")
        return None

    # If text is an empty string return None.
    if text == "":
        warnings.warn("Input is an empty string.")
        return None

    # Spacys max_length is set to a default of 1,000,000 characters
    # which roughly corresponds to 10 GB RAM.
    if len(text) > 1_000_000:
        raise ValueError(
            """Text is too long. 
            Please provide a text with less than 1,000,000 characters."""
        )

    text = _punctuate_lines(text)
    features = _extract_features(text)
    if features.isnull().values.any():
        return None
    score = _calculate_score(features)
    return score


def get_cefr(zix_score):
    """Get the CEFR level from a ZIX score.

    Args:
        zix_score (int, float): The ZIX score of the text.

    Returns:
        str: The CEFR level of the text.

    """
    if zix_score is None:
        warnings.warn("The given ZIX score to the function is invalid (None).")
        return None
    if zix_score >= 4.0:
        return "A1"
    elif zix_score >= 2.0:
        return "A2"
    elif zix_score >= 0:
        return "B1"
    elif zix_score >= -2:
        return "B2"
    elif zix_score >= -4:
        return "C1"
    else:
        return "C2"
