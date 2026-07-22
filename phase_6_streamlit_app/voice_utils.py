import io
import re
import logging
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def transcribe_audio(audio_bytes: bytes, api_key: str) -> str:
    """
    Transcribes audio bytes using Groq's Whisper endpoint.
    Biases transcription toward specific mutual fund terms.
    
    Args:
        audio_bytes: WAV audio file bytes.
        api_key: The Groq API key.
        
    Returns:
        Transcribed text as a string (empty if failed or silent).
    """
    if not audio_bytes:
        logging.warning("Received empty audio bytes for transcription.")
        return ""
        
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        logging.error(f"Failed to initialize Groq client for voice transcription: {e}")
        return ""

    # Domain vocabulary to bias the transcription
    prompt_vocab = (
        "HDFC Midcap Opportunities Fund, HDFC Flexi Cap Fund, HDFC Small Cap Fund, "
        "HDFC Multi Cap Fund, HDFC Top 100 Fund, SIP, NAV, expense ratio, exit load, "
        "KIM, SID, riskometer, lock-in period, benchmark, fund manager."
    )
    
    # We wrap the bytes in BytesIO and name it so the API library knows the file format.
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.wav"
    
    # Try whisper-large-v3-turbo first
    try:
        logging.info("Attempting transcription using whisper-large-v3-turbo...")
        response = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            prompt=prompt_vocab,
            language="en"
        )
        return response.text.strip()
    except Exception as turbo_err:
        logging.warning(f"whisper-large-v3-turbo failed: {turbo_err}. Retrying with fallback model whisper-large-v3...")
        
        # Fallback to whisper-large-v3
        try:
            # We must seek/reset the audio file pointer for the fallback request
            audio_file.seek(0)
            response = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                prompt=prompt_vocab,
                language="en"
            )
            return response.text.strip()
        except Exception as fallback_err:
            logging.error(f"Fallback transcription also failed: {fallback_err}")
            raise Exception(f"Transcription failed: {str(fallback_err)}")

def clean_text_for_speech(text: str) -> str:
    """
    Cleans text by removing markdown syntax, links, and non-ASCII/emoji characters
    to optimize readability for speech engines.
    """
    if not text:
        return ""
        
    # Remove markdown link markup like [link text](url) -> keep only link text
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove markdown stars/underscores/backticks
    cleaned = cleaned.replace("**", "").replace("*", "").replace("`", "").replace("___", "").replace("___", "")
    
    # Remove emojis (common Unicode ranges for emojis and pictographs)
    try:
        emoji_pattern = re.compile(
            "["
            "\U00010000-\U0010ffff"  # Supplementary Plane
            "]+", flags=re.UNICODE
        )
        cleaned = emoji_pattern.sub(r"", cleaned)
    except Exception as e:
        logging.debug(f"Error compiling/running emoji regex: {e}")
        
    return cleaned.strip()

def text_to_speech(text: str) -> io.BytesIO:
    """
    Converts text to speech bytes using gTTS.
    
    Args:
        text: The text to be converted to speech.
        
    Returns:
        A BytesIO object containing the audio in MP3 format.
    """
    try:
        from gtts import gTTS
    except ImportError:
        logging.error("gtts library is not installed.")
        raise ImportError("The 'gtts' package is required for voice output. Please run pip install gtts.")
        
    cleaned_text = clean_text_for_speech(text)
    if not cleaned_text:
        cleaned_text = "No text to read."
        
    fp = io.BytesIO()
    tts = gTTS(text=cleaned_text, lang='en', slow=False)
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp
