# app.py
import streamlit as st
import json
import os
import re
import base64
import time
from typing import Dict, List
from datetime import datetime
from types import SimpleNamespace

# --- Try importing Groq; provide a graceful fallback (mock) if not installed ---
GroqAvailable = True
try:
    from groq import Groq  # type: ignore
except Exception:
    GroqAvailable = False
    Groq = None  # for typing / checks below

# --- Mock Groq client to allow UI testing when the real SDK isn't available ---
class MockGroq:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or "mock-key"
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=self._mock_create
            )
        )

    def _mock_create(self, messages=None, model=None, temperature=None, max_tokens=None):
        user_msg = ""
        if messages:
            for m in messages:
                if m.get("role") == "user":
                    user_msg = m.get("content", "")
                    break

        if "Respond only with valid JSON" in user_msg or "Please provide a response in the following JSON format" in user_msg:
            mock_json = {
                "positive_rephrasing": "Nice work — the logic is solid. We can make this clearer and slightly more efficient by simplifying the loop and improving naming.",
                "the_why": "Combining boolean checks and using idiomatic constructs improves readability and performance for larger lists.",
                "suggested_improvement": "def get_active_users(users):\n    return [user for user in users if user.is_active and user.profile_complete]",
                "resource_link": "https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions"
            }
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(mock_json)))])
        else:
            summary_text = (
                "Great work! You've implemented functional logic and with a few changes (readability, naming, and "
                "idiomatic constructs) the code will be more maintainable and efficient. Keep iterating!"
            )
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=summary_text))])

# --- Use the real Groq if available, otherwise the MockGroq ---
GroqClientClass = Groq if GroqAvailable else MockGroq

# ------------------- Page config & CSS (improved color scheme) -------------------
st.set_page_config(
    page_title="CodeRev",
    page_icon="CodeRev.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
:root{
    --bg: #0f1724;
    --surface: #0b1220;
    --muted: #94a3b8;
    --text: #e6eef8;
    --accent: #5eead4;
    --accent-2: #7c3aed;
    --accent-grad: linear-gradient(90deg, #06b6d4 0%, #7c3aed 100%);
    --code-bg: #071126;
    --card-border: rgba(255,255,255,0.04);
}

/* Page background */
body, .stApp {
    background: var(--bg);
    color: var(--text);
}

/* Header */
.main-header {
    background: var(--accent-grad);
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    text-align: center;
    color: white;
    box-shadow: 0 6px 18px rgba(12,16,26,0.6);
}

/* Sidebar info */
.sidebar-info {
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    border: 1px solid var(--card-border);
    color: var(--text);
}

/* Feature card */
.feature-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.015), rgba(255,255,255,0.01));
    padding: 1rem;
    border-radius: 12px;
    border-left: 4px solid rgba(255,255,255,0.04);
    margin: 1rem 0;
}

/* Metric card */
.metric-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid var(--card-border);
    box-shadow: 0 4px 12px rgba(2,6,23,0.6);
    text-align: center;
    color: var(--text);
}

/* Buttons */
.stButton>button {
    background: var(--accent);
    color: #022;
    border-radius: 10px;
    padding: 8px 12px;
    font-weight: 600;
    border: none;
}
.stButton>button:hover {
    background: var(--accent-2);
    color: white;
}

/* Code block style */
.stCodeBlock, pre {
    background: var(--code-bg) !important;
    color: var(--text) !important;
    border-radius: 8px;
    padding: 12px !important;
    border: 1px solid rgba(255,255,255,0.04) !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", monospace;
}

/* small helper badges */
.badge {
    display:inline-block;
    padding: 4px 8px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    color: #022;
    background: var(--accent);
    margin-right:6px;
}
.rubric-weight {
    background: rgba(255,255,255,0.02);
    padding:6px 8px;
    border-radius:6px;
    display:inline-block;
    margin-right:6px;
    color:var(--muted);
}

a {
    color: var(--accent-2);
    font-weight:600;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------- Main App Logic -------------------
class EmpatheticCodeReviewer:
    def __init__(self, groq_api_key: str):
        if GroqAvailable and Groq is not None:
            try:
                self.client = Groq(api_key=groq_api_key)
            except Exception:
                self.client = MockGroq(groq_api_key)
        else:
            self.client = MockGroq(groq_api_key)
        self.model = "llama3-8b-8192"

    def analyze_comment_severity(self, comment: str) -> str:
        harsh_indicators = ["bad", "wrong", "terrible", "awful", "stupid", "inefficient", "don't", "never", "horrible"]
        neutral_indicators = ["consider", "might", "could", "suggest", "perhaps"]
        comment_lower = comment.lower()
        harsh_count = sum(1 for indicator in harsh_indicators if indicator in comment_lower)
        neutral_count = sum(1 for indicator in neutral_indicators if indicator in comment_lower)
        if harsh_count > 0:
            return "harsh"
        elif neutral_count > 0:
            return "neutral"
        else:
            return "constructive"

    def get_language_from_code(self, code_snippet: str) -> str:
        language_patterns = {
            "python": [r"def\s+\w+\s*\(", r"import\s+\w+", r"from\s+\w+\s+import", r":\s*$"],
            "javascript": [r"function\s+\w+\s*\(", r"=>\s*{", r"var\s+\w+", r"let\s+\w+", r"const\s+\w+"],
            "java": [r"public\s+class", r"private\s+\w+", r"public\s+static\s+void\s+main"],
            "cpp": [r"#include\s*<", r"int\s+main\s*\(", r"std::", r"cout\s*<<"],
            "c": [r"#include\s*<", r"int\s+main\s*\(", r"printf\s*\("],
            "go": [r"func\s+\w+\s*\(", r"package\s+\w+", r"import\s*\("],
            "rust": [r"fn\s+\w+\s*\(", r"use\s+\w+", r"let\s+mut"],
            "php": [r"<\?php", r"function\s+\w+\s*\(", r"\$\w+"],
        }
        for lang, patterns in language_patterns.items():
            if any(re.search(pattern, code_snippet, re.MULTILINE) for pattern in patterns):
                return lang
        return "python"

    def generate_empathetic_feedback(self, code_snippet: str, original_comment: str, language: str, severity: str) -> Dict[str, str]:
        tone_instruction = {
            "harsh": "extra gentle and encouraging, as the original comment was quite direct and potentially discouraging",
            "neutral": "supportive and educational with a collaborative tone",
            "constructive": "warm, collaborative, and appreciative of the existing effort"
        }[severity]

        resource_examples = {
            "python": "Python documentation (docs.python.org), PEP 8 style guide",
            "javascript": "MDN Web Docs, JavaScript.info, ECMAScript specifications",
            "java": "Oracle Java documentation, Java Code Conventions",
            "cpp": "cppreference.com, ISO C++ guidelines",
            "c": "C standard documentation, K&R C book references",
            "go": "Go documentation (golang.org), Effective Go",
            "rust": "The Rust Book, Rust by Example",
            "php": "PHP Manual, PSR standards"
        }

        # sanitize code snippet so triple-backticks inside it won't break the prompt formatting
        safe_code = code_snippet.replace("```", "`\u200b``")

        # Double braces {{ }} produce literal braces in the f-string. The inner {resource_examples...} is evaluated.
        prompt = f"""
You are an experienced senior developer and mentor who excels at giving constructive, empathetic code reviews. Your goal is to transform direct criticism into supportive, educational guidance.

**Code Snippet ({language}):**
```{language}
{safe_code}
```

**Original Comment:** "{original_comment}"

Please provide a response in the following JSON format:
{{
    "positive_rephrasing": "A gentle, encouraging version of the feedback that maintains technical accuracy but uses supportive language",
    "the_why": "A clear explanation of the underlying software engineering principle, performance concern, or best practice",
    "suggested_improvement": "A concrete code example showing the recommended fix",
    "resource_link": "A real, helpful documentation link or resource relevant to {resource_examples.get(language, 'relevant documentation')}"
}}

**Important Guidelines:**
- Be {tone_instruction}
- Focus on growth and learning opportunities
- Explain the reasoning behind best practices
- Provide specific, actionable improvements
- Use collaborative language ("we", "let's") when appropriate
- Acknowledge what's working well before suggesting improvements
- Make sure the code example is syntactically correct and directly addresses the issue
- Keep explanations concise but comprehensive

Respond only with valid JSON.
"""

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer and mentor. Always respond with valid JSON containing the requested fields."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.25,
                max_tokens=900
            )
            response_text = response.choices[0].message.content.strip()

            # Remove surrounding code fences or ```json fences
            if response_text.startswith('```json'):
                response_text = response_text[len('```json'):].strip()
                if response_text.endswith('```'):
                    response_text = response_text[:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:].strip()
                if response_text.endswith('```'):
                    response_text = response_text[:-3].strip()

            # Extract first {...} block (robust heuristic)
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            json_text = response_text
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_text = response_text[first_brace:last_brace + 1]

            return json.loads(json_text)

        except json.JSONDecodeError as e:
            st.error(f"JSON parsing error: {e}. Returning safe fallback.")
            return {
                "positive_rephrasing": "Let's explore how we can enhance this aspect of the code together.",
                "the_why": "This improvement follows software engineering best practices for maintainable and readable code.",
                "suggested_improvement": "// Example improvement (language-dependent) would go here",
                "resource_link": "https://docs.python.org/3/tutorial/" if language == "python" else "https://developer.mozilla.org/"
            }
        except Exception as e:
            st.error(f"API call error: {e}")
            return {
                "positive_rephrasing": "There's a great opportunity to enhance this code.",
                "the_why": "Following established patterns improves code quality and maintainability.",
                "suggested_improvement": f"// Code improvement example for {language}",
                "resource_link": "https://docs.python.org/3/tutorial/" if language == "python" else "https://developer.mozilla.org/"
            }

    def generate_holistic_summary(self, code_snippet: str, all_feedback: List[Dict], language: str) -> str:
        prompt = f"""
Based on the code review feedback provided for this {language} code snippet, write an encouraging and supportive concluding paragraph that:

1. Acknowledges the developer's effort and current implementation
2. Highlights the main themes from the feedback (e.g., performance, readability, conventions)
3. Frames the suggestions as opportunities for growth
4. Maintains an encouraging, mentor-like tone
5. Ends with motivation for continued learning

**Code Snippet:**
```{language}
{code_snippet}
```

**Number of feedback items:** {len(all_feedback)}

Write a warm, encouraging paragraph (3-5 sentences) that would make a developer feel supported and motivated to implement the suggestions.
"""
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a supportive senior developer providing encouraging feedback. Write in a warm, mentoring tone."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.4,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error generating summary: {e}")
            return "Great work on this implementation! The feedback above provides some excellent opportunities to enhance your code's performance, readability, and adherence to best practices. Keep iterating and learning!"

# ------------------- Helper: Download link -------------------
def create_download_link(content: str, filename: str, link_text: str) -> str:
    b64 = base64.b64encode(content.encode()).decode()
    return f'<a href="data:file/markdown;base64,{b64}" download="{filename}" class="download-link">{link_text}</a>'

# ------------------- Sidebar Rubric & Config -------------------
with st.sidebar:
#     st.markdown("<div class='sidebar-info'><h3 class='badge'>Mission 1</h3><strong>Empathetic Code Reviewer</strong></div>", unsafe_allow_html=True)
#     st.markdown("## 🧭 Hackathon Rubric (Quick View)")
#     st.markdown("<div class='rubric-weight'>Functionality & Correctness — 25%</div><div class='rubric-weight'>AI Output & Prompting — 45%</div><div class='rubric-weight'>Code Quality — 20%</div><div class='rubric-weight'>Innovation — 10%</div>", unsafe_allow_html=True)
#     st.markdown("---")
#     st.markdown("## 📋 Detailed Scoring Rubric")
#     st.markdown("""
# - **Functionality & Correctness (25 pts)**: Does the app run and produce the requested Markdown output?
# - **Quality of AI Output & Prompt Engineering (45 pts)**: Depth, nuance, and usefulness of AI-generated feedback.
# - **Code Quality & Documentation (20 pts)**: Readability, structure, and runnable instructions.
# - **Innovation & Stand Out Features (10 pts)**: Extra features (tone toggles, rubric integration, offline mock mode).
# """)
#     st.markdown("---")
    st.markdown("## ⚙️ Configuration")
    api_key = st.text_input("🔑 Groq API Key", type="password", placeholder="Paste your Groq API key here")
    if not GroqAvailable:
        st.warning("`groq` SDK not found in this environment. The app is running in **demo/mock** mode. Install the `groq` package and add your API key for real model responses.")
    st.markdown("---")
    if st.button("📝 Load Sample Data", use_container_width=True):
        st.session_state.sample_loaded = True

# ------------------- Main UI -------------------
def main():
    # -- Splash screen: show logo for first 3 seconds on initial load --
    if not st.session_state.get('splash_shown', False):
        splash_container = st.empty()
        with splash_container.container():
            cols = st.columns([1, 3, 1])
            with cols[1]:
                # Prefer a local file named `CodeRev.png` at repo root; fallback to a hosted placeholder
                logo_path = "CodeRev.png"
                if os.path.exists(logo_path):
                    st.image(logo_path, width=420)
                else:
                    st.image("https://placehold.co/800x240?text=CodeRev+Demo", width=420)

                st.markdown("<h3 style='text-align:center;color:var(--text)'>Welcome to CodeRev</h3>", unsafe_allow_html=True)

        # keep splash visible for 3 seconds, then set flag and rerun to render main UI
        time.sleep(3)
        st.session_state['splash_shown'] = True
        splash_container.empty()
        st.experimental_rerun()

    # Main header
    st.markdown("""
    <div class="main-header">
        <h1> CodeRev</h1>
        <p><strong>Transforming Critical Feedback into Constructive Growth</strong></p>
        <p style="opacity:0.9;">Turn blunt comments into supportive, educational guidance using generative AI.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("## 💻 Code Input")
        language_options = ["Auto-detect", "Python", "JavaScript", "Java", "C++", "C", "Go", "Rust", "PHP"]
        selected_language = st.selectbox("Programming Language", language_options)

        sample_code = ""
        if st.session_state.get('sample_loaded', False):
            sample_code = """def get_active_users(users):
    results = []
    for u in users:
        if u.is_active == True and u.profile_complete == True:
            results.append(u)
    return results"""

        code_snippet = st.text_area("Code Snippet", value=sample_code, height=220, placeholder="Paste your code here...")

        st.markdown("## 📝 Review Comments")
        sample_comments = []
        if st.session_state.get('sample_loaded', False):
            sample_comments = [
                "This is inefficient. Don't loop twice conceptually.",
                "Variable 'u' is a bad name.",
                "Boolean comparison '== True' is redundant."
            ]
        if 'num_comments' not in st.session_state:
            st.session_state.num_comments = len(sample_comments) if sample_comments else 3
        num_comments = st.number_input("Number of Comments", min_value=1, max_value=10, value=st.session_state.num_comments)
        st.session_state.num_comments = num_comments

        comments = []
        for i in range(num_comments):
            default_comment = sample_comments[i] if i < len(sample_comments) else ""
            comment = st.text_input(f"Comment {i+1}", value=default_comment, key=f"comment_{i}")
            if comment and comment.strip():
                comments.append(comment.strip())

    with col2:
        st.markdown("## 🎯 Analysis & Results")
        if not api_key:
            st.info("⚠️ For live model responses, enter your Groq API key in the sidebar. Demo mode uses a mock client.")
        if not code_snippet.strip():
            st.info("📝 Paste a code snippet to analyze.")
        elif not comments:
            st.info("💬 Add at least one review comment.")
        else:
            if st.button("🚀 Generate Empathetic Review", type="primary", use_container_width=True):
                try:
                    with st.spinner("🤖 Generating empathetic feedback..."):
                        reviewer = EmpatheticCodeReviewer(api_key or "")
                        detected_language = reviewer.get_language_from_code(code_snippet) if selected_language == "Auto-detect" else selected_language.lower()
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        all_feedback = []
                        total_comments = len(comments)
                        for i, comment in enumerate(comments):
                            status_text.text(f"Processing comment {i+1}/{total_comments}...")
                            severity = reviewer.analyze_comment_severity(comment)
                            feedback = reviewer.generate_empathetic_feedback(code_snippet, comment, detected_language, severity)
                            all_feedback.append(feedback)
                            progress_bar.progress((i + 1) / (total_comments + 1))

            st.markdown("---")
            st.markdown("## 📊 Empathetic Review Report")
            if 'results' in st.session_state:
                results = st.session_state.results

                # Metric cards
                mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                with mcol1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>🔍 Language</h4>
                        <div style="font-weight:700; font-size:18px;">{results['language'].title()}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mcol2:
                    harsh_comments = sum(1 for comment in results['comments'] if EmpatheticCodeReviewer("").analyze_comment_severity(comment) == "harsh")
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>⚠️ Harsh</h4>
                        <div style="font-weight:700; font-size:18px;">{harsh_comments}</div>
                        <div style="color:var(--muted); font-size:12px;">Detected harsh comments</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mcol3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>💬 Comments</h4>
                        <div style="font-weight:700; font-size:18px;">{len(results['comments'])}</div>
                        <div style="color:var(--muted); font-size:12px;">Total comments</div>
                    </div>
                    """, unsafe_allow_html=True)
                with mcol4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>✨ Improvements</h4>
                        <div style="font-weight:700; font-size:18px;">{len(results['feedback'])}</div>
                        <div style="color:var(--muted); font-size:12px;">Suggestions generated</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("### 💻 Original Code")
                st.code(results['code_snippet'], language=results['language'])

                st.markdown("### 🤝 Constructive Feedback")
                for i, (original_comment, feedback) in enumerate(zip(results['comments'], results['feedback']), 1):
                    with st.expander(f"💡 Comment {i}: \"{original_comment[:60]}{'...' if len(original_comment) > 60 else ''}\"", expanded=True):
                        left, right = st.columns([1,1])
                        with left:
                            st.markdown("**🤝 Positive Rephrasing:**")
                            st.info(feedback.get('positive_rephrasing', '—'))
                            st.markdown("**🧠 The 'Why':**")
                            st.write(feedback.get('the_why', '—'))
                        with right:
                            st.markdown("**🔧 Suggested Improvement:**")
                            st.code(feedback.get('suggested_improvement', ''), language=results['language'])
                            st.markdown("**📚 Learn More:**")
                            resource = feedback.get('resource_link', '')
                            if isinstance(resource, str) and resource.startswith('http'):
                                st.markdown(f"[📖 Documentation Link]({resource})")
                            else:
                                st.write(resource)

                st.markdown("### 🎉 Summary")
                st.success(results['summary'])

                # Download
                st.markdown("### 📥 Download Report")
                markdown_content = f"# 🌟 Empathetic Code Review Report\n\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n## Original Code ({results['language'].title()})\n\n```{results['language']}\n{results['code_snippet']}\n```\n\n## Constructive Feedback\n\n"
                for i, (original_comment, feedback) in enumerate(zip(results['comments'], results['feedback']), 1):
                    markdown_content += f"### 💡 Analysis of Comment {i}: \"{original_comment}\"\n\n**🤝 Positive Rephrasing:** {feedback.get('positive_rephrasing','')}\n\n**🧠 The 'Why':** {feedback.get('the_why','')}\n\n**🔧 Suggested Improvement:**\n```{results['language']}\n{feedback.get('suggested_improvement','')}\n```\n\n**📚 Learn More:** [{feedback.get('resource_link','')}]\n\n---\n\n"
                markdown_content += f"## 🎉 Summary\n\n{results['summary']}\n\n*Happy coding! 🚀*\n"
                filename = f"empathetic_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                st.download_button(label="📄 Download Markdown Report", data=markdown_content, file_name=filename, mime="text/markdown", use_container_width=True)

                # --- Rubric scoring widget (helps you demonstrate scoring & innovation) ---
                st.markdown("---")
                # st.markdown("## 🧮 Self-Evaluation (Demo judge panel)")
                # st.markdown commented out for now

if __name__ == "__main__":
    if 'sample_loaded' not in st.session_state:
        st.session_state.sample_loaded = False
    # initialize splash flag (so splash shows only once per user session)
    if 'splash_shown' not in st.session_state:
        st.session_state.splash_shown = False
    main()
