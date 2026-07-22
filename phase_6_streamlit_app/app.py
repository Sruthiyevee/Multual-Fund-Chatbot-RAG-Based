import streamlit as st
import os
import sys
import random
import base64
import streamlit.components.v1 as components

# Add project root to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import backend modules
try:
    from phase3_retrieval.retrieval_pipeline import RetrievalSystem
    from phase3_retrieval.query_classifier import QueryClassifier
    from phase4_generation.generation_pipeline import AnswerGenerator
    from phase4_generation.refusal_handler import RefusalHandler
    from utils.suggestions import SuggestionsHandler
    from voice_utils import transcribe_audio, text_to_speech
except ImportError as e:
    st.error(f"Failed to import backend modules: {e}")
    st.stop()

# Page Config
st.set_page_config(
    page_title="MF Facts AI",
    page_icon="ℹ️",
    layout="centered"
)

# Resolve avatar paths
user_avatar_path = os.path.join(current_dir, "user_avatar.png")
bot_avatar_path = os.path.join(current_dir, "bot_avatar.png")

# Helper to encode local images to base64
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return ""

user_avatar_b64 = get_base64_image(user_avatar_path)

# --- CSS Styling (Premium Dark Theme matching user mockup) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Apply global font override */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: #060b16 !important;
    }
    
    /* Dark background */
    .stApp {
        background-color: #060b16 !important;
    }
    
    /* Add padding to the bottom of the scroll container so the last message is fully visible above the fixed input bar */
    .stAppViewBlockContainer {
        padding-bottom: 130px !important;
    }
    
    /* Style stBottom to match the mockup theme and remove the white banner */
    div[data-testid="stBottom"] {
        background-color: #060b16 !important;
        background: #060b16 !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Clear all light theme backgrounds inside the bottom layout block */
    div[data-testid="stBottom"] *:not(button):not(.custom-mic-btn) {
        background-color: transparent !important;
    }
    
    /* Custom Navigation Bar */
    .custom-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0 20px 0;
        border-bottom: 1px solid #14223c;
        margin-bottom: 25px;
    }
    
    .nav-logo {
        color: #ffffff;
        font-size: 19px;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    
    .nav-right {
        display: flex;
        align-items: center;
        gap: 28px;
    }
    
    .nav-links {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    
    .nav-link {
        color: #94a3b8;
        font-size: 15px;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
        transition: color 0.2s;
    }
    
    .nav-link:hover {
        color: #ffffff;
    }
    
    .nav-link.active {
        color: #ffffff;
        border-bottom: 2px solid #00d2ff;
        padding-bottom: 4px;
    }
    
    .nav-icons {
        display: flex;
        align-items: center;
        gap: 18px;
    }
    
    .nav-icon {
        color: #94a3b8;
        font-size: 17px;
        cursor: pointer;
        transition: color 0.2s;
    }
    
    .nav-icon:hover {
        color: #ffffff;
    }
    
    .nav-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        object-fit: cover;
        border: 1.5px solid #14223c;
    }
    
    /* Chat message overrides */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 12px 0 !important;
    }
    
    /* User Message Bubble (Right-aligned, Cyan background, Dark text) */
    div[data-testid="stChatMessage"][data-testid="user"] {
        flex-direction: row-reverse !important;
    }
    
    div[data-testid="stChatMessage"][data-testid="user"] div[data-testid="stChatMessageContent"] {
        background: #00d2ff !important;
        color: #060b11 !important;
        border-radius: 20px 20px 4px 20px !important;
        padding: 14px 18px !important;
        margin-right: 12px !important;
        margin-left: auto !important;
        max-width: 75% !important;
        box-shadow: 0 4px 12px rgba(0, 210, 255, 0.15) !important;
    }
    
    /* Make sure user text displays as dark blue */
    div[data-testid="stChatMessage"][data-testid="user"] div[data-testid="stChatMessageContent"] p {
        color: #060b11 !important;
        font-weight: 500 !important;
    }
    
    /* Assistant Message Bubble (Left-aligned, Dark blue-gray card, Soft border) */
    div[data-testid="stChatMessage"][data-testid="assistant"] div[data-testid="stChatMessageContent"] {
        background-color: #111d33 !important;
        border: 1px solid #1c2e4e !important;
        border-radius: 20px 20px 20px 4px !important;
        padding: 18px 22px !important;
        color: #cbd5e1 !important;
        margin-left: 12px !important;
        max-width: 82% !important;
    }
    
    /* Styled Blockquote (Cyan card inset with left border) */
    blockquote {
        background-color: #0c1524 !important;
        border-left: 3px solid #00d2ff !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 14px 18px !important;
        margin: 16px 0 !important;
        color: #cbd5e1 !important;
    }
    
    blockquote strong {
        color: #00d2ff !important;
        font-size: 13.5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: block;
        margin-bottom: 6px;
    }
    
    /* Action pills row layout */
    .actions-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 14px;
        margin-left: 55px; /* Alignment with message bubble start */
        margin-bottom: 10px;
    }
    
    /* Pill shaped action buttons */
    .action-pill {
        background-color: #0c1524 !important;
        border: 1px solid #1c2e4e !important;
        color: #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 6px 14px !important;
        font-size: 13px !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        transition: all 0.2s !important;
        cursor: pointer !important;
    }
    
    .action-pill:hover {
        background-color: #14223c !important;
        border-color: #00d2ff !important;
        color: #00d2ff !important;
    }
    
    /* Suggestion button styling */
    div.stButton > button {
        background-color: #0c1524 !important;
        border: 1px solid #1c2e4e !important;
        color: #e2e8f0 !important;
        border-radius: 20px !important;
        padding: 6px 14px !important;
        font-size: 13px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s !important;
        width: auto !important;
        min-height: 32px !important;
    }
    
    div.stButton > button:hover {
        background-color: #14223c !important;
        border-color: #00d2ff !important;
        color: #00d2ff !important;
    }
    

    
    /* Remove avatars wrapper icons of Streamlit */
    div[data-testid="chatAvatarIcon-user"], div[data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }
    
    /* Make avatars circular */
    div[data-testid="stChatMessage"] img {
        border-radius: 50% !important;
        object-fit: cover !important;
    }
    
    /* Chat input container bottom styling (outer wrapper transparent) */
    div[data-testid="stChatInput"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Style the inner chat input bar to match the mockup */
    div[data-testid="stChatInput"] > div {
        background-color: #0b1322 !important; /* dark navy inner input bar */
        border: 1px solid #1e2e4e !important;
        border-radius: 28px !important;
        padding: 5px 12px 5px 44px !important; /* left padding for paperclip */
        position: relative !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Paperclip icon inside the inner chat input bar */
    div[data-testid="stChatInput"] > div::before {
        content: "📎" !important;
        position: absolute !important;
        left: 18px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        font-size: 18px !important;
        color: #94a3b8 !important;
        pointer-events: none !important;
        opacity: 0.7 !important;
    }
    
    /* Textarea padding-right to accommodate mic & send buttons */
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #ffffff !important;
        font-size: 14.5px !important;
        border: none !important;
        padding-right: 95px !important; /* space for mic (40px) + send (40px) */
    }
    
    /* Send button customization inside the input bar */
    div[data-testid="stBottom"] button[data-testid="stChatInputSubmitButton"] {
        background-color: #00d2ff !important;
        color: #060b11 !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: background-color 0.2s !important;
        position: absolute !important;
        right: 8px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 99999 !important;
    }
    
    div[data-testid="stBottom"] button[data-testid="stChatInputSubmitButton"]:hover {
        background-color: #00b4d8 !important;
    }
    
    div[data-testid="stBottom"] button[data-testid="stChatInputSubmitButton"] svg {
        color: #060b11 !important;
        fill: #060b11 !important;
    }
    
    /* Style for the custom mic button injected via JS */
    div[data-testid="stBottom"] .custom-mic-btn {
        position: absolute !important;
        right: 48px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 50% !important;
        background-color: #ffffff !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        z-index: 999999 !important;
        font-size: 16px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15) !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    div[data-testid="stBottom"] .custom-mic-btn:hover {
        background-color: #f1f5f9 !important;
    }
    
    /* Style the disclaimer to be fixed below the input bar */
    .bottom-disclaimer {
        position: fixed !important;
        bottom: 8px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 100% !important;
        max-width: 730px !important;
        z-index: 99999 !important;
        text-align: center !important;
        color: #475569 !important;
        font-size: 11px !important;
        background-color: transparent !important;
        pointer-events: none !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Suggested questions list */
    .suggested-questions {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 15px;
    }
    
    /* Hide Streamlit components headers & footers */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #060b16;
    }
    ::-webkit-scrollbar-thumb {
        background: #14223c;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Helper to automatically format fact blocks as markdown blockquotes
def format_response_markdown(text: str) -> str:
    lines = text.split("\n")
    formatted_lines = []
    in_blockquote = False
    
    fact_headers = ["Exit Load Fact:", "Fact:", "Expense Ratio:", "Minimum SIP:", "Riskometer Rating:", "Lock-in Period:", "Benchmark:"]
    
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(header) for header in fact_headers):
            if in_blockquote:
                formatted_lines.append(f"**{stripped}**")
            else:
                formatted_lines.append(f"\n> **{stripped}**")
                in_blockquote = True
        elif in_blockquote and stripped == "":
            in_blockquote = False
            formatted_lines.append("")
        elif in_blockquote:
            formatted_lines.append(f"> {line}")
        else:
            formatted_lines.append(line)
            
    return "\n".join(formatted_lines)

# --- Initialization ---

@st.cache_resource(show_spinner=False)
def load_rag_system():
    base_dir = project_root
    embeddings_dir = os.path.join(base_dir, "phase2_vector_db")
    
    if not os.path.exists(embeddings_dir):
        st.error(f"Embeddings directory not found at {embeddings_dir}. Please run Phase 2 first.")
        st.stop()
        
    try:
        retriever = RetrievalSystem(embeddings_dir)
        classifier = QueryClassifier()
        refusal_handler = RefusalHandler()
        suggestions_handler = SuggestionsHandler()
        
        api_key = None
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
        if not api_key:
             api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key or api_key == "YOUR_GROQ_API_KEY_HERE":
            st.error("❌ **GROQ_API_KEY not configured!**")
            st.stop()

        generator = AnswerGenerator(api_key=api_key)
        return retriever, classifier, refusal_handler, suggestions_handler, generator
    except Exception as e:
        st.error(f"❌ Failed to initialize RAG system: {type(e).__name__}")
        st.stop()

retriever, classifier, refusal_handler, suggestions_handler, generator = load_rag_system()

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    initial_text = "Hello! I'm your MF Facts assistant. I can help you analyze mutual funds, check exit loads, or understand market trends. How can I help you today?"
    try:
        init_audio = text_to_speech(initial_text)
        init_bytes = init_audio.getvalue() if hasattr(init_audio, 'getvalue') else init_audio.read()
    except Exception:
        init_bytes = None

    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": initial_text,
            "show_starters": True,
            "source": None,
            "suggestions": [],
            "audio_bytes": init_bytes
        }
    ]

# Starter questions (fixed set)
STARTER_QUESTIONS = [
    "What is the expense ratio of HDFC Midcap Fund?",
    "Is there any exit load for HDFC Large Cap Fund?",
    "What is the minimum SIP investment required for HDFC Flexi Cap Fund?",
    "What is the risk level and benchmark of HDFC Small Cap Fund?",
    "How can I download my capital gains statement?",
]

if "show_suggestions" not in st.session_state:
    st.session_state.show_suggestions = True

# --- UI Layout ---

# Custom Navigation Header matching user mockup
navbar_html = f"""
<div class="custom-navbar">
    <div class="nav-logo">MF Facts</div>
</div>
"""
st.markdown(navbar_html, unsafe_allow_html=True)

# Display Chat History
for idx, msg in enumerate(st.session_state.messages):
    avatar = user_avatar_path if msg["role"] == "user" else bot_avatar_path
    
    with st.chat_message(msg["role"], avatar=avatar):
        # Apply fact formatting to assistant messages
        if msg["role"] == "assistant":
            formatted_text = format_response_markdown(msg["content"])
            st.markdown(formatted_text)
            
            # Preloaded audio player loaded in parallel with response text
            if "audio_bytes" in msg and msg["audio_bytes"]:
                st.audio(msg["audio_bytes"], format="audio/mp3")
        else:
            st.markdown(msg["content"])
                    
    # Display action row for assistant sources & suggestion pills (placed directly under chat bubble)
    if msg["role"] == "assistant":
        has_source = "source" in msg and msg["source"]
        has_sugg = "suggestions" in msg and msg["suggestions"]
        
        if has_source or has_sugg:
            # We can use Streamlit columns to display source links and query buttons side-by-side
            col_widths = []
            if has_source:
                col_widths.append(1.5)
            if has_sugg:
                for _ in msg["suggestions"]:
                    col_widths.append(1.0)
            
            if col_widths:
                # Wrap inside a container to enforce bottom margin
                with st.container():
                    cols = st.columns(col_widths)
                    curr_col = 0
                    
                    if has_source:
                        with cols[curr_col]:
                            source = msg["source"]
                            if source.startswith("http"):
                                from source_utils import get_source_display_name
                                display_name = get_source_display_name(source)
                                st.markdown(f'<a href="{source}" target="_blank" class="action-pill">🔗 Source: {display_name}</a>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<span class="action-pill">🔗 Source: {source}</span>', unsafe_allow_html=True)
                            curr_col += 1
                            
                    if has_sugg:
                        for q in msg["suggestions"]:
                            with cols[curr_col]:
                                if st.button(q, key=f"sugg_{idx}_{curr_col}"):
                                    st.session_state.triggered_question = q
                                    st.rerun()
                                curr_col += 1

# Show starter questions after the first message
if st.session_state.show_suggestions and len(st.session_state.messages) == 1:
    st.markdown("<div class='suggested-questions'>", unsafe_allow_html=True)
    st.markdown("**Try asking:**")
    for idx, question in enumerate(STARTER_QUESTIONS):
        if st.button(question, key=f"starter_{idx}", use_container_width=True):
            st.session_state.show_suggestions = False
            st.session_state.triggered_question = question
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Show voice transcription warning if any
if "voice_warning" in st.session_state and st.session_state.voice_warning:
    st.warning(st.session_state.voice_warning)
    del st.session_state.voice_warning

# Native st.chat_input at the top-level (so it is natively position:fixed at the viewport bottom)
user_input = st.chat_input("Ask a question...")

# Render mic recorder at the top-level (will be hidden programmatically by JavaScript)
from streamlit_mic_recorder import mic_recorder
audio = mic_recorder(
    start_prompt="🎤",
    stop_prompt="🛑",
    just_once=True,
    key="mic_recorder",
    use_container_width=True
)

# JavaScript DOM hack: Hooks into parent DOM to setup custom proxy mic button without breaking React
components.html("""
<script>
    const parentDoc = window.parent.document;
    
    function manageMicProxy() {
        // 1. Find the real mic recorder iframe
        const iframe = Array.from(parentDoc.querySelectorAll('iframe')).find(f => {
            return f.src && f.src.includes('streamlit_mic_recorder');
        });
        
        if (iframe) {
            // Find its closest element-container parent
            const micContainer = iframe.closest('div.element-container');
            if (micContainer) {
                // Hide it fully so React doesn't visual render it, but keep it in DOM
                micContainer.style.position = 'absolute';
                micContainer.style.left = '-9999px';
                micContainer.style.top = '-9999px';
                micContainer.style.width = '1px';
                micContainer.style.height = '1px';
                micContainer.style.opacity = '0';
                micContainer.style.pointerEvents = 'none';
            }
            
            // 2. Find stChatInput bar to inject the custom proxy button
            const chatInputBar = parentDoc.querySelector('div[data-testid="stChatInput"] > div');
            if (chatInputBar) {
                let proxyBtn = chatInputBar.querySelector('.custom-mic-btn');
                if (!proxyBtn) {
                    proxyBtn = parentDoc.createElement('button');
                    proxyBtn.className = 'custom-mic-btn';
                    proxyBtn.innerHTML = '🎤';
                    proxyBtn.type = 'button';
                    
                    // Click handler delegates to the button inside the hidden iframe
                    proxyBtn.addEventListener('click', () => {
                        try {
                            const innerDoc = iframe.contentDocument || iframe.contentWindow.document;
                            const realMicBtn = innerDoc.querySelector('button');
                            if (realMicBtn) {
                                realMicBtn.click();
                                
                                // Visual state sync for active/inactive recording
                                if (proxyBtn.innerHTML === '🎤') {
                                    proxyBtn.innerHTML = '🛑';
                                    proxyBtn.style.backgroundColor = '#ef4444';
                                    proxyBtn.style.color = '#ffffff';
                                } else {
                                    proxyBtn.innerHTML = '🎤';
                                    proxyBtn.style.backgroundColor = '#ffffff';
                                    proxyBtn.style.color = '#000000';
                                }
                            }
                        } catch (err) {
                            console.error("Failed to delegate click to hidden mic recorder button:", err);
                        }
                    });
                    
                    chatInputBar.appendChild(proxyBtn);
                }
            }
        }
    }
    
    // Poll DOM every 100ms to preserve layout during Streamlit reruns
    setInterval(manageMicProxy, 100);
</script>
""", height=0)

# Process recorded audio
if audio:
    if "last_processed_audio_id" not in st.session_state:
        st.session_state.last_processed_audio_id = None
        
    audio_id = audio.get("id")
    if audio_id != st.session_state.last_processed_audio_id:
        st.session_state.last_processed_audio_id = audio_id
        audio_bytes = audio["bytes"]
        if audio_bytes:
            api_key = None
            if "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
            if not api_key:
                api_key = os.getenv("GROQ_API_KEY")
                
            if api_key:
                try:
                    transcribed_text = transcribe_audio(audio_bytes, api_key)
                    transcribed_text = transcribed_text.strip()
                    if transcribed_text:
                        st.session_state.triggered_question = f"🎤 {transcribed_text}"
                        st.rerun()
                    else:
                        st.session_state.voice_warning = "Didn't catch that, try again. 🎤"
                        st.rerun()
                except Exception as e:
                    st.session_state.voice_warning = f"Voice transcription error: {str(e)}"
                    st.rerun()
            else:
                st.session_state.voice_warning = "GROQ_API_KEY not configured for voice transcription."
                st.rerun()

# Resolve the prompt
if "triggered_question" in st.session_state:
    prompt = st.session_state.triggered_question
    del st.session_state.triggered_question
else:
    prompt = None

if user_input:
    prompt = user_input

# Handle User Input
if prompt:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=user_avatar_path):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant", avatar=bot_avatar_path):
        with st.spinner("Analyzing documents..."):
            try:
                # Strip the 🎤 emoji prefix if present so RAG backend handles raw query
                processing_prompt = prompt
                if processing_prompt.startswith("🎤 "):
                    processing_prompt = processing_prompt[2:]
                elif processing_prompt.startswith("🎤"):
                    processing_prompt = processing_prompt[1:]
                
                # 1. Check for conversational triggers
                conversational_triggers = {"ok", "okay", "thanks", "thank you", "got it", "thx", "cheers", "cool", "👍", "yes", "hi", "hello"}
                cleaned_query = "".join(char for char in processing_prompt.lower() if char.isalnum() or char.isspace()).strip()
                
                # Setup defaults
                response_text = ""
                first_source = None
                suggestions = []

                if cleaned_query in conversational_triggers:
                    response_text = "You’re welcome! 🙂 What else would you like to know about mutual funds?"
                else:
                    # 2. Query Classification
                    classification = classifier.classify(processing_prompt)
                    
                    if classification['type'] == 'advisory':
                        # Advisory question - polite refusal
                        refusal = refusal_handler.get_refusal(processing_prompt, classification)
                        response_text = refusal['message']
                        first_source = refusal['educational_link']
                        suggestions = refusal['suggestions']
                    else:
                        # Factual question - proceed with RAG
                        # 3. Retrieval
                        chunks = retriever.retrieve(processing_prompt, k=5)
                        
                        # Check if we have good chunks
                        if not chunks or (chunks and chunks[0].get('score', 0) < 0.5):
                            # No answer available
                            response_text = "I don't know based on the provided sources 🙂 Try asking about specific fund details like expense ratio, SIP amount, or lock-in period."
                            first_source = None  # NO SOURCE
                            suggestions = suggestions_handler.get_no_answer_suggestions()
                        else:
                            # 4. Generation
                            response_text = generator.generate_answer(processing_prompt, chunks)
                    
                    # 5. Source Extraction (only for factual answers with chunks)
                    if classification.get('type') == 'factual' and chunks and chunks[0].get('score', 0) >= 0.5:
                        sources = [
                            chunk.get('metadata', {}).get('source_url') or 
                            chunk.get('metadata', {}).get('source_file')
                            for chunk in chunks
                        ]
                        sources = [s for s in sources if s]
                        
                        if sources:
                            first_source = sources[0]

                # Format response fact blockquotes
                formatted_response = format_response_markdown(response_text)
                st.markdown(formatted_response)
                
                # Display source below the message (if available)
                if first_source:
                    if first_source.startswith("http"):
                        from source_utils import get_source_display_name
                        display_name = get_source_display_name(first_source)
                        st.markdown(f'<div class="actions-row"><a href="{first_source}" target="_blank" class="action-pill">🔗 Source: {display_name}</a></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="actions-row"><span class="action-pill">🔗 Source: {first_source}</span></div>', unsafe_allow_html=True)
                
                # Pre-generate TTS audio bytes in parallel with response creation
                try:
                    audio_fp = text_to_speech(response_text)
                    audio_bytes = audio_fp.getvalue() if hasattr(audio_fp, 'getvalue') else audio_fp.read()
                except Exception:
                    audio_bytes = None

                # Update History with source, suggestions, and preloaded audio bytes
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text,
                    "source": first_source,
                    "suggestions": suggestions,
                    "audio_bytes": audio_bytes
                })
                
                st.rerun() # Force rerun to clean layout
                
            except Exception as e:
                st.error(f"❌ Error: {type(e).__name__}: {str(e)}")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"Sorry, I encountered an error. Please check:\n\n1. API key is correctly set in Streamlit Cloud Secrets\n2. All dependencies are installed\n3. Vector database files are present\n\nError: {str(e)}",
                    "source": None,
                    "suggestions": []
                })

# Disclaimer text positioned at the bottom viewport
st.markdown('<div class="bottom-disclaimer">MF Facts AI can provide financial data but should not be considered investment advice.</div>', unsafe_allow_html=True)
