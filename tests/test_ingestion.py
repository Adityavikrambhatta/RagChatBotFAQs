from pathlib import Path


def test_sample_docs_exist() -> None:
    sample_dir = Path("data/sample_docs")
    assert sample_dir.exists()
    assert any(sample_dir.glob("*.txt"))


def test_readme_mentions_langchain() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "LangChain" in readme
    assert "MessagesPlaceholder" in readme
