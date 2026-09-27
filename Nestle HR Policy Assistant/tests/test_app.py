from pathlib import Path

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app import (
    ABSTENTION,
    HRPolicyAssistant,
    Settings,
    create_app,
    format_citations,
    load_policy_documents,
    split_policy_documents,
)

BASE_DIR = Path(__file__).resolve().parents[1]
POLICY_DIR = BASE_DIR / "HR_policy_pdf"


def settings_for(tmp_path: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "provider": "openai",
        "policy_dir": POLICY_DIR,
        "vector_store_dir": tmp_path / ".chroma",
        "openai_api_key": "test-key",
        "openai_chat_model": "gpt-3.5-turbo",
        "openai_embedding_model": "text-embedding-3-small",
        "ollama_base_url": "http://localhost:11434",
        "ollama_chat_model": "llama3.1",
        "ollama_embedding_model": "nomic-embed-text",
        "chunk_size": 1000,
        "chunk_overlap": 150,
        "retrieval_k": 4,
        "min_relevance_score": 0.15,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_real_policy_pdf_extracts_text_and_page_metadata() -> None:
    documents, warnings = load_policy_documents(POLICY_DIR)

    assert not warnings
    assert documents
    assert documents[0].page_content.strip()
    assert documents[0].metadata["source"] == "the_nestle_hr_policy_pdf_2012.pdf"
    assert documents[0].metadata["page"] == 0


def test_split_keeps_source_page_and_bounds_chunk_length() -> None:
    source = Document(
        page_content="A policy sentence. " * 20,
        metadata={"source": "policy.pdf", "page": 2},
    )

    chunks = split_policy_documents([source], chunk_size=80, chunk_overlap=10)

    assert len(chunks) > 1
    assert all(len(chunk.page_content) <= 80 for chunk in chunks)
    assert all(chunk.metadata["source"] == "policy.pdf" for chunk in chunks)
    assert all(chunk.metadata["page"] == 2 for chunk in chunks)


def test_citations_are_unique_and_pages_are_one_based() -> None:
    chunks = [
        Document(page_content="One", metadata={"source": "policy.pdf", "page": 0}),
        Document(page_content="Two", metadata={"source": "policy.pdf", "page": 0}),
        Document(page_content="Three", metadata={"source": "policy.pdf", "page": 2}),
    ]

    assert format_citations(chunks) == "- policy.pdf, p. 1\n- policy.pdf, p. 3"


class FakeStore:
    def __init__(self, matches: list[tuple[Document, float]]) -> None:
        self.matches = matches

    def similarity_search_with_relevance_scores(self, question: str, k: int):
        return self.matches[:k]


def test_answer_cites_source_and_abstains_from_low_relevance(tmp_path: Path) -> None:
    assistant = HRPolicyAssistant(settings_for(tmp_path))
    supported_doc = Document(
        page_content="Employees may request leave through the HR portal.",
        metadata={"source": "leave-policy.pdf", "page": 4},
    )
    assistant.vector_store = FakeStore([(supported_doc, 0.8)])  # type: ignore[assignment]
    assistant._get_chat_model = lambda: RunnableLambda(  # type: ignore[method-assign]
        lambda _: AIMessage(content="Employees may request leave through the HR portal.")
    )

    response = assistant.answer("How do employees request leave?")

    assert "Employees may request leave" in response
    assert "leave-policy.pdf, p. 5" in response

    assistant.vector_store = FakeStore([(supported_doc, 0.05)])  # type: ignore[assignment]
    assert assistant.answer("What is the office lunch menu?") == ABSTENTION


def test_settings_reject_unknown_provider(tmp_path: Path) -> None:
    settings = settings_for(tmp_path, provider="other")

    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        settings.validate()


def test_provider_auto_selects_openai_only_when_key_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert Settings.from_env(tmp_path).provider == "openai"

    monkeypatch.delenv("OPENAI_API_KEY")
    settings = Settings.from_env(tmp_path)
    assert settings.provider == "ollama"
    assert "OPENAI_API_KEY was not found" in settings.provider_notice


def test_explicit_openai_without_key_falls_back_but_ollama_choice_is_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_CHAT_MODEL", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    settings = Settings.from_env(tmp_path)
    assert settings.provider == "ollama"
    assert settings.ollama_chat_model == "qwen:latest"

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    settings = Settings.from_env(tmp_path)
    assert settings.provider == "ollama"
    assert not settings.provider_notice


def test_ollama_chat_disables_reasoning_and_bounds_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import langchain_ollama

    captured: dict[str, object] = {}

    class FakeChatOllama:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(langchain_ollama, "ChatOllama", FakeChatOllama)
    assistant = HRPolicyAssistant(settings_for(tmp_path, provider="ollama"))
    assistant._get_chat_model()

    assert captured["reasoning"] is False
    assert captured["num_predict"] == 512


def test_ui_orders_query_submit_and_answer(tmp_path: Path) -> None:
    demo = create_app(HRPolicyAssistant(settings_for(tmp_path)))
    components = [
        (type(component).__name__, getattr(component, "value", None))
        for component in demo.blocks.values()
    ]

    query_heading = components.index(("Markdown", "### User query"))
    query_box = next(
        index
        for index in range(query_heading + 1, len(components))
        if components[index][0] == "Textbox"
    )
    submit_button = components.index(("Button", "Submit"))
    answer_heading = components.index(("Markdown", "### Answer"))
    theme_switch = next(
        component
        for component in demo.blocks.values()
        if type(component).__name__ == "Checkbox"
    )

    assert query_heading < query_box < submit_button < answer_heading
    assert theme_switch.label == "Dark theme"
