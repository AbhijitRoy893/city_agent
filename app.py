"""
app.py
------
Streamlit front-end for CityPilot (see main.py).

Run with:
    streamlit run app.py
"""

import html
import streamlit as st
from main import build_agent, TOOLS, extract_text

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="CityPilot",
    page_icon="🏙️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =========================
# Skyline mark (used once, in the header — the one deliberate visual moment)
# NOTE: kept as a single line on purpose — Streamlit's markdown renderer
# treats 4+ leading spaces as a code block, so any multi-line HTML/SVG
# passed to st.markdown must avoid indentation, or be flattened like this.
# =========================
SKYLINE_SVG = (
    '<svg viewBox="0 0 220 60" xmlns="http://www.w3.org/2000/svg" class="skyline-mark">'
    '<rect x="4" y="30" width="16" height="30" fill="#1B2740"/>'
    '<rect x="24" y="18" width="14" height="42" fill="#233252"/>'
    '<rect x="42" y="34" width="12" height="26" fill="#1B2740"/>'
    '<rect x="58" y="10" width="16" height="50" fill="#2B3D63"/>'
    '<rect x="78" y="26" width="12" height="34" fill="#1B2740"/>'
    '<rect x="94" y="16" width="14" height="44" fill="#233252"/>'
    '<rect x="112" y="36" width="12" height="24" fill="#1B2740"/>'
    '<rect x="128" y="6" width="16" height="54" fill="#2B3D63"/>'
    '<rect x="148" y="24" width="12" height="36" fill="#1B2740"/>'
    '<rect x="164" y="14" width="14" height="46" fill="#233252"/>'
    '<rect x="182" y="32" width="12" height="28" fill="#1B2740"/>'
    '<rect x="198" y="20" width="16" height="40" fill="#2B3D63"/>'
    '<circle cx="188" cy="16" r="7" fill="#E8A33D"/>'
    '<rect x="60" y="16" width="3" height="3" fill="#E8A33D"/>'
    '<rect x="98" y="24" width="3" height="3" fill="#E8A33D"/>'
    '<rect x="132" y="14" width="3" height="3" fill="#E8A33D"/>'
    '<rect x="168" y="22" width="3" height="3" fill="#E8A33D"/>'
    "</svg>"
)

# =========================
# Styling
# NOTE: CSS is inside a <style> block, so indentation there is harmless —
# only literal HTML markup (rendered via st.markdown) needs to avoid it.
# =========================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --bg:        #0B1120;
    --panel:     #111A2E;
    --panel-2:   #16213A;
    --line:      #223050;
    --text:      #E7EAF0;
    --muted:     #7C8AA5;
    --amber:     #E8A33D;
    --teal:      #4FD1C5;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: var(--bg); color: var(--text); }

.header-wrap {
    position: relative;
    padding: 0.5rem 0 1.6rem 0;
    border-bottom: 1px solid var(--line);
    margin-bottom: 1.6rem;
}
.skyline-mark {
    position: absolute;
    top: -6px;
    right: 0;
    width: 180px;
    opacity: 0.55;
}
.wordmark {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 2.4rem;
    letter-spacing: -0.02em;
    color: var(--text);
    margin: 0;
    line-height: 1.1;
}
.wordmark span { color: var(--amber); }
.tagline {
    font-family: 'Inter', sans-serif;
    color: var(--muted);
    font-size: 1rem;
    margin-top: 0.35rem;
    max-width: 34ch;
}

section[data-testid="stSidebar"] {
    background: var(--panel);
    border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }
.side-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--text);
    margin-bottom: 0.2rem;
}
.side-desc {
    color: var(--muted);
    font-size: 0.88rem;
    line-height: 1.5;
    margin-bottom: 1rem;
}
.side-label {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.78rem;
    color: var(--muted);
    margin: 1.1rem 0 0.6rem 0;
}
.capability {
    border-left: 2px solid var(--teal);
    padding: 0.15rem 0 0.15rem 0.7rem;
    margin-bottom: 0.6rem;
}
.capability-name {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: var(--teal);
}
.capability-desc {
    font-size: 0.82rem;
    color: var(--muted);
    margin-top: 0.1rem;
}
.side-footer {
    color: var(--muted);
    font-size: 0.78rem;
    line-height: 1.5;
    margin-top: 1.5rem;
    border-top: 1px solid var(--line);
    padding-top: 1rem;
}

hr { border-color: var(--line); }

.stButton > button {
    background: transparent;
    border: 1px solid var(--line);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    border-radius: 6px;
}
.stButton > button:hover {
    border-color: var(--amber);
    color: var(--amber);
}

[data-testid="stChatMessage"] {
    background: transparent;
    border-radius: 8px;
    padding: 0.4rem 0.2rem;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    border-left: 2px solid var(--teal);
    padding-left: 0.9rem;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    border-right: 2px solid var(--amber);
    padding-right: 0.9rem;
}

[data-testid="stChatInput"] textarea {
    background: var(--panel-2) !important;
    border: 1px solid var(--line) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif;
}
[data-testid="stChatInput"] {
    border-color: var(--line) !important;
}

.tool-console {
    font-family: 'IBM Plex Mono', monospace;
    background: var(--panel-2);
    border: 1px solid var(--line);
    border-left: 2px solid var(--teal);
    border-radius: 4px;
    padding: 0.7rem 0.85rem;
    margin-bottom: 0.6rem;
}
.tool-console-name {
    color: var(--teal);
    font-size: 0.8rem;
    font-weight: 500;
}
.tool-console-args {
    color: var(--muted);
    font-size: 0.76rem;
    margin: 0.25rem 0 0.5rem 0;
    word-break: break-word;
}
.tool-console-result {
    color: var(--text);
    font-size: 0.78rem;
    white-space: pre-wrap;
    line-height: 1.5;
    border-top: 1px dashed var(--line);
    padding-top: 0.5rem;
}

[data-testid="stExpander"] {
    border: 1px solid var(--line);
    border-radius: 6px;
    background: var(--panel);
}
</style>
""",
    unsafe_allow_html=True,
)


def render_tool_console(calls):
    """Render tool calls as a monospace telemetry block instead of chat badges.

    Built as single-line HTML strings (no indentation/newlines) so
    Streamlit's markdown renderer doesn't mistake them for a code block.
    """
    for call in calls:
        args_str = ", ".join(f"{k}={v!r}" for k, v in call["args"].items())
        block = (
            '<div class="tool-console">'
            f'<div class="tool-console-name">{html.escape(call["name"])}()</div>'
            f'<div class="tool-console-args">{html.escape(args_str)}</div>'
            f'<div class="tool-console-result">{html.escape(str(call["result"]))}</div>'
            "</div>"
        )
        st.markdown(block, unsafe_allow_html=True)


# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown('<div class="side-title">CityPilot</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="side-desc">A LangChain agent on Gemini that decides for '
        "itself when to check live weather or search the news for a city.</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-label">CAPABILITIES</div>', unsafe_allow_html=True)
    for t in TOOLS:
        block = (
            '<div class="capability">'
            f'<div class="capability-name">{html.escape(t.name)}</div>'
            f'<div class="capability-desc">{html.escape(t.description)}</div>'
            "</div>"
        )
        st.markdown(block, unsafe_allow_html=True)

    show_tool_calls = st.toggle("Show tool activity", value=True)

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown(
        '<div class="side-footer">Agent framework: LangChain<br>'
        "Model: Gemini<br>"
        "Search: Tavily<br>"
        "Weather: OpenWeatherMap</div>",
        unsafe_allow_html=True,
    )

# =========================
# Header
# =========================
header_block = (
    '<div class="header-wrap">'
    + SKYLINE_SVG
    + '<div class="wordmark">City<span>Pilot</span></div>'
    + '<div class="tagline">Live weather and local news for any city, '
    "answered by an agent that chooses its own tools.</div>"
    "</div>"
)
st.markdown(header_block, unsafe_allow_html=True)

# =========================
# Session state
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    # No blocking CLI-style approval here — a synchronous web request can't
    # pause for terminal input(). Tool calls are instead shown transparently
    # via the telemetry block below.
    st.session_state.agent = build_agent(with_cli_approval=False)

# =========================
# Render chat history
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls") and show_tool_calls:
            render_tool_console(msg["tool_calls"])

# =========================
# Chat input
# =========================
user_input = st.chat_input("Ask about your city's weather and what's happening around you")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Checking..."):
            result = st.session_state.agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]}
            )
            final_messages = result["messages"]
            reply = extract_text(final_messages[-1].content)

            # Collect any tool calls made during this turn for transparency
            tool_calls_info = []
            tool_call_index = {}
            for m in final_messages:
                if getattr(m, "tool_calls", None):
                    for tc in m.tool_calls:
                        tool_call_index[tc["id"]] = {
                            "name": tc["name"],
                            "args": tc["args"],
                        }
                if m.__class__.__name__ == "ToolMessage" and m.tool_call_id in tool_call_index:
                    entry = tool_call_index[m.tool_call_id]
                    entry["result"] = extract_text(m.content)
                    tool_calls_info.append(entry)

        st.markdown(reply)
        if tool_calls_info and show_tool_calls:
            render_tool_console(tool_calls_info)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "tool_calls": tool_calls_info}
    )