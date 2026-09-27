# Final Report: AI-Powered HR Policy Assistant

## 1. Objective and scope

This project implements a conversational interface for finding information in the HR policy PDFs stored in `HR_policy_pdf/`. The application is designed to return answers grounded in retrieved document passages, cite their source PDF and page, and abstain when the indexed material does not support an answer.

The current source is `the_nestle_hr_policy_pdf_2012.pdf`. Its filename indicates that it is from 2012; this implementation does not verify that the policy is current, complete, or approved. A separate project-assignment PDF at the workspace root is intentionally excluded from policy ingestion.

## 2. Programming environment

The application uses Python, Gradio 6, LangChain integrations, PyPDF, ChromaDB, and python-dotenv. The active implementation environment was Python 3.13.5. Runtime requirements are listed in `requirements.txt`; pytest is isolated in `requirements-dev.txt`.

Create and activate a virtual environment, install dependencies, and create local configuration from the template:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The default `LLM_PROVIDER=auto` selects OpenAI when `OPENAI_API_KEY` is present and otherwise falls back to Ollama, with the selected provider and fallback notice shown in the interface. Explicit `LLM_PROVIDER=openai` without a key also falls back to Ollama; explicit `LLM_PROVIDER=ollama` remains local regardless of whether an OpenAI key exists. The OpenAI defaults are `gpt-3.5-turbo` for chat and `text-embedding-3-small` for embeddings. Ollama defaults to `qwen:latest` for chat and `nomic-embed-text` for embeddings; both must be pulled into a running local Ollama service. Provider, model, paths, chunk dimensions, and retrieval thresholds are configurable through environment variables.

## 3. PDF processing

`load_policy_documents` scans top-level `*.pdf` files in `HR_policy_pdf/` and loads each using LangChain's `PyPDFLoader`. Empty pages are discarded. The application retains each page's source filename and zero-based page metadata for traceability. A malformed PDF is reported as a skipped file; indexing stops with a useful error if no readable text remains.

The actual source was parsed successfully during the implementation check: **7 text-bearing pages** were extracted with **no skipped-page/file warnings**. This pipeline reads embedded PDF text. It does not perform OCR, so scanned pages must be OCR-processed before indexing.

## 4. Chunking and vector representations

`RecursiveCharacterTextSplitter` divides page documents into chunks of 1,000 characters with 150 characters of overlap by default. It prefers paragraph, line, sentence, and word boundaries while preserving source and page metadata. These settings are configurable with `CHUNK_SIZE` and `CHUNK_OVERLAP`.

The tested policy produced **20 chunks** with the default settings. In OpenAI mode, each chunk is embedded with the configured OpenAI embedding model; in Ollama mode, it uses the configured local Ollama embedding model. Chroma stores the vectors and metadata using cosine similarity. Separate generated storage directories are selected per provider and embedding model so vectors of incompatible dimensions are not mixed. Rebuilding replaces only the generated index for the selected provider/model.

## 5. Question-answering workflow

For a user question, the application:

1. Loads the matching Chroma index or builds it from the policy folder if absent.
2. Retrieves up to four similar chunks by default and filters results using `MIN_RELEVANCE_SCORE` (default 0.15).
3. Supplies the question and retrieved excerpts to the configured chat model. The prompt requires evidence-based answers, treats document text and conversation history as untrusted reference data, and directs the assistant to abstain rather than guess when excerpts do not answer the question.
4. Displays citations using the PDF filename and one-based page number. Duplicate citations to the same page are collapsed.

If no retrieved passage passes the configured threshold, the assistant returns a fixed abstention response and asks the user to confirm with HR. Retrieval thresholds are deployment-dependent and should be evaluated against representative, approved HR questions; the default is not a formal accuracy guarantee.

## 6. Gradio interface

Run `python app.py` to launch the local Gradio interface at `http://127.0.0.1:7860`. It provides a conversational question box, responses with source citations, a policy/index status area, and a **Rebuild policy index** control for changes to the PDFs. The first question triggers indexing if a compatible index is not already available. The interface warns users to avoid entering personal employee data and to confirm case-specific decisions with HR.

## 7. Testing and verification

The focused pytest suite contains eight checks covering:

- Text extraction and page/source metadata from the actual HR policy PDF.
- Chunk length and metadata preservation.
- Deduplicated citations with correct one-based page labels.
- Grounded-response citation and low-relevance abstention behavior using a mocked model/store.
- Rejection of an unsupported provider configuration.
- Automatic OpenAI selection when a key exists, Ollama fallback when it does not, and preservation of an explicit Ollama selection.
- Ollama chat settings that disable extended reasoning and cap generated output.

Verification completed in the implementation environment:

- `python -m py_compile app.py tests/test_app.py`: passed.
- `python -m pytest -q`: **8 passed**.
- PDF/Gradio smoke check: **7 text-bearing pages, 20 chunks, 0 extraction warnings**, and successful Gradio Blocks construction.
- Live Ollama check: successfully embedded and indexed all 20 chunks and answered a policy-purpose question with citations to pages 3, 5, and 7.

The test suite mocks generation and retrieval for deterministic behavior; it does not verify live OpenAI credentials or model availability. In the current runtime no OpenAI key was found, and the UI confirmed that Ollama was selected. A live local Ollama embedding and generation request was verified separately.

## 8. Privacy, security, and deployment limitations

The app binds to localhost by default and does not create a public share URL. Local binding is not a substitute for organizational approval or access controls. The prototype does not provide authentication, role-based authorization, audit logging, or a managed retention/deletion workflow.

OpenAI mode transmits document chunks for embedding and retrieved excerpts plus the question for generation to the configured OpenAI service. Confirm vendor, data-processing, retention, and confidentiality requirements before using company materials. Ollama can keep inference local when hosted locally, but access to the host, model service, PDF files, and Chroma data still requires protection. Generated vector indexes are stored locally under `.chroma/`; secrets and those indexes are excluded from version control.

Before operational use, Nestlé HR, legal, privacy, and security stakeholders should verify that the 2012-named source is current and approved, review representative answer quality and abstention behavior, and define authentication, authorization, logging, retention, monitoring, and escalation controls. The chatbot must not be used as the final authority for employee-specific decisions.