# 🌟 CodeRev

**Web app:** [CodeRev](https://coderev.streamlit.app/#code-rev)

A Streamlit app that converts direct, critical review comments into empathetic, constructive, and educational feedback using a generative AI model (Groq by default). Includes a demo/mock mode so UI and workflows can be tested even when the `groq` SDK or an API key is not available.

---

## Features

* Accepts a code snippet and a list of raw review comments.
* Uses an LLM (via Groq) to generate for each comment:

  * **Positive Rephrasing** (empathetic tone)
  * **The 'Why'** (clear engineering rationale)
  * **Suggested Improvement** (concrete code example)
  * **Resource Link** (relevant documentation)
* Detects comment severity (harsh / neutral / constructive) and adapts tone.
* Auto language detection (or manual selection).
* Downloadable Markdown report.
* Hackathon scoring rubric panel and a demo self-evaluation widget.
* Mock Groq client when `groq` SDK or API key is missing (safe demo mode).

---

## Quickstart (Local)

1. **Clone the repo**

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

2. **Create & activate a virtual environment** (recommended)

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

3. **Install dependencies**

Create a `requirements.txt` (example below) and then:

```bash
pip install -r requirements.txt
```

**Example `requirements.txt`:**

```
streamlit
groq
```

> If you don’t install `groq`, the app will run in **demo/mock** mode using a built-in mock client.

4. **Run the app**

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

---

## Deployment (Streamlit Cloud)

1. Add your project to a GitHub repo (include `app.py` and `requirements.txt`).
2. In Streamlit Cloud, choose **New app** → select the repo and branch, point to `app.py`.
3. Deploy. If you want live Groq responses, add your Groq API key in the app sidebar after deployment.

**Hosted demo:** [https://coderev.streamlit.app/#code-rev](https://coderev.streamlit.app/#code-rev)

---

## Configuration & Usage

* **Groq API key:** Optional for local demo. For real LLM outputs, generate a Groq API key from the Groq Console and paste it into the sidebar input labeled "🔑 Groq API Key (optional for demo)".
* **Sample data:** Click **Load Sample Data** in the sidebar to populate the sample code and comments used in the hackathon prompt.
* **Generate Review:** Paste your code and comments, then press **Generate Empathetic Review**.

---

## Example Input (JSON)

This is the input required by the hackathon specification (the app UI accepts the same fields):

```json
{
  "code_snippet": "def get_active_users(users):\n    results = []\n    for u in users:\n        if u.is_active == True and u.profile_complete == True:\n            results.append(u)\n    return results",
  "review_comments": [
    "This is inefficient. Don't loop twice conceptually.",
    "Variable 'u' is a bad name.",
    "Boolean comparison '== True' is redundant."
  ]
}
```

---

## Notes & Troubleshooting

* **`ModuleNotFoundError: No module named 'groq'`** — add `groq` to `requirements.txt` and redeploy, or run in demo mode (no Groq required).
* **Model responses are invalid JSON** — the app strips common markdown fences and heuristically extracts the first `{...}` block. If the model returns malformed JSON, a safe fallback is used.
* **Local testing** — the app includes a `MockGroq` client which returns sensible placeholder responses so you can preview the full UI without an API key.

---

## Extending the App (ideas to stand out)

* Add a tone slider to let the reviewer control how gentle or blunt the rephrase should be.
* Save historical reviews (Git-backed or DB) and show improvement over time.
* Add multi-language support and more precise language detection.
* Build a CI integration that automatically converts harsh PR comments into empathetic suggestions.

---

## License

MIT License — feel free to reuse and adapt.

---

## Author

Created by the project contributor.

If you want any changes to the README (add badges, contributor list, or a demo GIF), tell me what to include and I'll update it in the canvas.
