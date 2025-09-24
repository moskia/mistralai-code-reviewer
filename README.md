# 📦 MistralAI Code Reviewer

An API that fetches a GitHub repository, summarizes its contents, and uses **Mistral AI** to generate a structured **code review**.
Useful for quick project audits, candidate assignment reviews, or just exploring a repo’s quality/security.

[![Tests](https://github.com/yourname/mistralai-code-reviewer/actions/workflows/tests.yml/badge.svg)](https://github.com/yourname/mistralai-code-reviewer/actions/workflows/tests.yml)

---

## ✨ Features

* Fetch repo contents via GitHub **Tree API** (fast, efficient).
* Prefers **application code** over config/docs for analysis.
* Summarizes code into **token-friendly previews**.
* Sends to Mistral AI and returns a **structured JSON review**.
* Truncates large repos with a clear note: `(Note: analysis truncated)`.
* REST API with interactive docs at `/docs`.

---

## ⚙️ Requirements

* Python **3.10+** (if not using Docker)
* A [Mistral API key](https://docs.mistral.ai/)
* (Optional) A GitHub token for higher API rate limits

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
MISTRAL_API_KEY=your_mistral_key_here
MISTRAL_MODEL=mistral-large-latest
# Optional but recommended for higher GitHub API limits
GITHUB_TOKEN=ghp_xxx
```

---

## 🏃 Run with Python (venv)

```bash
# clone repo
git clone https://github.com/yourname/mistralai-code-reviewer.git
cd mistralai-code-reviewer

# create venv
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# run server
uvicorn app.main:app --reload --port 8000
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Example request

```bash
curl -X POST http://127.0.0.1:8000/review \
  -H "Content-Type: application/json" \
  -d '{
        "assignment_description":"Review this project",
        "github_repo_url":"https://github.com/tiangolo/fastapi",
        "candidate_level":"Junior"
      }'
```

---

## 🐳 Run with Docker

### Build the image

```bash
docker build -t mistral-reviewer .
```

### Run the container

```bash
docker run -p 8000:8000 --env-file .env mistral-reviewer
```

Now the API is live at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 🧪 Run Tests

Unit tests use mocks (no real GitHub/Mistral calls).

```bash
pytest -q
```

You can also run the AI service directly with the helper script:

```bash
python test_ai_service.py
```

---

## 📝 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# install deps early for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📌 Known Limitations

* Repos with **>50 files or >0.5 MB** of code are truncated for performance.
* Only the first 80 lines of each file are sent to the model.
* Very large repos (like TensorFlow or VS Code) may miss coverage.
* Output depends on the AI model and may vary.

---

## 🎯 Next Steps

* Add batching for very large repos (process in chunks).
* Add GitHub Actions CI (already provided in `.github/workflows/tests.yml`).
* Optional frontend to paste repo URLs and view results nicely.

