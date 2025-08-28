import streamlit as st
import json
import os
from typing import Dict, List
from groq import Groq
import re
from datetime import datetime
import base64

# Page configuration
st.set_page_config(
    page_title="🌟 Empathetic Code Reviewer",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .code-input {
        background: #2d3748;
        color: #e2e8f0;
        border-radius: 8px;
        border: 1px solid #4a5568;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    .sidebar-info {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class EmpatheticCodeReviewer:
    def __init__(self, groq_api_key: str):
        """Initialize the Empathetic Code Reviewer with Groq API key."""
        self.client = Groq(api_key=groq_api_key)
        self.model = "llama3-8b-8192"
        
    def analyze_comment_severity(self, comment: str) -> str:
        """Analyze the severity/tone of a comment to adjust response style."""
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
        """Detect programming language from code snippet."""
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
        
        code_lower = code_snippet.lower()
        
        for lang, patterns in language_patterns.items():
            if any(re.search(pattern, code_snippet, re.MULTILINE) for pattern in patterns):
                return lang
        
        return "python"  # Default fallback
    
    def generate_empathetic_feedback(self, code_snippet: str, original_comment: str, language: str, severity: str) -> Dict[str, str]:
        """Generate empathetic feedback for a single comment using Groq API."""
        
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
        
        prompt = f"""
You are an experienced senior developer and mentor who excels at giving constructive, empathetic code reviews. Your goal is to transform direct criticism into supportive, educational guidance.

**Code Snippet ({language}):**
```{language}
{code_snippet}
```

**Original Comment:** "{original_comment}"

Please provide a response in the following JSON format:
{{
    "positive_rephrasing": "A gentle, encouraging version of the feedback that maintains technical accuracy but uses supportive language",
    "the_why": "A clear explanation of the underlying software engineering principle, performance concern, or best practice",
    "suggested_improvement": "A concrete code example showing the recommended fix",
    "resource_link": "A real, helpful documentation link or resource relevant to {language} (like {resource_examples.get(language, 'relevant documentation')})"
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
                    {
                        "role": "system",
                        "content": "You are an expert code reviewer and mentor. Always respond with valid JSON containing the requested fields."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure it's valid JSON
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            st.error(f"JSON parsing error: {e}")
            return {
                "positive_rephrasing": f"Let's explore how we can enhance this aspect of the code together.",
                "the_why": "This improvement follows software engineering best practices for maintainable and readable code.",
                "suggested_improvement": f"// Enhanced {language} code example would be provided here",
                "resource_link": f"https://docs.python.org/3/tutorial/" if language == "python" else f"https://developer.mozilla.org/"
            }
        except Exception as e:
            st.error(f"API call error: {e}")
            return {
                "positive_rephrasing": f"There's a great opportunity to enhance this code.",
                "the_why": "Following established patterns improves code quality and maintainability.",
                "suggested_improvement": f"// Code improvement example for {language}",
                "resource_link": f"https://docs.python.org/3/tutorial/" if language == "python" else f"https://developer.mozilla.org/"
            }
    
    def generate_holistic_summary(self, code_snippet: str, all_feedback: List[Dict], language: str) -> str:
        """Generate an encouraging summary of all the feedback."""
        
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
                    {
                        "role": "system",
                        "content": "You are a supportive senior developer providing encouraging feedback. Write in a warm, mentoring tone."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.4,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            st.error(f"Error generating summary: {e}")
            return "Great work on this implementation! The feedback above provides some excellent opportunities to enhance your code's performance, readability, and adherence to best practices. These kinds of improvements are part of every developer's journey, and implementing them will make you a stronger programmer. Keep up the excellent work and continue learning!"

def create_download_link(content: str, filename: str, link_text: str) -> str:
    """Create a download link for the markdown content."""
    b64 = base64.b64encode(content.encode()).decode()
    return f'<a href="data:file/markdown;base64,{b64}" download="{filename}" class="download-link">{link_text}</a>'

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌟 Empathetic Code Reviewer</h1>
        <p><strong>Transforming Critical Feedback into Constructive Growth</strong></p>
        <p>Turn harsh code review comments into supportive, educational guidance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "🔑 Groq API Key",
            type="password",
            placeholder="Enter your Groq API key",
            help="Get your API key from https://console.groq.com/"
        )
        
        if not api_key:
            st.markdown("""
            <div class="sidebar-info">
                <h4>🚀 Getting Started:</h4>
                <ol>
                    <li>Visit <a href="https://console.groq.com/" target="_blank">Groq Console</a></li>
                    <li>Create an account</li>
                    <li>Generate an API key</li>
                    <li>Paste it above</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Features info
        st.markdown("## ✨ Features")
        features = [
            "🎯 **Context Aware**: Adjusts tone based on comment severity",
            "🧠 **Educational**: Explains the 'why' behind suggestions",
            "🔧 **Practical**: Provides concrete code examples",
            "📚 **Resourceful**: Links to relevant documentation",
            "🤝 **Empathetic**: Transforms harsh feedback into supportive guidance"
        ]
        
        for feature in features:
            st.markdown(feature)
        
        st.markdown("---")
        
        # Sample data button
        if st.button("📝 Load Sample Data", use_container_width=True):
            st.session_state.sample_loaded = True
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("## 💻 Code Input")
        
        # Language selection
        language_options = ["Auto-detect", "Python", "JavaScript", "Java", "C++", "C", "Go", "Rust", "PHP"]
        selected_language = st.selectbox("Programming Language", language_options)
        
        # Code snippet input
        sample_code = ""
        if st.session_state.get('sample_loaded', False):
            sample_code = """def get_active_users(users):
    results = []
    for u in users:
        if u.is_active == True and u.profile_complete == True:
            results.append(u)
    return results"""
        
        code_snippet = st.text_area(
            "Code Snippet",
            value=sample_code,
            height=200,
            placeholder="Paste your code here...",
            help="Enter the code that needs review"
        )
        
        st.markdown("## 📝 Review Comments")
        
        # Comments input
        sample_comments = []
        if st.session_state.get('sample_loaded', False):
            sample_comments = [
                "This is inefficient. Don't loop twice conceptually.",
                "Variable 'u' is a bad name.",
                "Boolean comparison '== True' is redundant."
            ]
        
        # Dynamic comment inputs
        if 'num_comments' not in st.session_state:
            st.session_state.num_comments = len(sample_comments) if sample_comments else 3
        
        num_comments = st.number_input(
            "Number of Comments",
            min_value=1,
            max_value=10,
            value=st.session_state.num_comments
        )
        
        st.session_state.num_comments = num_comments
        
        comments = []
        for i in range(num_comments):
            default_comment = sample_comments[i] if i < len(sample_comments) else ""
            comment = st.text_input(
                f"Comment {i+1}",
                value=default_comment,
                placeholder=f"Enter review comment {i+1}...",
                key=f"comment_{i}"
            )
            if comment.strip():
                comments.append(comment.strip())
    
    with col2:
        st.markdown("## 🎯 Analysis & Results")
        
        if not api_key:
            st.warning("⚠️ Please enter your Groq API key in the sidebar to continue.")
        elif not code_snippet.strip():
            st.info("📝 Please enter a code snippet to analyze.")
        elif not comments:
            st.info("💬 Please enter at least one review comment.")
        else:
            # Process button
            if st.button("🚀 Generate Empathetic Review", type="primary", use_container_width=True):
                try:
                    with st.spinner("🤖 Analyzing and generating empathetic feedback..."):
                        # Initialize reviewer
                        reviewer = EmpatheticCodeReviewer(api_key)
                        
                        # Detect language if auto-detect is selected
                        if selected_language == "Auto-detect":
                            detected_language = reviewer.get_language_from_code(code_snippet)
                        else:
                            detected_language = selected_language.lower()
                        
                        # Progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Generate feedback for each comment
                        all_feedback = []
                        total_comments = len(comments)
                        
                        for i, comment in enumerate(comments):
                            status_text.text(f"Processing comment {i+1}/{total_comments}...")
                            severity = reviewer.analyze_comment_severity(comment)
                            feedback = reviewer.generate_empathetic_feedback(
                                code_snippet, comment, detected_language, severity
                            )
                            all_feedback.append(feedback)
                            progress_bar.progress((i + 1) / (total_comments + 1))
                        
                        # Generate summary
                        status_text.text("Generating holistic summary...")
                        summary = reviewer.generate_holistic_summary(code_snippet, all_feedback, detected_language)
                        progress_bar.progress(1.0)
                        status_text.text("✅ Analysis complete!")
                        
                        # Store results in session state
                        st.session_state.results = {
                            'code_snippet': code_snippet,
                            'language': detected_language,
                            'comments': comments,
                            'feedback': all_feedback,
                            'summary': summary
                        }
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Results display
    if 'results' in st.session_state:
        st.markdown("---")
        st.markdown("## 📊 Empathetic Review Report")
        
        results = st.session_state.results
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🔍</h3>
                <p><strong>Language</strong></p>
                <p>{}</p>
            </div>
            """.format(results['language'].title()), unsafe_allow_html=True)
        
        with col2:
            harsh_comments = sum(1 for comment in results['comments'] 
                               if EmpatheticCodeReviewer("").analyze_comment_severity(comment) == "harsh")
            st.markdown("""
            <div class="metric-card">
                <h3>⚠️</h3>
                <p><strong>Harsh Comments</strong></p>
                <p>{}</p>
            </div>
            """.format(harsh_comments), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>💬</h3>
                <p><strong>Total Comments</strong></p>
                <p>{}</p>
            </div>
            """.format(len(results['comments'])), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>✨</h3>
                <p><strong>Improvements</strong></p>
                <p>{}</p>
            </div>
            """.format(len(results['feedback'])), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Original code display
        st.markdown("### 💻 Original Code")
        st.code(results['code_snippet'], language=results['language'])
        
        # Feedback sections
        st.markdown("### 🤝 Constructive Feedback")
        
        for i, (original_comment, feedback) in enumerate(zip(results['comments'], results['feedback']), 1):
            with st.expander(f"💡 Comment {i}: \"{original_comment[:50]}{'...' if len(original_comment) > 50 else ''}\"", expanded=True):
                
                col_left, col_right = st.columns([1, 1])
                
                with col_left:
                    st.markdown("**🤝 Positive Rephrasing:**")
                    st.info(feedback['positive_rephrasing'])
                    
                    st.markdown("**🧠 The 'Why':**")
                    st.write(feedback['the_why'])
                
                with col_right:
                    st.markdown("**🔧 Suggested Improvement:**")
                    st.code(feedback['suggested_improvement'], language=results['language'])
                    
                    st.markdown("**📚 Learn More:**")
                    if feedback['resource_link'].startswith('http'):
                        st.markdown(f"[📖 Documentation Link]({feedback['resource_link']})")
                    else:
                        st.write(feedback['resource_link'])
        
        # Summary
        st.markdown("### 🎉 Summary")
        st.success(results['summary'])
        
        # Generate and offer download
        st.markdown("### 📥 Download Report")
        
        # Create markdown content
        markdown_content = f"""# 🌟 Empathetic Code Review Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Original Code ({results['language'].title()})

```{results['language']}
{results['code_snippet']}
```

## Constructive Feedback

"""
        
        for i, (original_comment, feedback) in enumerate(zip(results['comments'], results['feedback']), 1):
            markdown_content += f"""### 💡 Analysis of Comment {i}: "{original_comment}"

**🤝 Positive Rephrasing:** {feedback['positive_rephrasing']}

**🧠 The 'Why':** {feedback['the_why']}

**🔧 Suggested Improvement:**
```{results['language']}
{feedback['suggested_improvement']}
```

**📚 Learn More:** [{feedback['resource_link']}]({feedback['resource_link']})

---

"""
        
        markdown_content += f"""## 🎉 Summary

{results['summary']}

*Happy coding! 🚀*
"""
        
        # Download button
        filename = f"empathetic_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        st.download_button(
            label="📄 Download Markdown Report",
            data=markdown_content,
            file_name=filename,
            mime="text/markdown",
            use_container_width=True
        )

if __name__ == "__main__":
    # Initialize session state
    if 'sample_loaded' not in st.session_state:
        st.session_state.sample_loaded = False
    
    main()
