# ---------------------------------------------------------------
# Imports

import streamlit as st

st.set_page_config(layout="wide")

import os
import re
from datetime import datetime
import time
import base64
from docx import Document
from docx.shared import Pt, Inches
import io
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

import logging

logging.basicConfig(
    filename="app.log",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.WARNING,
)

import pandas as pd
import numpy as np
import spacy
from spacy.language import Language
import textdescriptives as td

from openai import OpenAI
from anthropic import Anthropic
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from utils_sample_texts import (
    SAMPLE_TEXT_01,
)

from utils_prompts import (
    SYSTEM_MESSAGE_ES,
    SYSTEM_MESSAGE_LS,
    RULES_ES,
    RULES_LS,
    REWRITE_COMPLETE,
    REWRITE_CONDENSED,
    CLAUDE_TEMPLATE_ES,
    CLAUDE_TEMPLATE_LS,
    CLAUDE_TEMPLATE_ANALYSIS_ES,
    CLAUDE_TEMPLATE_ANALYSIS_LS,
    OPENAI_TEMPLATE_ES,
    OPENAI_TEMPLATE_LS,
    OPENAI_TEMPLATE_ANALYSIS_ES,
    OPENAI_TEMPLATE_ANALYSIS_LS,
)

CLAUDE_TEMPLATES = [
    CLAUDE_TEMPLATE_ES,
    CLAUDE_TEMPLATE_LS,
    CLAUDE_TEMPLATE_ANALYSIS_ES,
    CLAUDE_TEMPLATE_ANALYSIS_LS,
]

OPENAI_TEMPLATES = [
    OPENAI_TEMPLATE_ES,
    OPENAI_TEMPLATE_LS,
    OPENAI_TEMPLATE_ANALYSIS_ES,
    OPENAI_TEMPLATE_ANALYSIS_LS,
]


# ---------------------------------------------------------------
# Constants

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

HAIKU = "claude-3-haiku-20240307"
SONNET = "claude-3-sonnet-20240229"
OPUS = "claude-3-opus-20240229"

M_LARGE = "mistral-large-2402"

GPT4 = "gpt-4-turbo"
GPT4o = "gpt-4o"

# From our testing we derive a sensible temperature of 0.5 as a good trade-off between creativity and coherence. Adjust this to your needs.
TEMPERATURE = 0.5

# Height of the text areas for input and output.
TEXT_AREA_HEIGHT = 600

# Maximum number of characters for the input text.
# This is way below the context window sizes of the models.
# Adjust to your needs. However, we found that users can work and validate better when we nudge to work with shorter texts.
MAX_CHARS_INPUT = 10_000


USER_WARNING = """<sub>⚠️ Achtung: Diese App ist ein Prototyp. Nutze die App :red[**nur für öffentliche, nicht sensible Daten**]. Die App liefert lediglich einen Textentwurf. Überprüfe das Ergebnis immer und passe es an, wenn nötig. Die aktuelle App-Version ist v0.1. Die letzte Aktualisierung war am 1.6.2024."""


# Constants for the formatting of the Word document that can be downloaded.
FONT_WORDDOC = "Arial"
FONT_SIZE_HEADING = 12
FONT_SIZE_PARAGRAPH = 9
FONT_SIZE_FOOTER = 7


# Limits for the understandability score to determine if the text is easy, medium or hard to understand.
LIMIT_HARD = 13
LIMIT_MEDIUM = 16


# ---------------------------------------------------------------
# Functions


@st.cache_resource
def get_project_info():
    """Get markdown for project information that is shown in the expander section at the top of the app."""
    with open("utils_expander.md") as f:
        return f.read()


def create_project_info(project_info):
    """Create expander for project info. Add the image in the middle of the content."""
    with st.expander("Detaillierte Informationen zum Projekt"):
        project_info = project_info.split("### Image ###")
        st.markdown(project_info[0], unsafe_allow_html=True)
        st.image("score.png", use_column_width=True)
        st.markdown(project_info[1], unsafe_allow_html=True)


@st.cache_resource
def get_word_scores():
    """Get commond word scores from the parquet file.

    This is a list of common German words in texts written in Einfache and Leichte Sprache. We use this ranking to calculate, how common the vocabulary in the text ist and therefore how easy the text is to understand.

    We have lemmatized and lower cased the words. Also note that the German `ß` has been replaced with `ss`.
    """
    word_scores = pd.read_parquet("word_scores.parq")
    word_scores = dict(zip(word_scores["lemma"], word_scores["score"]))
    return word_scores


@st.cache_resource
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


def get_cefr_level(score):
    """Get CEFR level from understandability score.

    We calculated these ranges by scoring various text samples where we had an approximate idea of their CEFR level. Again these ranges are not perfect, but give a good indication of the CEFR level.
    """
    if score >= 18.3:
        return "A1"
    elif score >= 17.7 and score < 18.3:
        return "A2"
    elif score >= 17.5 and score < 17.7:
        return "A2 bis B1"
    elif score >= 15.7 and score < 17.5:
        return "B1"
    elif score >= 13.7 and score < 15.7:
        return "B2"
    elif score >= 12.4 and score < 13.7:
        return "C1"
    elif score >= 12.2 and score < 12.4:
        return "C1 bis C2"
    elif score < 12.2:
        return "C2"


def get_understandability(text):
    """Get understandability score from text."""
    # Replace newlines with punctuation, so that paragraphs
    # and bullet point lists are not counted as complex sentences.
    text = punctuate_paragraphs_and_bulleted_lists(text)

    features = extract_text_features(text)
    return calculate_understandability(features)


def create_prompt(text, prompt_es, prompt_ls, analysis_es, analysis_ls, analysis):
    """Create prompt and system message according the app settings."""
    if analysis:
        if leichte_sprache:
            final_prompt = analysis_ls.format(rules=RULES_LS, prompt=text)
            system = SYSTEM_MESSAGE_LS
        else:
            final_prompt = analysis_es.format(rules=RULES_ES, prompt=text)
            system = SYSTEM_MESSAGE_ES
    else:
        if leichte_sprache:
            if condense_text:
                final_prompt = prompt_ls.format(
                    rules=RULES_LS, completeness=REWRITE_CONDENSED, prompt=text
                )
            else:
                final_prompt = prompt_ls.format(
                    rules=RULES_LS, completeness=REWRITE_COMPLETE, prompt=text
                )
            system = SYSTEM_MESSAGE_LS
        else:
            final_prompt = prompt_es.format(
                rules=RULES_ES, completeness=REWRITE_COMPLETE, prompt=text
            )
            system = SYSTEM_MESSAGE_ES
    return final_prompt, system


def get_result_from_response(response):
    """Extract text between tags from response."""
    if leichte_sprache:
        result = re.findall(
            r"<leichtesprache>(.*?)</leichtesprache>", response, re.DOTALL
        )
    else:
        result = re.findall(
            r"<einfachesprache>(.*?)</einfachesprache>", response, re.DOTALL
        )
    result = "\n".join(result)
    return result.strip()


@st.cache_resource
def get_anthropic_client():
    return Anthropic(api_key=ANTHROPIC_API_KEY)


def invoke_anthropic_model(
    text,
    max_tokens=4096,
    temperature=TEMPERATURE,
    modelId=HAIKU,
    analysis=False,
):
    """Invoke Anthropic model."""
    final_prompt, system = create_prompt(text, *CLAUDE_TEMPLATES, analysis)
    try:
        message = anthropic_client.messages.create(
            model=modelId,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": final_prompt,
                }
            ],
        )
        message = message.content[0].text.strip()
        return True, get_result_from_response(message)
    except Exception as e:
        return False, e


@st.cache_resource
def get_openai_client():
    return OpenAI()


def invoke_openai_model(
    text,
    modelId="gpt-4o",
    temperature=TEMPERATURE,
    max_tokens=4096,
    analysis=False,
):
    """Invoke OpenAI model."""
    final_prompt, system = create_prompt(text, *OPENAI_TEMPLATES, analysis)
    try:
        message = openai_client.chat.completions.create(
            model=modelId,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": final_prompt},
            ],
        )
        message = message.choices[0].message.content.strip()
        return True, get_result_from_response(message)
    except Exception as e:
        print(f"Error: {e}")
        return False, e


@st.cache_resource
def get_mistral_client():
    return MistralClient(api_key=MISTRAL_API_KEY)


def invoke_mistral_model(
    text, modelId="mistral-large-latest", temperature=TEMPERATURE, analysis=False
):
    """Invoke Mistral model."""
    # Our Claude templates seem to work fine for Mistral as well.
    final_prompt, system = create_prompt(text, *CLAUDE_TEMPLATES, analysis)
    messages = [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content=final_prompt),
    ]
    try:
        message = mistral_client.chat(
            model=modelId,
            messages=messages,
            temperature=temperature,
        )
        message = message.choices[0].message.content.strip()
        return True, get_result_from_response(message)
    except Exception as e:
        print(f"Error: {e}")
        return False, e


def enter_sample_text():
    """Enter sample text into the text input in the left column."""
    st.session_state.key_textinput = SAMPLE_TEXT_01


def get_one_click_results():
    """Send prompt to all models in parallel and collect results."""

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_mistral = executor.submit(
            invoke_mistral_model,
            text_input,
            modelId=M_LARGE,
        )
        future_gpt = executor.submit(
            invoke_openai_model,
            text_input,
            modelId=GPT4,
        )
        future_gpto = executor.submit(
            invoke_openai_model,
            text_input,
            modelId=GPT4o,
        )
        future_claude_v3_haiku = executor.submit(
            invoke_anthropic_model,
            text_input,
            modelId=HAIKU,
        )
        future_claude_v3_sonnet = executor.submit(
            invoke_anthropic_model,
            text_input,
            modelId=SONNET,
        )
        future_claude_v3_opus = executor.submit(
            invoke_anthropic_model,
            text_input,
            modelId=OPUS,
        )

    success_mistral, response_mistral = future_mistral.result()
    zix_mistral = get_understandability(response_mistral)

    success_gpt, response_gpt = future_gpt.result()
    zix_gpt = get_understandability(response_gpt)

    success_gpto, response_gpto = future_gpto.result()
    zix_gpto = get_understandability(response_gpto)

    success_claude_v3_haiku, response_claude_v3_haiku = future_claude_v3_haiku.result()
    zix_claude_v3_haiku = get_understandability(response_claude_v3_haiku)

    success_claude_v3_sonnet, response_claude_v3_sonnet = (
        future_claude_v3_sonnet.result()
    )
    zix_claude_v3_sonnet = get_understandability(response_claude_v3_sonnet)

    success_claude_v3_opus, response_claude_v3_opus = future_claude_v3_opus.result()
    zix_claude_v3_opus = get_understandability(response_claude_v3_opus)

    response = []

    if leichte_sprache:
        response.append(
            "Die Sprachmodelle haben versucht, den Ausgangstext in **Leichte Sprache** umzuschreiben."
        )
    else:
        response.append(
            "Die Sprachmodelle haben versucht, den Text in **Einfache Sprache** umzuschreiben."
        )

    if success_mistral:
        tmp = (
            f"\n----- Ergebnis von Mistral Large (Verständlichkeit: {zix_mistral :.0f} Punkte) -----"
            + "\n\n"
            + response_mistral
        )
        response.append(tmp)
    if success_claude_v3_haiku:
        tmp = (
            f"\n----- Ergebnis von Claude 3 Haiku (Verständlichkeit: {zix_claude_v3_haiku :.0f} Punkte) -----"
            + "\n\n"
            + response_claude_v3_haiku
        )
        response.append(tmp)
    if success_claude_v3_sonnet:
        tmp = (
            f"\n----- Ergebnis von Claude 3 Sonnet (Verständlichkeit: {zix_claude_v3_sonnet :.0f} Punkte) -----"
            + "\n\n"
            + response_claude_v3_sonnet
        )
        response.append(tmp)
    if success_claude_v3_opus:
        tmp = (
            f"\n----- Ergebnis von Claude 3 Opus (Verständlichkeit: {zix_claude_v3_opus :.0f} Punkte) -----"
            + "\n\n"
            + response_claude_v3_opus
        )
        response.append(tmp)
    if success_gpt:
        tmp = (
            f"\n------Ergebnis von GPT-4 (Verständlichkeit: {zix_gpt :.0f} Punkte) -----"
            + "\n\n"
            + response_gpt
        )
        response.append(tmp)
    if success_gpto:
        tmp = (
            f"\n----- Ergebnis von GPT-4o (Verständlichkeit: {zix_gpto :.0f} Punkte) -----"
            + "\n\n"
            + response_gpto
        )
        response.append(tmp)
    response = "\n\n\n".join(response)
    if response == "":
        return False, "Es ist ein Fehler aufgetreten."
    return True, response


def create_download_link(text_input, response, analysis=False):
    """Create a downloadable Word document and download link of the results."""
    document = Document()

    h1 = document.add_heading("Ausgangstext")
    p1 = document.add_paragraph("\n" + text_input)

    if analysis:
        h2 = document.add_heading(f"Analyse von Sprachmodell {model_choice}")
    elif do_one_click:
        h2 = document.add_heading(f"Vereinfachte Texte von Sprachmodellen")
    else:
        h2 = document.add_heading("Vereinfachter Text von Sprachmodell")

    p2 = document.add_paragraph(response)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    models_used = model_choice
    if do_one_click:
        models_used = "Mistral Large, Claude 3 Haiku, Claude 3 Sonnet, Claude 3 Opus, GPT-4, GPT-4o"
    footer = document.sections[0].footer
    footer.paragraphs[
        0
    ].text = f"Erstellt am {timestamp} mit der Prototyp-App «Einfache Sprache», Statistisches Amt, Kanton Zürich.\nSprachmodell(e): {models_used}\nVerarbeitungszeit: {time_processed:.1f} Sekunden"

    # Set font for all paragraphs.
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            run.font.name = FONT_WORDDOC

    # Set font size for all headings.
    for paragraph in [h1, h2]:
        for run in paragraph.runs:
            run.font.size = Pt(FONT_SIZE_HEADING)

    # Set font size for all paragraphs.
    for paragraph in [p1, p2]:
        for run in paragraph.runs:
            run.font.size = Pt(FONT_SIZE_PARAGRAPH)

    # Set font and font size for footer.
    for run in footer.paragraphs[0].runs:
        run.font.name = "Arial"
        run.font.size = Pt(FONT_SIZE_FOOTER)

    section = document.sections[0]
    section.page_width = Inches(8.27)  # Width of A4 paper in inches
    section.page_height = Inches(11.69)  # Height of A4 paper in inches

    io_stream = io.BytesIO()
    document.save(io_stream)

    # # A download button unfortunately resets the app. So we use a link instead.
    # https://github.com/streamlit/streamlit/issues/4382#issuecomment-1223924851
    # https://discuss.streamlit.io/t/creating-a-pdf-file-generator/7613?u=volodymyr_holomb

    b64 = base64.b64encode(io_stream.getvalue())
    file_name = "Ergebnis.docx"

    if do_one_click:
        caption = "Vereinfachte Texte herunterladen"
    else:
        caption = "Vereinfachten Text herunterladen"

    if analysis:
        file_name = "Analyse.docx"
        caption = "Analyse herunterladen"
    download_url = f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{file_name}">{caption}</a>'
    st.markdown(download_url, unsafe_allow_html=True)


def clean_log(text):
    """Remove linebreaks and tabs from log messages that otherwise would yield problems when parsing the logs."""
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    return text


def log_event(
    text,
    response,
    do_analysis,
    do_simplification,
    do_one_click,
    leichte_sprache,
    model_choice,
    time_processed,
    success,
):
    """Log event."""
    log_string = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    log_string += f"\t{clean_log(text)}"
    log_string += f"\t{clean_log(response)}"
    log_string += f"\t{do_analysis}"
    log_string += f"\t{do_simplification}"
    log_string += f"\t{do_one_click}"
    log_string += f"\t{leichte_sprache}"
    log_string += f"\t{model_choice}"
    log_string += f"\t{time_processed:.3f}"
    log_string += f"\t{success}"

    logging.warning(log_string)


# ---------------------------------------------------------------
# Main

anthropic_client = get_anthropic_client()
openai_client = get_openai_client()
mistral_client = get_mistral_client()

nlp = get_nlp_pipeline()
project_info = get_project_info()


st.markdown("## 🙋‍♀️ Sprache einfach vereinfachen")
create_project_info(project_info)
st.caption(USER_WARNING, unsafe_allow_html=True)
st.markdown("---")

# Set up first row with all buttons and settings.
button_cols = st.columns([1, 1, 1, 2])
with button_cols[0]:
    st.button(
        "Beispiel einfügen",
        on_click=enter_sample_text,
        use_container_width=True,
        type="secondary",
        help="Fügt einen Beispieltext ein.",
    )
    do_analysis = st.button(
        "Analysieren",
        use_container_width=True,
        help="Analysiert deinen Ausgangstext Satz für Satz.",
    )
with button_cols[1]:
    do_simplification = st.button(
        "Vereinfachen",
        use_container_width=True,
        help="Vereinfacht deinen Ausgangstext.",
    )
    do_one_click = st.button(
        "🚀 One-Klick",
        use_container_width=True,
        help="Schickt deinen Ausgangstext gleichzeitig an alle Modelle.",
    )
with button_cols[2]:
    leichte_sprache = st.toggle(
        "Leichte Sprache",
        value=False,
        help="**Schalter aktiviert**: «Leichte Sprache». **Schalter nicht aktiviert**: «Einfache Sprache».",
    )
    if leichte_sprache:
        condense_text = st.toggle(
            "Text verdichten",
            value=True,
            help="**Schalter aktiviert**: Modell konzentriert sich auf essentielle Informationen und versucht, Unwichtiges wegzulassen. **Schalter nicht aktiviert**: Modell versucht, alle Informationen zu übernehmen.",
        )
with button_cols[3]:
    model_choice = st.radio(
        label="Sprachmodell",
        options=(
            "Mistral Large",
            "Claude 3 Haiku",
            "Claude 3 Sonnet",
            "Claude 3 Opus",
            "GPT-4",
            "GPT-4o",
        ),
        index=5,
        horizontal=True,
        help="Alle Modelle liefern je nach Ausgangstext meist gute bis sehr gute Ergebnisse und sind alle einen Versuch wert. Claude Haiku und GPT-4o sind am schnellsten. Mehr Details siehe Infobox oben auf der Seite.",
    )

# Instantiate empty containers for the text areas.
cols = st.columns([2, 2, 1])

with cols[0]:
    source_text = st.container()
with cols[1]:
    placeholder_result = st.empty()
with cols[2]:
    placeholder_analysis = st.empty()

# Populate containers.
with source_text:
    text_input = st.text_area(
        "Ausgangstext, den du vereinfachen möchtest",
        height=TEXT_AREA_HEIGHT,
        max_chars=MAX_CHARS_INPUT,
        key="key_textinput",
    )
with placeholder_result:
    text_output = st.text_area(
        "Ergebnis",
        height=TEXT_AREA_HEIGHT,
        key="key_textoutput",
    )
with placeholder_analysis:
    text_analysis = st.metric(
        label="Verständlichkeit 0-20 Punkte",
        value=None,
        delta=None,
        help="Texte in Einfacher Sprache haben meist einen Wert von 16 bis 20 Punkten, Texte in Leichter Sprache 18 bis 20 Punkte.",
    )


# Derive modelId from explicit model_choice.
modelId = M_LARGE
if model_choice == "Claude 3 Haiku":
    modelId = HAIKU
elif model_choice == "Claude 3 Sonnet":
    modelId = SONNET
elif model_choice == "Claude 3 Opus":
    modelId = OPUS
elif model_choice == "GPT-4":
    modelId = GPT4
elif model_choice == "GPT-4o":
    modelId = GPT4o


# Start processing if one of the processing buttons is clicked.
if do_simplification or do_analysis or do_one_click:
    start_time = time.time()
    if text_input == "":
        st.error("Bitte gib einen Text ein.")
        st.stop()

    score_source = get_understandability(text_input)
    score_source_rounded = int(np.round(score_source, 0))
    cefr_source = get_cefr_level(score_source)

    # Analyze source text and display results.
    with source_text:
        if score_source < LIMIT_HARD:
            st.markdown(
                f"Dein Ausgangstext ist **:red[schwer verständlich]**. ({score_source_rounded} von 20 Punkten). Das entspricht etwa dem **:red[Sprachniveau {cefr_source}]**."
            )
        elif score_source >= LIMIT_HARD and score_source < LIMIT_MEDIUM:
            st.markdown(
                f"Dein Ausgangstext ist **:orange[nur mässig verständlich]**. ({score_source_rounded} von 20 Punkten). Das entspricht etwa dem **:orange[Sprachniveau {cefr_source}]**."
            )
        else:
            st.markdown(
                f"Dein Ausgangstext ist **:green[gut verständlich]**. ({score_source_rounded} von 20 Punkten). Das entspricht etwa dem **:green[Sprachniveau {cefr_source}]**."
            )
        with placeholder_analysis.container():
            text_analysis = st.metric(
                label="Verständlichkeit 0-20 Punkte",
                value=score_source_rounded,
                delta=None,
                help="Verständlichkeit auf einer Skala von 0 bis 20 Punkten (von 0 = extrem schwer verständlich bis 20 = sehr gut verständlich). Texte in Einfacher Sprache haben meist einen Wert von 16 bis 20 Punkten, Texte in Leichter Sprache 18 bis 20 Punkte.",
            )

        with placeholder_analysis.container():
            with st.spinner("Ich arbeite..."):
                # One-click simplification.
                if do_one_click:
                    success, response = get_one_click_results()
                # Regular text simplification or analysis.
                else:
                    if model_choice in ["GPT-4", "GPT-4o"]:
                        success, response = invoke_openai_model(
                            text_input,
                            modelId=modelId,
                            analysis=do_analysis,
                        )
                    elif model_choice in ["Mistral Large"]:
                        success, response = invoke_mistral_model(
                            text_input, modelId=modelId, analysis=do_analysis
                        )
                    else:
                        success, response = invoke_anthropic_model(
                            text_input, modelId=modelId, analysis=do_analysis
                        )
    if success is False:
        st.error(
            "Es ist ein Fehler bei der Abfrage der APIs aufgetreten. Bitte versuche es erneut. Alternativ überprüfe Code, API-Keys, Verfügbarkeit der Modelle und ggf. Internetverbindung."
        )
        time_processed = time.time() - start_time
        log_event(
            text_input,
            "Error from model call",
            do_analysis,
            do_simplification,
            do_one_click,
            leichte_sprache,
            model_choice,
            time_processed,
            success,
        )

        st.stop()

    # Display results in UI.
    text = "Dein vereinfachter Text"
    if do_analysis:
        text = "Deine Analyse"
    # Often the models return the German letter «ß». Replace it with the Swiss «ss».
    response = response.replace("ß", "ss")
    time_processed = time.time() - start_time

    with placeholder_result.container():
        st.text_area(
            text,
            height=TEXT_AREA_HEIGHT,
            value=response,
        )
        if do_simplification or do_one_click:
            score_target = get_understandability(response)
            score_target_rounded = int(np.round(score_target, 0))
            cefr_target = get_cefr_level(score_target)
            if score_target < LIMIT_HARD:
                st.markdown(
                    f"Dein vereinfachter Text ist **:red[schwer verständlich]**. ({score_target_rounded} von 20 Punkten). Das entspricht etwa dem **:red[Sprachniveau {cefr_target}]**."
                )
            elif score_target >= LIMIT_HARD and score_target < LIMIT_MEDIUM:
                st.markdown(
                    f"Dein vereinfachter Text ist **:orange[nur mässig verständlich]**. ({score_target_rounded} von 20 Punkten). Das entspricht etwa dem **:orange[Sprachniveau {cefr_target}]**."
                )
            else:
                st.markdown(
                    f"Dein vereinfachter Text ist **:green[gut verständlich]**. ({score_target_rounded} von 20 Punkten). Das entspricht etwa dem **:green[Sprachniveau {cefr_target}]**."
                )
            with placeholder_analysis.container():
                text_analysis = st.metric(
                    label="Verständlichkeit 0-20 Punkte",
                    value=score_target_rounded,
                    delta=int(np.round(score_target - score_source, 0)),
                    help="Verständlichkeit auf einer Skala von 0 bis 20 Punkten (von 0 = extrem schwer verständlich bis 20 = sehr gut verständlich). Texte in Einfacher Sprache haben meist einen Wert von 16 bis 20 Punkten.",
                )

                create_download_link(text_input, response)
                st.caption(f"Verarbeitet in {time_processed:.1f} Sekunden.")
        else:
            with placeholder_analysis.container():
                text_analysis = st.metric(
                    label="Verständlichkeit 0-20 Punkte",
                    value=score_source_rounded,
                    help="Verständlichkeit auf einer Skala von 0 bis 20 Punkten (von 0 = extrem schwer verständlich bis 20 = sehr gut verständlich). Texte in Einfacher Sprache haben meist einen Wert von 16 bis 20 Punkten.",
                )
                create_download_link(text_input, response, analysis=True)
                st.caption(f"Verarbeitet in {time_processed:.1f} Sekunden.")

        log_event(
            text_input,
            response,
            do_analysis,
            do_simplification,
            do_one_click,
            leichte_sprache,
            model_choice,
            time_processed,
            success,
        )
        st.stop()
