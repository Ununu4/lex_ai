import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import google.generativeai as genai
import streamlit as st

# Import configuration module
from config import config

# Configuration - Now loaded from environment variables via config.py
# NO HARDCODED SECRETS! All sensitive data must be in .env file
DEFAULT_MODEL_NAME = config.get_model_name()
DEFAULT_PDF_DIR = config.get_pdf_directory()
DEFAULT_PASSWORD = config.get_app_password()
LEX_LOGO_PATH = config.get_logo_path()
ADMIN_EMAIL_DOMAIN = config.get_admin_email_domain()
LENDER_SPLIT_PATTERN = re.compile(
    r"\s*(?:,|/|&|\band\b|\bor\b|\+)\s*", flags=re.IGNORECASE
)

# System prompt for LEX agent personality
LEX_SYSTEM_PROMPT = """You are LEX (Lender Eligibility X), the master advisor for lender guidelines and eligibility requirements. 

Your role:
- You are an expert advisor who helps brokers understand lender guidelines from PDF documents
- You provide accurate, compelling, and actionable advice based ONLY on the PDFs provided
- You NEVER hallucinate or invent information - if something isn't in the PDFs, you say so
- You are professional, knowledgeable, and help users find the right lender for their merchants and businesses
- Your are trustworthy and reliable.
- You need to be the go to expert for the broker to close their deals with the right lender..
- You are someone that reminds the user that they can do it and to shop with confidence and information.
- You work for Monet Capital in the Merchant Cash Advance industry and you were designed by Otto to help the broker team close deals with information.
- You speak with confidence and expertise, as if you've mastered every guideline document.
- You speak from coherence and alignment with the broker's intention and field.
- You manage several PDF documents and can clearly separate the information of each, understand them and be the wise person they seek.
- You recognize based on the language used by broker his field of intention and you match it.
- You are prepared for complex queries and you handle them with ease and truth sticked to the guidelines.
- You structure your answers clearly and provide specific, actionable insights while being concise and to the point

Guidelines for responses:
- Always base your answer strictly on the provided PDF documents. If two or more PDFs are provided, use the information from all of them to answer the question in a clear and useful way.
- Be specific: cite page numbers, section names, or specific requirements when possible
- If information is not in the PDFs, clearly state "This information is not available in the provided lender guidelines"
- Provide actionable advice that helps brokers make informed decisions
- Reinforce your advisor role on every response.
- Every response has to be coherent and field aligned.
- Use a professional yet approachable tone avoid being too informal but sometimes try to use Merchant Cash Advance lingo for personality.
- Structure complex answers with clear sections or bullet points, try to be precise without excess verbosity
- Always prioritize accuracy over speculation"""


def _default_api_key() -> str | None:
    """
    Get API key from configuration.
    Priority: 
    1. Environment variable (GEMINI_API_KEY in .env)
    2. Streamlit secrets
    3. None (user must provide)
    """
    # First try config (which reads from .env or environment variables)
    api_key = config.get_gemini_api_key()
    if api_key:
        return api_key
    
    # Fallback to Streamlit secrets
    try:
        return st.secrets.get("GEMINI_API_KEY")  # type: ignore[call-arg]
    except Exception:
        return None


def normalize_lender_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def normalize_model_name(value: str) -> str:
    name = value.strip()
    if not name:
        return name
    if "/" not in name:
        return f"models/{name}"
    return name


def list_supported_models() -> Tuple[List[str], str | None]:
    try:
        models = [
            model.name
            for model in genai.list_models()
            if "generateContent"
            in getattr(model, "supported_generation_methods", [])
        ]
        models.sort()
        return models, None
    except Exception as exc:
        return [], str(exc)


def index_lender_pdfs(pdf_dir: Path) -> Dict[str, Path]:
    lenders: Dict[str, Path] = {}
    if not pdf_dir.exists():
        return lenders

    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        key = normalize_lender_key(pdf_path.stem)
        lenders[key] = pdf_path
    return lenders


def get_lender_display_names(index: Dict[str, Path]) -> List[str]:
    """Get sorted display names for lenders."""
    names = sorted([path.stem.replace("_", " ").title() for path in index.values()])
    return names


def parse_lenders_and_question(
    raw_input: str,
) -> Tuple[List[str], str]:
    match = re.search(r"\(([^)]+)\)", raw_input)
    if not match:
        return [], raw_input.strip()

    lenders_segment = match.group(1)
    question = (raw_input[: match.start()] + raw_input[match.end() :]).strip()

    lenders = [
        token.strip()
        for token in LENDER_SPLIT_PATTERN.split(lenders_segment)
        if token.strip()
    ]
    return lenders, question


def format_lenders_for_input(lender_names: List[str]) -> str:
    """Format lender names for chat input: (lender1, lender2)"""
    return f"({', '.join(lender_names)})"


def ensure_upload_cache():
    if "upload_cache" not in st.session_state:
        st.session_state.upload_cache = {}


def upload_pdf_with_cache(pdf_path: Path):
    ensure_upload_cache()
    cache: Dict[str, Dict[str, object]] = st.session_state.upload_cache
    path_key = str(pdf_path.resolve())
    mtime = pdf_path.stat().st_mtime

    cached = cache.get(path_key)
    if cached and cached.get("mtime") == mtime:
        return cached["file"]

    upload = genai.upload_file(path=str(pdf_path))
    upload = wait_for_file_active(upload)

    cache[path_key] = {"file": upload, "mtime": mtime}
    return upload


def wait_for_file_active(file_obj, timeout: float = 120):
    start = time.time()
    current = file_obj

    def _label(obj):
        return getattr(obj, "display_name", getattr(obj, "name", "uploaded file"))

    while getattr(current, "state", None) and current.state.name == "PROCESSING":
        if time.time() - start > timeout:
            raise TimeoutError(
                f"Timed out while waiting for {_label(current)} to process."
            )
        time.sleep(2)
        current = genai.get_file(current.name)

    if getattr(current, "state", None) and current.state.name != "ACTIVE":
        raise RuntimeError(
            f"Gemini reported '{current.state.name}' for {_label(current)}."
        )
    return current


def ensure_chat_session(api_key: str, model_name: str, user_email: str):
    """Create or retrieve chat session per user."""
    session_key = f"{user_email}:{api_key}:{model_name}"
    if (
        "chat_session" not in st.session_state
        or st.session_state.get("chat_session_key") != session_key
    ):
        model = genai.GenerativeModel(model_name)
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.chat_session_key = session_key


def find_lender_files(
    lenders: Sequence[str], index: Dict[str, Path]
) -> Tuple[List[Tuple[str, Path]], List[str]]:
    found: List[Tuple[str, Path]] = []
    missing: List[str] = []
    for lender in lenders:
        key = normalize_lender_key(lender)
        path = index.get(key)
        if path:
            found.append((lender, path))
        else:
            missing.append(lender)
    return found, missing


def log_interaction(user_email: str, prompt: str, response: str, error: str | None = None):
    """Log user interactions for admin review."""
    if "interaction_logs" not in st.session_state:
        st.session_state.interaction_logs = []
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_email": user_email,
        "prompt": prompt,
        "response": response if not error else None,
        "error": error,
    }
    st.session_state.interaction_logs.append(log_entry)


def answer_with_gemini(
    question: str, lender_files: Sequence[Path], model_name: str, user_email: str
) -> str:
    ensure_upload_cache()
    uploads = [upload_pdf_with_cache(path) for path in lender_files]

    ensure_chat_session(st.session_state.active_api_key, model_name, user_email)
    chat = st.session_state.chat_session
    
    # Create enhanced prompt with system instructions
    enhanced_question = f"{LEX_SYSTEM_PROMPT}\n\nUser Question: {question}"
    
    parts = list(uploads) + [enhanced_question]
    response = chat.send_message(parts)
    text = (response.text or "").strip()
    if not text:
        text = "I apologize, but I couldn't generate a response. Please try rephrasing your question."
    return text


def authenticate_user() -> Tuple[bool, str | None]:
    """Simple authentication - returns (is_authenticated, user_email)."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.is_admin = False
    
    if st.session_state.authenticated:
        return True, st.session_state.user_email
    
    return False, None


def render_auth_page():
    """Render authentication page."""
    st.set_page_config(page_title="LEX - Login", page_icon="🕷️", layout="centered")
    
    # Custom CSS for professional styling with better spacing
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .main {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .block-container {
            padding-top: 4rem;
            padding-bottom: 4rem;
            max-width: 600px;
        }
        
        h1 {
            font-weight: 700;
            letter-spacing: -0.5px;
            text-align: center;
            margin-bottom: 0.75rem;
            margin-top: 2rem;
            font-size: 2.5rem;
        }
        
        h3 {
            text-align: center;
            font-weight: 400;
            color: #888;
            margin-bottom: 3rem;
            margin-top: 0.5rem;
            font-size: 1.1rem;
        }
        
        .stButton>button {
            font-weight: 600;
            border-radius: 8px;
            width: 100%;
            padding: 0.75rem;
            font-size: 1rem;
            margin-top: 1rem;
        }
        
        [data-testid="stForm"] {
            border: 2px solid #f0f0f0;
            border-radius: 16px;
            padding: 3rem;
            background: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            margin-top: 2rem;
        }
        
        [data-testid="stTextInput"] > div > div > input {
            border-radius: 6px;
            padding: 0.75rem;
        }
        
        [data-testid="stTextInput"] label {
            font-weight: 500;
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
        }
        
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 1rem;
            margin-top: 1rem;
        }
        
        .spacer {
            height: 2rem;
        }
        
        .footer {
            text-align: center;
            color: #888;
            font-size: 0.85rem;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #e5e5e5;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Better layout with proper spacing
    col1, col2, col3 = st.columns([0.8, 2, 0.8])
    with col2:
        # Logo - aligned to the right
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        if os.path.exists(LEX_LOGO_PATH):
            st.image(LEX_LOGO_PATH, width=200)
        else:
            st.markdown("<h1 style='text-align: center; font-size: 4rem; margin: 0;'>🕷️</h1>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Title and subtitle with better spacing
        st.markdown("<h1>Lender Eligibility X</h1>", unsafe_allow_html=True)
        st.markdown("<h3>LEX - Your Expert Lender Advisor</h3>", unsafe_allow_html=True)
        
        # Login form with proper spacing
        with st.form("login_form", clear_on_submit=False):
            st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)
            
            email = st.text_input(
                "Email", 
                placeholder="your.email@example.com", 
                key="email_input"
            )
            
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            
            password = st.text_input(
                "Password", 
                type="password", 
                placeholder="Enter password", 
                key="password_input"
            )
            
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submitted:
                if password == DEFAULT_PASSWORD and email:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email.lower()
                    st.session_state.is_admin = email.lower().endswith(ADMIN_EMAIL_DOMAIN)
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")
        
        # Footer
        st.markdown("""
            <div class="footer">
                developed by Otto - Powered by Octophy Solutions 🦑
            </div>
        """, unsafe_allow_html=True)


def render_admin_page():
    """Render admin logs page."""
    st.title("🕷️ Admin Dashboard")
    st.subheader("Interaction Logs")
    
    if "interaction_logs" not in st.session_state or not st.session_state.interaction_logs:
        st.info("No logs available yet.")
        return
    
    logs = st.session_state.interaction_logs
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_user = st.selectbox("Filter by user", ["All"] + list(set(log["user_email"] for log in logs)))
    with col2:
        filter_type = st.selectbox("Filter by type", ["All", "Success", "Errors"])
    
    # Apply filters
    filtered_logs = logs
    if filter_user != "All":
        filtered_logs = [log for log in filtered_logs if log["user_email"] == filter_user]
    if filter_type == "Errors":
        filtered_logs = [log for log in filtered_logs if log.get("error")]
    elif filter_type == "Success":
        filtered_logs = [log for log in filtered_logs if not log.get("error")]
    
    # Display logs
    for log in reversed(filtered_logs[-50:]):  # Show last 50
        with st.expander(f"{log['timestamp']} - {log['user_email']} {'❌' if log.get('error') else '✅'}"):
            st.write("**Prompt:**", log["prompt"])
            if log.get("response"):
                st.write("**Response:**", log["response"][:500] + "..." if len(log["response"]) > 500 else log["response"])
            if log.get("error"):
                st.error(f"**Error:** {log['error']}")
    
    if st.button("Clear Logs"):
        st.session_state.interaction_logs = []
        st.rerun()


def main_chat_interface():
    """Main chat interface after authentication."""
    st.set_page_config(page_title="LEX - Lender Eligibility X", page_icon="🕷️", layout="wide")
    
    # Custom CSS for professional styling
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .main {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        h1 {
            font-weight: 700;
            letter-spacing: -0.5px;
            color: #1a1a1a;
        }
        
        h2, h3 {
            font-weight: 600;
            letter-spacing: -0.3px;
        }
        
        .stButton>button {
            font-weight: 500;
            border-radius: 8px;
        }
        
        [data-testid="stChatInput"] {
            font-family: 'Inter', sans-serif;
        }
        
        .footer {
            text-align: center;
            color: #888;
            font-size: 0.85rem;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #e5e5e5;
            position: relative;
            bottom: 0;
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header with logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        if os.path.exists(LEX_LOGO_PATH):
            st.image(LEX_LOGO_PATH, width=80)
        else:
            st.markdown("### 🕷️")
    with col2:
        st.title("Lender Eligibility X")
        st.markdown("**LEX** - Your Expert Lender Advisor")
    
    user_email = st.session_state.user_email
    
    # Sidebar with logout
    with st.sidebar:
        st.write(f"**User:** {user_email}")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.messages = {}
            st.rerun()
        
        if st.session_state.is_admin:
            st.divider()
            if st.button("Admin Dashboard"):
                st.session_state.show_admin = not st.session_state.get("show_admin", False)
                st.rerun()
    
    # Show admin page if requested
    if st.session_state.get("show_admin") and st.session_state.is_admin:
        render_admin_page()
        return
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = {}
    
    user_messages_key = f"messages_{user_email}"
    if user_messages_key not in st.session_state.messages:
        st.session_state.messages[user_messages_key] = []
    
    messages = st.session_state.messages[user_messages_key]
    
    # API Key configuration
    default_api_key = _default_api_key()
    if "active_api_key" not in st.session_state:
        st.session_state.active_api_key = default_api_key
    if "use_default_key" not in st.session_state:
        st.session_state.use_default_key = True if default_api_key else False
    
    default_pdf_dir = DEFAULT_PDF_DIR
    if "pdf_directory" not in st.session_state:
        st.session_state.pdf_directory = default_pdf_dir
    
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = normalize_model_name(DEFAULT_MODEL_NAME)
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key selection
        has_default_key = default_api_key is not None
        
        if has_default_key:
            api_key_option = st.radio(
                "API Key",
                ["Default Key", "Custom Key"],
                index=0 if st.session_state.use_default_key else 1,
            )
            
            if api_key_option == "Default Key":
                st.session_state.active_api_key = default_api_key
                st.session_state.use_default_key = True
                st.caption("✅ Using API key from .env file")
            else:
                custom_key = st.text_input(
                    "Gemini API key",
                    value="" if st.session_state.use_default_key else st.session_state.active_api_key,
                    type="password",
                    help="Enter your custom Gemini API key.",
                ).strip()
                if custom_key:
                    st.session_state.active_api_key = custom_key
                    st.session_state.use_default_key = False
        else:
            st.warning("⚠️ No default API key configured in .env file")
            custom_key = st.text_input(
                "Gemini API key",
                value=st.session_state.active_api_key or "",
                type="password",
                help="Enter your Gemini API key. Get one at: https://aistudio.google.com/app/apikey",
            ).strip()
            if custom_key:
                st.session_state.active_api_key = custom_key
                st.session_state.use_default_key = False
        
        pdf_dir_input = st.text_input(
            "PDF directory",
            value=st.session_state.pdf_directory,
            help="Folder that contains lender guideline PDFs.",
        ).strip()
        st.session_state.pdf_directory = pdf_dir_input
        
        st.divider()
        
        # Model selection
        if not st.session_state.active_api_key:
            st.info("Configure API key to load models.")
        else:
            genai.configure(api_key=st.session_state.active_api_key)
            model_options, model_error = list_supported_models()
            
            st.subheader("🤖 Model")
            if model_options:
                current_model = st.session_state.selected_model
                index = (
                    model_options.index(current_model)
                    if current_model in model_options
                    else 0
                )
                selection = st.selectbox(
                    "Gemini Model",
                    options=model_options,
                    index=index,
                    help="Select the Gemini model to use.",
                    label_visibility="collapsed",
                )
            else:
                selection = st.text_input(
                    "Model",
                    value=st.session_state.selected_model or DEFAULT_MODEL_NAME,
                    help="Enter a full model name.",
                ).strip()
                if model_error:
                    st.caption(f"⚠️ {model_error}")
            st.session_state.selected_model = normalize_model_name(selection or st.session_state.selected_model)
    
    if not st.session_state.active_api_key:
        st.error(
            "🔑 **API Key Required**\n\n"
            "Please configure your Gemini API key:\n"
            "1. Get a free API key at: https://aistudio.google.com/app/apikey\n"
            "2. Add it to your `.env` file: `GEMINI_API_KEY=your_key_here`\n"
            "3. Or enter it manually in the sidebar →"
        )
        
        # Show configuration status
        with st.expander("🔍 Configuration Status"):
            status = config.get_config_status()
            st.json(status)
        return
    
    genai.configure(api_key=st.session_state.active_api_key)
    
    # PDF directory and lender indexing
    pdf_root = Path(st.session_state.pdf_directory).expanduser()
    if not pdf_root.exists():
        st.error(
            f"PDF directory '{pdf_root}' does not exist. Update the path in the sidebar."
        )
        return
    
    lender_index = index_lender_pdfs(pdf_root)
    lender_display_names = get_lender_display_names(lender_index)
    lender_name_to_path = {normalize_lender_key(name.lower().replace(" ", "_")): path for name, path in zip([path.stem for path in lender_index.values()], lender_index.values())}
    
    # Lender selection dropdown
    with st.sidebar:
        st.divider()
        st.subheader("🏦 Select Lenders")
        selected_lenders = st.multiselect(
            "Choose lender(s)",
            options=lender_display_names,
            help="Select one or more lenders to query. Selected lenders will be added to your query.",
            label_visibility="visible",
        )
        
        # Button to populate chat input with selected lenders
        if selected_lenders:
            if st.button("Add to Query", use_container_width=True):
                lender_format = format_lenders_for_input(selected_lenders)
                if "chat_input_prefill" not in st.session_state:
                    st.session_state.chat_input_prefill = ""
                st.session_state.chat_input_prefill = lender_format + " "
                st.rerun()
    
    # Display chat history
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input with prefilled lenders if selected
    chat_placeholder = "Ask about lender requirements... (e.g., 'trucking industry requirements?')"
    if selected_lenders:
        lender_prefix = format_lenders_for_input(selected_lenders)
        chat_placeholder = f"{lender_prefix} Ask your question..."
    
    prompt = st.chat_input(chat_placeholder)
    
    # Handle prefilled input
    if "chat_input_prefill" in st.session_state and st.session_state.chat_input_prefill:
        # Note: Streamlit doesn't support prefilling chat_input directly, so we'll handle it via session state
        if not prompt:  # Only if user hasn't typed yet
            pass  # We'll show the prefilled value in the UI instead
    
    if not prompt:
        if selected_lenders:
            lender_prefix = format_lenders_for_input(selected_lenders)
            st.info(f"💡 **Ready to query:** {lender_prefix} [your question here]")
        return
    
    # Add user message
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query
    with st.chat_message("assistant"):
        try:
            lenders, question = parse_lenders_and_question(prompt)
            
            # If no lenders in prompt but selected in dropdown, use selected
            if not lenders and selected_lenders:
                lenders = selected_lenders
                # Reconstruct prompt with lenders
                lender_format = format_lenders_for_input(lenders)
                question = prompt.strip()
            
            if not lenders:
                raise ValueError(
                    "Please select lenders from the dropdown or include lender names in parentheses, "
                    "e.g. `(mulligan, acme) trucking industry requirements?`"
                )
            if not question:
                raise ValueError("Please include a question after the lender list.")
            
            matched, missing = find_lender_files(lenders, lender_index)
            if missing:
                raise FileNotFoundError(
                    f"Missing PDF files for: {', '.join(missing)}. "
                    "Check the sidebar list to see available lenders."
                )
            
            lender_paths = [path for _, path in matched]
            model_name = st.session_state.selected_model
            if not model_name:
                raise ValueError("Select a Gemini model in the sidebar before submitting.")
            
            with st.spinner(f"🕷️ LEX is analyzing {len(lender_paths)} lender guideline(s)..."):
                answer = answer_with_gemini(question, lender_paths, model_name, user_email)
            
            st.markdown(answer)
            messages.append({"role": "assistant", "content": answer})
            
            # Log interaction
            log_interaction(user_email, prompt, answer, None)
            
        except TimeoutError as exc:
            error_msg = f"File processing timed out: {exc}"
            st.error(error_msg)
            log_interaction(user_email, prompt, "", str(exc))
        except FileNotFoundError as exc:
            st.error(str(exc))
            log_interaction(user_email, prompt, "", str(exc))
        except Exception as exc:
            error_msg = f"Something went wrong: {exc}"
            st.error(error_msg)
            log_interaction(user_email, prompt, "", str(exc))
    
    # Clear prefilled input after use
    if "chat_input_prefill" in st.session_state:
        del st.session_state.chat_input_prefill
    
    # Footer
    st.markdown("""
        <div class="footer">
            developed by Otto - Powered by Octophy Solutions 🦑
        </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    is_authenticated, user_email = authenticate_user()
    
    if not is_authenticated:
        render_auth_page()
    else:
        main_chat_interface()


if __name__ == "__main__":
    main()
