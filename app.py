import os

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv("BEAVELO_API_URL", "http://127.0.0.1:8000")
GITHUB_REPOSITORY_URL = os.getenv(
    "GITHUB_REPOSITORY_URL",
    "https://github.com/Sudheesh901/text-to-sql-query-Azure",
).rstrip("/")


st.set_page_config(
    page_title="SQL Query Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
        :root { --ink: #202432; --muted: #687083; --line: #e5e8ef; --canvas: #ffffff; --panel: #ffffff; --surface: #f5f7fb; --accent: #2563eb; --accent-dark: #1d4ed8; }
        .stApp { background: var(--canvas); color: var(--ink); }
        [data-testid="stHeader"] { background: rgba(255, 255, 255, 0.94); border-bottom: 1px solid var(--line); }
        [data-testid="stSidebar"] { background: #f6f8fc; border-right: 1px solid var(--line); }
        [data-testid="stSidebar"] > div:first-child { padding: 2.2rem 1.5rem; }
        /* Community Cloud keeps its own toolbar fixed at the top of the page. */
        .block-container { max-width: 1060px; padding-top: 5rem; padding-bottom: 4rem; }
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.25rem 0 1.4rem;
            margin-bottom: 3.25rem;
            border-bottom: 1px solid var(--line);
        }
        .product-label {
            color: var(--ink);
            font-size: 1rem;
            font-weight: 750;
            letter-spacing: -0.02em;
        }
        .nav-links { display: flex; align-items: center; gap: 0.8rem; }
        .nav-link {
            color: var(--muted) !important;
            font-size: 0.88rem;
            font-weight: 600;
            text-decoration: none !important;
            padding: 0.48rem 0.75rem;
            border-radius: 0.48rem;
        }
        .nav-link:hover { color: var(--ink) !important; background: var(--surface); }
        .fork-link { background: var(--ink); color: #fff !important; }
        .fork-link:hover { background: #343b4e; }
        .github-icon-link { display: inline-flex; align-items: center; justify-content: center; padding: 0.42rem; }
        .github-icon { display: block; width: 1.25rem; height: 1.25rem; }
        .eyebrow {
            color: var(--accent-dark);
            font-size: 0.72rem;
            font-weight: 780;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            margin-bottom: 0.72rem;
        }
        .hero-title {
            max-width: 690px;
            margin: 0;
            font-size: clamp(2.3rem, 5vw, 3.8rem);
            line-height: 1.08;
            letter-spacing: -0.05em;
            color: var(--ink);
        }
        .hero-copy {
            max-width: 630px;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.62;
            margin: 1rem 0 2.4rem;
        }
        .plain-language-card {
            margin: 0 0 2.2rem;
            padding: 1.25rem 1.35rem;
            border: 1px solid #dce3f0;
            border-radius: 0.9rem;
            background: var(--panel);
        }
        .plain-language-card h3 {
            margin: 0 0 0.38rem;
            color: var(--ink);
            font-size: 0.98rem;
            letter-spacing: -0.015em;
        }
        .plain-language-card p {
            margin: 0;
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.58;
        }
        .plain-language-steps {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1rem;
        }
        .plain-language-step {
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.45;
        }
        .plain-language-step strong { color: var(--ink); display: block; margin-bottom: 0.16rem; }
        .workspace-kicker, .section-title {
            color: var(--ink);
            font-size: 0.9rem;
            font-weight: 750;
            letter-spacing: -0.01em;
        }
        .workspace-kicker { margin-bottom: 0.55rem; }
        .helper-copy {
            color: var(--muted);
            font-size: 0.84rem;
            margin: 0.25rem 0 0.9rem;
        }
        [data-testid="stForm"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 0.9rem;
            padding: 1.1rem;
            box-shadow: 0 12px 34px rgba(36, 55, 91, 0.06);
        }
        .stTextArea textarea, .stTextInput input {
            background: #fff !important;
            border: 1px solid #cfd7e6 !important;
            border-radius: 0.65rem !important;
            color: var(--ink) !important;
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        .stTextArea textarea:focus, .stTextInput input:focus {
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.13) !important;
        }
        .stButton > button, .stFormSubmitButton > button {
            min-height: 2.6rem;
            border: 0 !important;
            border-radius: 0.62rem !important;
            background: var(--accent) !important;
            color: white !important;
            font-size: 0.92rem !important;
            font-weight: 680 !important;
            transition: transform 120ms ease, background 120ms ease;
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover {
            background: var(--accent-dark) !important;
            transform: translateY(-1px);
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--line) !important;
            border-radius: 0.75rem !important;
            background: rgba(255, 255, 255, 0.58);
        }
        [data-testid="stExpander"] summary {
            color: var(--muted) !important;
            font-size: 0.87rem !important;
        }
        .result-heading {
            margin: 2.15rem 0 0.7rem;
            color: var(--ink);
            font-size: 1.05rem;
            font-weight: 750;
            letter-spacing: -0.025em;
        }
        .result-meta {
            color: var(--muted);
            font-size: 0.83rem;
            margin: -0.33rem 0 0.75rem;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 0.75rem;
            overflow: hidden;
        }
        .stAlert { border-radius: 0.75rem; }
        .sidebar-copy { color: var(--muted); font-size: 0.9rem; line-height: 1.6; }
        .sidebar-eyebrow { color: var(--accent-dark); font-size: 0.72rem; font-weight: 750; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.75rem; }
        .sidebar-step { display: flex; gap: 0.75rem; align-items: flex-start; margin: 1rem 0; color: var(--muted); font-size: 0.9rem; line-height: 1.45; }
        .step-number { flex: 0 0 1.5rem; height: 1.5rem; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; background: #e7efff; color: var(--accent-dark); font-size: 0.75rem; font-weight: 800; }
        @media (max-width: 700px) {
            .block-container { padding-top: 4.5rem; }
            .topbar { margin-bottom: 2.4rem; }
            .hero-title { font-size: 2.45rem; }
            .plain-language-steps { grid-template-columns: 1fr; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialise_state():
    """Create session keys once so UI state persists through Streamlit reruns."""
    defaults = {
        "question_input": "",
        "pending_question": None,
        "clarification": None,
        "sql_query": None,
        "results": None,
        "notice": None,
        "error": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_workspace():
    """Clear the current query workspace without changing backend state."""
    for key in (
        "question_input",
        "pending_question",
        "clarification",
        "sql_query",
        "results",
        "notice",
        "error",
    ):
        st.session_state[key] = "" if key == "question_input" else None


def ask_data_service(question):
    """Call the FastAPI backend and return its JSON response."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/query",
            json={"question": question},
            timeout=45,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise RuntimeError(
            "The data service is temporarily unavailable. Please try again."
        ) from error


def process_question(question):
    """Send a question to the API and store its UI-ready response."""
    clean_question = question.strip()
    if not clean_question:
        return

    st.session_state.results = None
    st.session_state.sql_query = None
    st.session_state.error = None
    st.session_state.notice = None

    if clean_question.lower() in {"hi", "hello", "hey"}:
        st.session_state.notice = "Hello — what would you like to learn from your data?"
        return

    try:
        response = ask_data_service(clean_question)
    except RuntimeError as error:
        st.session_state.error = str(error)
        return

    status = response.get("status")
    if status == "clarification":
        st.session_state.pending_question = clean_question
        st.session_state.clarification = response.get(
            "message",
            "Could you clarify your question?",
        )
        return
    if status == "error":
        st.session_state.error = response.get(
            "message",
            "We could not complete that request.",
        )
        return

    if status != "success":
        st.session_state.error = "The API returned an unexpected response."
        return

    st.session_state.sql_query = response.get("sql")
    st.session_state.results = pd.DataFrame(
        response.get("rows", []),
        columns=response.get("columns", []),
    )


initialise_state()

with st.sidebar:
    st.markdown("<div class='sidebar-eyebrow'>SQL Query Studio</div>", unsafe_allow_html=True)
    st.markdown("## How to use")
    st.markdown(
        """
        <div class='sidebar-step'><span class='step-number'>1</span><span>Describe the business question you want answered.</span></div>
        <div class='sidebar-step'><span class='step-number'>2</span><span>Review the returned data and generated SQL.</span></div>
        <div class='sidebar-step'><span class='step-number'>3</span><span>Refine the question when you need a different view.</span></div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("New question", use_container_width=True):
        reset_workspace()
        st.rerun()
    st.divider()
    st.markdown("### About")
    st.markdown(
        "<p class='sidebar-copy'>A practical, open-source interface for exploring business data in plain language. Queries are generated as read-only SQL for review.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f"[View source on GitHub]({GITHUB_REPOSITORY_URL})")


st.markdown(
    """
    <div class='topbar'>
        <div class='product-label'>SQL Query Studio</div>
        <div class='nav-links'>
            <a class='nav-link github-icon-link' href='https://github.com/Sudheesh901/text-to-sql-query-Azure' target='_blank' rel='noopener' aria-label='View source on GitHub' title='View source on GitHub'>
                <img class='github-icon' src='https://github.githubassets.com/favicons/favicon.svg' alt='GitHub'>
            </a>
            <a class='nav-link fork-link' href='https://github.com/Sudheesh901/text-to-sql-query-Azure/fork' target='_blank' rel='noopener'>Fork on GitHub</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<div class='eyebrow'>Natural-language analytics</div>", unsafe_allow_html=True)
st.markdown("<h1 class='hero-title'>Ask better questions of your business data.</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='hero-copy'>Write your question as you would ask a colleague. The workspace generates a read-only SQL query and returns the data you need—without requiring SQL expertise.</p>",
    unsafe_allow_html=True,
)

st.markdown("<div class='workspace-kicker'>Ask a question</div>", unsafe_allow_html=True)
st.markdown("<div class='helper-copy'>Start with the business outcome you need — not the tables or columns.</div>", unsafe_allow_html=True)

with st.expander("Try an example question"):
    example_columns = st.columns(3)
    examples = [
        "Which customers are located in Germany?",
        "Show the top 3 products by quantity ordered.",
        "What were the total orders by month?",
    ]
    for column, example in zip(example_columns, examples):
        with column:
            if st.button(example, key=f"example_{example}", use_container_width=True):
                st.session_state.question_input = example

with st.form("question_form", clear_on_submit=False):
    question = st.text_area(
        "Your question",
        key="question_input",
        placeholder="For example: Which suppliers provide the most products?",
        height=108,
        label_visibility="collapsed",
    )
    submit = st.form_submit_button("Generate answer", use_container_width=True)
if submit:
    with st.spinner("Preparing your answer..."):
        process_question(question)

if st.session_state.clarification:
    st.markdown("<div class='result-heading'>One detail before we continue</div>", unsafe_allow_html=True)
    st.info(st.session_state.clarification)
    with st.form("clarification_form"):
        clarification_answer = st.text_input(
            "Your answer",
            placeholder="For example: Across all products",
        )
        clarification_submit = st.form_submit_button("Continue", use_container_width=True)

    if clarification_submit:
        if clarification_answer.strip():
            follow_up_question = f"""
Original user question:
{st.session_state.pending_question}

Clarification answer from user:
{clarification_answer.strip()}

Generate the SQL query now.
"""
            st.session_state.pending_question = None
            st.session_state.clarification = None
            with st.spinner("Applying your clarification..."):
                process_question(follow_up_question)
            st.rerun()
        else:
            st.warning("Please add a short answer so the query can continue.")

if st.session_state.notice:
    st.success(st.session_state.notice)

if st.session_state.error:
    st.error(f"We could not complete that request. {st.session_state.error}")

if st.session_state.results is not None:
    st.markdown("<div class='result-heading'>Results</div>", unsafe_allow_html=True)
    result_count = len(st.session_state.results) if hasattr(st.session_state.results, "__len__") else None
    if result_count is not None:
        st.markdown(f"<div class='result-meta'>{result_count} row{'s' if result_count != 1 else ''} returned</div>", unsafe_allow_html=True)

    if hasattr(st.session_state.results, "empty") and st.session_state.results.empty:
        st.info("The query ran successfully, but no matching records were found.")
    else:
        st.dataframe(st.session_state.results, use_container_width=True, hide_index=True)

if st.session_state.sql_query:
    with st.expander("View generated SQL"):
        st.code(st.session_state.sql_query, language="sql")

with st.expander("About this workspace"):
    st.markdown(
        "This workspace uses your database schema to translate business questions into read-only SQL. "
        "Generated SQL is available above for review whenever you need it."
    )
