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

import numpy as np

from openai import OpenAI
from anthropic import Anthropic
from mistralai import Mistral
import google.generativeai as genai

from utils_understandability import get_zix, get_cefr

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

API_KEYS = {
    "OPENAI": os.getenv("OPENAI_API_KEY"),
    "ANTHROPIC": os.getenv("ANTHROPIC_API_KEY"),
    "MISTRAL": os.getenv("MISTRAL_API_KEY"),
    "GOOGLE": os.getenv("GOOGLE_API_KEY"),
}
genai.configure(api_key=API_KEYS["GOOGLE"])


MODEL_IDS = {
    "Mistral Nemo": "open-mistral-nemo",
    "Mistral large": "mistral-large-latest",
    "Claude Haiku 3.5": "claude-3-5-haiku-latest",
    "Claude Sonnet 3.5": "claude-3-5-sonnet-latest",
    "GPT-4o mini": "gpt-4o-mini",
    "GPT-4o": "gpt-4o",
    "o1 mini": "o1-mini",
    "o1": "o1-preview",
    "Gemini 1.5 Flash": "gemini-1.5-flash",
    "Gemini 2.0 Flash": "gemini-2.0-flash-exp",
    "Gemini 1.5 Pro": "gemini-1.5-pro",
}

# From our testing we derive a sensible temperature of 0.5 as a good trade-off between creativity and coherence. Adjust this to your needs.
TEMPERATURE = 0.5
MAX_TOKENS = 8192

# Height of the text areas for input and output.
TEXT_AREA_HEIGHT = 600

# Maximum number of characters for the input text.
# This is way below the context window sizes of the models.
# Adjust to your needs. However, we found that users can work and validate better when we nudge to work with shorter texts.
MAX_CHARS_INPUT = 10_000


USER_WARNING = """<sub>⚠️ Achtung: Diese App ist ein Prototyp. Nutze die App :red[**nur für öffentliche, nicht sensible Daten**]. Die App liefert lediglich einen Textentwurf. Überprüfe das Ergebnis immer und passe es an, wenn nötig. Die aktuelle App-Version ist v0.5 Die letzte Aktualisierung war am 22.12.2024."""


# Constants for the formatting of the Word document that can be downloaded.
FONT_WORDDOC = "Arial"
FONT_SIZE_HEADING = 12
FONT_SIZE_PARAGRAPH = 9
FONT_SIZE_FOOTER = 7
DEFAULT_OUTPUT_FILENAME = "Ergebnis.docx"
ANALYSIS_FILENAME = "Analyse.docx"

# Limits for the understandability score to determine if the text is easy, medium or hard to understand.
LIMIT_HARD = 0
LIMIT_MEDIUM = -2

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------
# Functions


@st.cache_resource
def get_project_info():
    """Get markdown for project information that is shown in the expander section at the top of the app."""
    with open("utils_expander.md") as f:
        return f.read()


@st.cache_resource
def create_project_info(project_info):
    """Create expander for project info. Add the image in the middle of the content."""
    with st.expander("Detaillierte Informationen zum Projekt"):
        project_info = project_info.split("### Image ###")
        st.markdown(project_info[0], unsafe_allow_html=True)
        st.image("zix_scores.jpg", use_container_width=True)
        st.markdown(project_info[1], unsafe_allow_html=True)


def create_prompt(text, prompt_es, prompt_ls, analysis_es, analysis_ls, analysis):
    """Create prompt and system message according the app settings."""
    if analysis:
        final_prompt = (
            analysis_ls.format(rules=RULES_LS, prompt=text)
            if leichte_sprache
            else analysis_es.format(rules=RULES_ES, prompt=text)
        )
        system = SYSTEM_MESSAGE_LS if leichte_sprache else SYSTEM_MESSAGE_ES
    else:
        if leichte_sprache:
            completeness = REWRITE_CONDENSED if condense_text else REWRITE_COMPLETE
            final_prompt = prompt_ls.format(
                rules=RULES_LS, completeness=completeness, prompt=text
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
    tag = "leichtesprache" if leichte_sprache else "einfachesprache"
    result = re.findall(rf"<{tag}>(.*?)</{tag}>", response, re.DOTALL)
    return "\n".join(result).strip()


def strip_markdown(text):
    """Strip markdown from text."""
    # Remove markdown headers.
    text = re.sub(r"#+\s", "", text)
    # Remove markdown italic and bold.
    text = re.sub(r"\*\*|\*|__|_", "", text)
    return text


@st.cache_resource
def get_anthropic_client():
    return Anthropic(api_key=API_KEYS["ANTHROPIC"])


@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=API_KEYS["OPENAI"])


@st.cache_resource
def get_mistral_client():
    return Mistral(api_key=API_KEYS["MISTRAL"])


def invoke_anthropic_model(
    text,
    model_id=MODEL_IDS["Claude Haiku 3.5"],
    analysis=False,
):
    """Invoke Anthropic model."""
    final_prompt, system = create_prompt(text, *CLAUDE_TEMPLATES, analysis)
    try:
        message = anthropic_client.messages.create(
            model=model_id,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": final_prompt,
                }
            ],
        )
        message = message.content[0].text.strip()
        message = get_result_from_response(message)
        message = strip_markdown(message)
        return True, message
    except Exception as e:
        print(f"Error: {e}")
        return False, e


def invoke_openai_model(
    text,
    model_id=MODEL_IDS["GPT-4o mini"],
    analysis=False,
):
    """Invoke OpenAI model."""
    final_prompt, system = create_prompt(text, *OPENAI_TEMPLATES, analysis)
    try:
        message = openai_client.chat.completions.create(
            model=model_id,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": final_prompt},
            ],
        )
        message = message.choices[0].message.content.strip()
        message = get_result_from_response(message)
        message = strip_markdown(message)
        return True, message
    except Exception as e:
        print(f"Error: {e}")
        return False, e


def invoke_openai_reasoning_model(
    text,
    model_id=MODEL_IDS["o1 mini"],
    analysis=False,
):
    """Invoke OpenAI model."""
    final_prompt, _ = create_prompt(text, *OPENAI_TEMPLATES, analysis)
    try:
        message = openai_client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": final_prompt},
            ],
        )
        message = message.choices[0].message.content.strip()
        message = get_result_from_response(message)
        message = strip_markdown(message)
        return True, message
    except Exception as e:
        print(f"Error: {e}")
        return False, e


def invoke_mistral_model(
    text, model_id=MODEL_IDS["Mistral large"], temperature=TEMPERATURE, analysis=False
):
    """Invoke Mistral model."""
    # Our Claude templates seem to work fine for Mistral as well.
    final_prompt, system = create_prompt(text, *CLAUDE_TEMPLATES, analysis)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": final_prompt},
    ]
    try:
        message = mistral_client.chat.complete(
            model=model_id,
            messages=messages,
            temperature=TEMPERATURE,
        )
        message = message.choices[0].message.content.strip()
        message = get_result_from_response(message)
        message = strip_markdown(message)
        return True, message
    except Exception as e:
        print(f"Error: {e}")
        return False, e


def invoke_google_model(
    text,
    model_id=MODEL_IDS["Gemini 2.0 Flash"],
    analysis=False,
):
    """Invoke Google model."""
    final_prompt, system = create_prompt(text, *OPENAI_TEMPLATES, analysis)
    google_client = genai.GenerativeModel(
        model_id,
        generation_config={"temperature": TEMPERATURE},
        system_instruction=system,
    )
    try:
        message = google_client.generate_content(
            final_prompt,
        )
        message = message.text.strip()
        message = get_result_from_response(message)
        message = strip_markdown(message)
        return True, message
    except Exception as e:
        print(f"Error: {e}")
        return False, e


def enter_sample_text():
    """Enter sample text into the text input in the left column."""
    st.session_state.key_textinput = SAMPLE_TEXT_01


def get_one_click_results():
    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = {
            "Mistral large": executor.submit(
                invoke_mistral_model,
                st.session_state.key_textinput,
                MODEL_IDS["Mistral large"],
            ),
            "Mistral Nemo": executor.submit(
                invoke_mistral_model,
                st.session_state.key_textinput,
                MODEL_IDS["Mistral Nemo"],
            ),
            "GPT-4o mini": executor.submit(
                invoke_openai_model,
                st.session_state.key_textinput,
                MODEL_IDS["GPT-4o mini"],
            ),
            "GPT-4o": executor.submit(
                invoke_openai_model,
                st.session_state.key_textinput,
                MODEL_IDS["GPT-4o"],
            ),
            "o1 mini": executor.submit(
                invoke_openai_reasoning_model,
                st.session_state.key_textinput,
                MODEL_IDS["o1 mini"],
            ),
            "o1": executor.submit(
                invoke_openai_reasoning_model,
                st.session_state.key_textinput,
                MODEL_IDS["o1"],
            ),
            "Claude Haiku 3.5": executor.submit(
                invoke_anthropic_model,
                st.session_state.key_textinput,
                MODEL_IDS["Claude Haiku 3.5"],
            ),
            "Claude Sonnet 3.5": executor.submit(
                invoke_anthropic_model,
                st.session_state.key_textinput,
                MODEL_IDS["Claude Sonnet 3.5"],
            ),
            "Gemini 1.5 Flash": executor.submit(
                invoke_google_model,
                st.session_state.key_textinput,
                MODEL_IDS["Gemini 1.5 Flash"],
            ),
            "Gemini 2.0 Flash": executor.submit(
                invoke_google_model,
                st.session_state.key_textinput,
                MODEL_IDS["Gemini 2.0 Flash"],
            ),
            "Gemini 1.5 Pro": executor.submit(
                invoke_google_model,
                st.session_state.key_textinput,
                MODEL_IDS["Gemini 1.5 Pro"],
            ),
        }

    responses = {name: future.result() for name, future in futures.items()}
    response_texts = []

    # We add 0 to the rounded ZIX score to avoid -0.
    # https://stackoverflow.com/a/11010791/7117003
    for name, (success, response) in responses.items():
        if success:
            zix = get_zix(response)
            zix = int(np.round(zix, 0) + 0)
            cefr = get_cefr(zix)
            response_texts.append(
                f"\n----- Ergebnis von {name} (Verständlichkeit: {zix}, Niveau etwa {cefr}) -----\n\n{response}"
            )

    if not response_texts:
        return False, "Es ist ein Fehler aufgetreten."
    return True, "\n\n\n".join(response_texts)


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

    timestamp = datetime.now().strftime(DATETIME_FORMAT)
    models_used = model_choice
    if do_one_click:
        models_used = ", ".join([model for model in MODEL_IDS.keys()])
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
    file_name = DEFAULT_OUTPUT_FILENAME

    if do_one_click:
        caption = "Vereinfachte Texte herunterladen"
    else:
        caption = "Vereinfachten Text herunterladen"

    if analysis:
        file_name = ANALYSIS_FILENAME
        caption = "Analyse herunterladen"
    download_url = f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{file_name}">{caption}</a>'
    st.markdown(download_url, unsafe_allow_html=True)


def clean_log(text):
    """Remove linebreaks and tabs from log messages
    that otherwise would yield problems when parsing the logs."""
    return text.replace("\n", " ").replace("\t", " ")


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
    log_string = f"{datetime.now().strftime(DATETIME_FORMAT)}"
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

project_info = get_project_info()

# Persist text input across sessions in session state.
# Otherwise, the text input sometimes gets lost when the user clicks on a button.
if "key_textinput" not in st.session_state:
    st.session_state.key_textinput = ""

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
        options=([model_name for model_name in MODEL_IDS.keys()]),
        index=3,
        horizontal=True,
        help="Alle Modelle liefern je nach Ausgangstext meist gute bis sehr gute Ergebnisse und sind alle einen Versuch wert. Claude Haiku, GPT-4o mini und Gemini Flash sind am schnellsten. Mehr Details siehe Infobox oben auf der Seite.",
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
    st.text_area(
        "Ausgangstext, den du vereinfachen möchtest",
        value=None,
        height=TEXT_AREA_HEIGHT,
        max_chars=MAX_CHARS_INPUT,
        key="key_textinput",
    )
with placeholder_result:
    text_output = st.text_area(
        "Ergebnis",
        height=TEXT_AREA_HEIGHT,
    )
with placeholder_analysis:
    text_analysis = st.metric(
        label="Verständlichkeit -10 bis 10",
        value=None,
        delta=None,
        help="Verständlichkeit auf einer Skala von -10 bis 10 Punkten (von -10 = extrem schwer verständlich bis 10 = sehr gut verständlich). Texte in Einfacher Sprache haben meist einen Wert von 0 bis 4 oder höher, Texte in Leichter Sprache 2 bis 6 oder höher.",
    )


# Derive model_id from explicit model_choice.
model_id = MODEL_IDS[model_choice]

# Start processing if one of the processing buttons is clicked.
if do_simplification or do_analysis or do_one_click:
    start_time = time.time()
    if st.session_state.key_textinput == "":
        st.error("Bitte gib einen Text ein.")
        st.stop()

    score_source = get_zix(st.session_state.key_textinput)
    # We add 0 to avoid negative zero.
    score_source_rounded = int(np.round(score_source, 0) + 0)
    cefr_source = get_cefr(score_source)

    # Analyze source text and display results.
    with source_text:
        if score_source < LIMIT_HARD:
            st.markdown(
                f"Dein Ausgangstext ist **:red[schwer verständlich]**. ({score_source_rounded} auf einer Skala von -10 bis 10). Das entspricht etwa dem **:red[Sprachniveau {cefr_source}]**."
            )
        elif score_source >= LIMIT_HARD and score_source < LIMIT_MEDIUM:
            st.markdown(
                f"Dein Ausgangstext ist **:orange[nur mässig verständlich]**. ({score_source_rounded} auf einer Skala von -10 bis 10). Das entspricht etwa dem **:orange[Sprachniveau {cefr_source}]**."
            )
        else:
            st.markdown(
                f"Dein Ausgangstext ist **:green[gut verständlich]**. ({score_source_rounded} auf einer Skala von -10 bis 10). Das entspricht etwa dem **:green[Sprachniveau {cefr_source}]**."
            )
        with placeholder_analysis.container():
            text_analysis = st.metric(
                label="Verständlichkeit von -10 bis 10",
                value=score_source_rounded,
                delta=None,
                help="Verständlichkeit auf einer Skala von -10 bis 10 Punkten (von -10 = extrem schwer verständlich bis 10 = sehr gut verständlich). Texte in Einfacher Sprache haben meist einen Wert von 0 bis 4 oder höher, Texte in Leichter Sprache 2 bis 6 oder höher.",
            )

        with placeholder_analysis.container():
            with st.spinner("Ich arbeite..."):
                # One-click simplification.
                if do_one_click:
                    success, response = get_one_click_results()
                # Regular text simplification or analysis
                else:
                    if model_choice in ["GPT-4o mini", "GPT-4o"]:
                        success, response = invoke_openai_model(
                            st.session_state.key_textinput,
                            model_id=model_id,
                            analysis=do_analysis,
                        )
                    elif model_choice in ["o1 mini", "o1"]:
                        success, response = invoke_openai_reasoning_model(
                            st.session_state.key_textinput,
                            model_id=model_id,
                            analysis=do_analysis,
                        )
                    elif model_choice in ["Mistral large", "Mistral Nemo"]:
                        success, response = invoke_mistral_model(
                            st.session_state.key_textinput,
                            model_id=model_id,
                            analysis=do_analysis,
                        )
                    elif model_choice in [
                        "Gemini 1.5 Flash",
                        "Gemini 2.0 Flash",
                        "Gemini 1.5 Pro",
                    ]:
                        success, response = invoke_google_model(
                            st.session_state.key_textinput,
                            model_id=model_id,
                            analysis=do_analysis,
                        )
                    else:
                        success, response = invoke_anthropic_model(
                            st.session_state.key_textinput,
                            model_id=model_id,
                            analysis=do_analysis,
                        )
    if success is False:
        st.error(
            "Es ist ein Fehler bei der Abfrage der APIs aufgetreten. Bitte versuche es erneut. Alternativ überprüfe Code, API-Keys, Verfügbarkeit der Modelle und ggf. Internetverbindung."
        )
        time_processed = time.time() - start_time
        log_event(
            st.session_state.key_textinput,
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
            score_target = get_zix(response)
            score_target_rounded = int(np.round(score_target, 0) + 0)
            cefr_target = get_cefr(score_target)
            if score_target < LIMIT_HARD:
                st.markdown(
                    f"Dein vereinfachter Text ist **:red[schwer verständlich]**. ({score_target_rounded}  auf einer Skala von -10 bis 10). Das entspricht etwa dem **:red[Sprachniveau {cefr_target}]**."
                )
            elif score_target >= LIMIT_HARD and score_target < LIMIT_MEDIUM:
                st.markdown(
                    f"Dein vereinfachter Text ist **:orange[nur mässig verständlich]**. ({score_target_rounded}  auf einer Skala von -10 bis 10). Das entspricht etwa dem **:orange[Sprachniveau {cefr_target}]**."
                )
            else:
                st.markdown(
                    f"Dein vereinfachter Text ist **:green[gut verständlich]**. ({score_target_rounded}  auf einer Skala von -10 bis 10). Das entspricht etwa dem **:green[Sprachniveau {cefr_target}]**."
                )
            with placeholder_analysis.container():
                text_analysis = st.metric(
                    label="Verständlichkeit -10 bis 10",
                    value=score_target_rounded,
                    delta=int(np.round(score_target - score_source, 0)),
                    help="Verständlichkeit auf einer Skala von -10 bis 10 (von -10 = extrem schwer verständlich bis 10 = sehr gut verständlich). Texte in Einfacher Sprache haben meist einen Wert von 0 bis 4 oder höher.",
                )

                create_download_link(st.session_state.key_textinput, response)
                st.caption(f"Verarbeitet in {time_processed:.1f} Sekunden.")
        else:
            with placeholder_analysis.container():
                text_analysis = st.metric(
                    label="Verständlichkeit -10 bis 10",
                    value=score_source_rounded,
                    help="Verständlichkeit auf einer Skala von -10 bis 10 (von -10 = extrem schwer verständlich bis 10 = sehr gut verständlich). Texte in Einfacher Sprache haben meist einen Wert von 0 bis 4 oder höher.",
                )
                create_download_link(
                    st.session_state.key_textinput, response, analysis=True
                )
                st.caption(f"Verarbeitet in {time_processed:.1f} Sekunden.")

        log_event(
            st.session_state.key_textinput,
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
