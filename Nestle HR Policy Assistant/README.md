# Nestlé HR Policy Assistant

A local Gradio question-answering app for the policy PDFs in `HR_policy_pdf/`. It extracts PDF text with PyPDFLoader, splits it into overlapping chunks, embeds those chunks in Chroma, retrieves relevant passages, and asks a configured language model to answer with page citations.

## Requirements

- Python 3.10 or newer (tested here with Python 3.13)
- An OpenAI API key to use OpenAI, or an installed/running Ollama service with the configured models pulled

## Setup

In PowerShell from this project folder:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The default `LLM_PROVIDER=auto` selects OpenAI when `OPENAI_API_KEY` is set and otherwise falls back to Ollama. To use OpenAI, add an API key to `.env`:

```dotenv
LLM_PROVIDER=auto
OPENAI_API_KEY=your-key
OPENAI_CHAT_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

If no OpenAI key is configured, the app selects Ollama automatically. Install/start Ollama and pull both configured models:

```powershell
ollama pull qwen:latest
ollama pull nomic-embed-text
```

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

Place approved policy PDFs at the top level of `HR_policy_pdf/`. The supplied `the_nestle_hr_policy_pdf_2012.pdf` is loaded automatically; the assignment brief in the project root is not indexed. Scanned/image-only PDFs need OCR before this text-based pipeline can use them.

## Run

```powershell
python app.py
```

Open <http://127.0.0.1:7860>. The first question builds the index if needed. Use **Rebuild policy index** after adding or replacing PDFs. Each embedding provider/model gets a separate local Chroma directory under `.chroma/`; rebuilding replaces only that provider/model's generated index.

Run the tests with:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Configuration

All settings are read from `.env`; see `.env.example`. `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_K`, and `MIN_RELEVANCE_SCORE` adjust text splitting and retrieval. Relative policy/index paths are resolved from the project directory. The app binds to `127.0.0.1` and does not create a public Gradio share link by default.

If `LLM_PROVIDER=openai` is explicitly set but `OPENAI_API_KEY` is absent, the app also falls back to Ollama and displays a notice. An explicit `LLM_PROVIDER=ollama` always selects Ollama, even when an OpenAI key is present. The local Ollama service and configured models must be available for fallback requests to succeed.

The chatbot is informational, not an HR decision-maker. It cites retrieved PDF pages and declines answers when retrieval scores are below the configured threshold. Confirm policy interpretation and individual cases with HR. The bundled policy filename indicates a 2012 document; verify that it is current and approved before relying on it.

## Data handling

The Chroma index and `.env` are excluded from version control. OpenAI mode sends question text and retrieved policy excerpts to the configured OpenAI service for embedding and generation. Ollama can keep inference local when its service and models run locally, but the local host still needs appropriate security. This prototype has no authentication, authorization, audit controls, or production data-retention policy. Do not use it with confidential documents or employee data until approved by the organization's security, privacy, and HR owners.