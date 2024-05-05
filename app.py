# Imports
import os
import threading
import traceback

import httpx
import streamlit as st
from deepgram import (
    DeepgramClient,
    FileSource,
    PrerecordedOptions,
)
from st_audiorec import st_audiorec
from st_social_media_links import SocialMediaIcons

# Configs
__version__ = "1.0.3"

st.set_page_config(
    page_title="Deepgram API Playground",
    page_icon="▶️",
    menu_items={
        "About": f"▶️ Deepgram API Playground v{__version__}  "
)

st.header("🎵➡️ 🔠 Deepgram STT API Playground", divider="violet")
st.caption(
    "A feature-rich API playground for Deepgram's SoTA Speech-to-Text and Speech-Recognition models 🚀"
)

MODELS = {
    "Nova-2": "nova-2-ea",
    "Nova": "nova",
    "Whisper Cloud": "whisper-medium",
    "Enhanced": "enhanced",
    "Base": "base",
}

LANGUAGES = {
    "Automatic Language Detection": None,
    "English": "en",
    "French": "fr",
    "Hindi": "hi",
}

@st.cache_data
def prerecorded(source, options: PrerecordedOptions) -> None:
    payload: FileSource = {"buffer": source["buffer"]}
    response = (
        deepgram.listen.prerecorded.v("1")
        .transcribe_file(
            payload,
            options,
        )
        .to_dict()
    )

    # Write the response to the console
    if detected_language := response["results"]["channels"][0].get("detected_language", None):
        st.write(
            f"🔠 __Detected language:__ {detected_language} ({list(LANGUAGES.keys())[list(LANGUAGES.values()).index(detected_language)]})"
        )

    # FIXME: Parse multichannel response
    if summarize:
        tab1, tab2, tab3 = st.tabs(["📝Response", "🗒️Transcript", "🤏Summary"])
        try:
            tab3.write(
                response["results"]["channels"][0]["alternatives"][0]["summaries"][0]["summary"]
            )
        except Exception as e:
            st.error(e)
    else:
        tab1, tab2 = st.tabs(["📝Response", "🗒️Transcript"])
    try:
        tab1.write(response)
    except Exception as e:
        st.error(e)
    try:
        if paragraphs or smart_format:
            tab2.write(
                response["results"]["channels"][0]["alternatives"][0]["paragraphs"]["transcript"]
            )
        else:
            tab2.write(response["results"]["channels"][0]["alternatives"][0]["transcript"])
    except Exception as e:
        st.error(e)


lcol, mcol, rcol = st.columns(3)

language = mcol.selectbox(
    "🔠 Language",
    options=list(LANGUAGES.keys()),
    help="⚠️Some features are [only accessible in certain languages](https://developers.deepgram.com/documentation/features/)",
)

lang_options = {
    "detect_language"
    if language == "Automatic Language Detection"
    else "language": (True if language == "Automatic Language Detection" else LANGUAGES[language])
}

model = rcol.selectbox(
    "🤖 Model",
    options=list(MODELS.keys()),
    help="[Models overview](https://developers.deepgram.com/docs/models-overview)",
)

with st.sidebar:
    with st.expander("🛠️Setup", expanded=True):
        st.info("🚀Sign up for a [Free API key](https://console.deepgram.com/signup)")

        deepgram_api_key = st.text_input(
            "🔐 Deepgram API Key",
            type="password",
            placeholder="Enter your Deepgram API key",
            help="""
            The [Deepgram API key](https://developers.deepgram.com/docs/authenticating) can also be passed through 
            [Streamlit secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management) or
            the `DEEPGRAM_API_KEY` environment variable""",
        )

        if deepgram_api_key == "":
            if "DEEPGRAM_API_KEY" in st.secrets:
                deepgram_api_key = st.secrets["DEEPGRAM_API_KEY"]
            elif "DEEPGRAM_API_KEY" in os.environ:
                deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
            else:
                st.error("Please enter your Deepgram API key to continue")
                st.stop()

        deepgram = DeepgramClient(deepgram_api_key)

    with st.expander("🦾 Features", expanded=True):
        detect_topics = st.checkbox(
            "Topic Detection",
            help="Indicates whether Deepgram will identify and extract key topics for sections of content",
            value=True,
        )

        diarize = st.checkbox(
            "Diarization",
            help="Indicates whether to recognize speaker changes",
            value=True,
        )

        detect_entities = st.checkbox(
            "Entity Detection",
            help="Indicates whether Deepgram will identify and extract key entities for sections of content",
            value=True,
        )

        multichannel = st.checkbox(
            "Multichannel",
            help="Recognizes multiple audio channels and transcribes each channel independently",
        )

        paragraphs = st.checkbox(
            "Paragraphs",
            help="""Indicates whether Deepgram will split audio into paragraphs to improve transcript readability. 
            When paragraphs is set to true, punctuate will also be set to true""",
            value=True,
        )

        profanity_filter = st.checkbox(
            "Profanity filter",
            help="Indicates whether to remove profanity from the transcript",
        )

        punctuate = st.checkbox(
            "Punctuation",
            help="Indicates whether to add punctuation and capitalization to the transcript",
        )

        if redact := st.checkbox(
            "Redaction",
            help="Indicates whether to redact sensitive information, replacing redacted content with asterisks (*)",
        ):
            lcol, rcol = st.columns([1, 14])
            numbers = rcol.checkbox("Numbers", help="Aggressively redacts strings of numerals")
            pci = rcol.checkbox(
                "PCI",
                help="Redacts sensitive credit card information, including credit card number, expiration date, and CVV",
            )
            ssn = rcol.checkbox("SSN", help="Redacts social security numbers")
        else:
            pci = ssn = numbers = None
        redact_options = [
            "pci" if pci else None,
            "ssn" if ssn else None,
            "numbers" if numbers else None,
        ]

        if search := st.checkbox(
            "Search",
            help="""
            Terms or phrases to search for in the submitted audio. 
            Deepgram searches for acoustic patterns in audio rather than text patterns in transcripts 
            because we have noticed that acoustic pattern matching is more performant.
            """,
        ):
            search_terms = st.text_input(
                "Search terms",
                placeholder="TERM_1, TERM_2",
                help="Enter terms as comma-separated values",
            )
        else:
            search_terms = ""

        smart_format = st.checkbox(
            "Smart Format",
            help="""Smart Format improves readability by applying additional formatting. 
            When enabled, the following features will be automatically applied: 
            Punctuation, Numerals, Paragraphs, Dates, Times, and Alphanumerics""",
            value=True,
        )

        summarize = st.checkbox(
            "Summarization",
            help="""Indicates whether Deepgram will provide summaries for sections of content. 
            When Summarization is enabled, Punctuation will also be enabled by default""",
            value=True,
        )

        if utterances := st.checkbox(
            "Utterences",
            help="""Segments speech into meaningful semantic units. 
                By default, when utterances is enabled, it starts a new utterance after 0.8s of silence. 
                You can customize the length of time used to determine where to split utterances with the utt_split parameter""",
            value=True,
        ):
            utt_split = st.number_input(
                "Utterance split",
                min_value=0.0,
                step=0.1,
                value=0.8,
                help="""Length of time in seconds of silence between words that Deepgram will use 
                when determining where to split utterances. Default is 0.8""",
            )
        else:
            utt_split = 0.8

    with open("sidebar.html", "r", encoding="UTF-8") as sidebar_file:
        sidebar_html = sidebar_file.read().replace("{VERSION}", __version__)

    st.components.v1.html(sidebar_html, height=228)

    st.html(
        """
        <div style="text-align:center; font-size:14px; color:lightgrey">
            <hr style="margin-bottom: 6%; margin-top: 0%;">
            Share the ❤️ on social media
        </div>"""
    )

    
# TODO: Extract audio from video for all modes
audio_source = st.radio(
    "Choose audio source",
    options=[
        "🎶 Pick a sample file",
        "️🗣 Record audio️",
        "⬆️ Upload audio file",
    ],
    horizontal=True,
)

if audio_source == "⬆️ Upload audio file":
    st.session_state["audio"] = st.file_uploader(
        label="⬆️ Upload audio file",
        label_visibility="collapsed",
    )
    st.session_state["mimetype"] = (
        st.session_state["audio"].type if st.session_state["audio"] else None
    )

elif audio_source == "️🗣 Record audio️":
    st.session_state["audio"] = st_audiorec()

else:
    st.session_state["audio"] = "assets/sample_file.wav"

if st.session_state["audio"] and audio_source != "️🗣 Record audio️":
    st.audio(st.session_state["audio"])

options = PrerecordedOptions(
    model=MODELS[model],
    detect_topics=detect_topics,
    diarize=diarize,
    detect_entities=detect_entities,
    multichannel=multichannel,
    paragraphs=paragraphs,
    profanity_filter=profanity_filter,
    punctuate=punctuate,
    redact=[option for option in redact_options if option],
    smart_format=smart_format,
    summarize=summarize,
    search=f"""[{search_terms or ""}]""",
    utterances=utterances,
    utt_split=utt_split,
)

# Check whether requested file is local, uploaded or remote, and prepare source
if audio_source in (["⬆️ Upload audio file", "️🗣 Record audio️"]):
    # file is uploaded/recorded
    source = {
        "buffer": st.session_state["audio"],
    }
else:
    # file is local
    source = {"buffer": open(st.session_state["audio"], "rb").read()}

if st.button(
    "🪄 Transcribe",
    use_container_width=True,
    type="primary",
    disabled=not deepgram_api_key,
    help="" if deepgram_api_key else "Enter your Deepgram API key",
):
    try:
        prerecorded(source, options)
    except Exception as e:
        if str(e).endswith("timed out"):
            st.error(
                f"""{e}  
                Please try after some time, or try with a smaller source if the issue persists.""",
                icon="⌚",
            )
        else:
            st.error(
                f"""The app has encountered an error:  
                `{e}`  
                Please create an issue [here](https://github.com/SiddhantSadangi/st_deepgram_playground/issues/new) 
                with the below traceback""",
                icon="🥺",
            )
            st.code(traceback.format_exc())

st.success(
    "[Star the repo](https://github.com/SiddhantSadangi/st_deepgram_playground) to show your :heart:",
    icon="⭐",
)
