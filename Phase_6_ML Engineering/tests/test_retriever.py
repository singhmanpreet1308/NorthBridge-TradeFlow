
import pytest

from assistant.retriever import (
    KnowledgeRetriever,
    format_evidence,
    load_knowledge_base,
    tokenize,
)


@pytest.fixture(scope="module")
def retriever():
    return KnowledgeRetriever()


def top_doc_ids(results):
    return [r["doc_id"] for r in results]


# 1. Knowledge base
def test_knowledge_base_loads_all_versioned_notes():
    documents = load_knowledge_base()

    doc_ids = [doc["doc_id"] for doc in documents]
    assert doc_ids == ["KB-001", "KB-002", "KB-003", "KB-004", "KB-005"]

    for doc in documents:
        assert doc["version"] != "unversioned", doc["doc_id"]
        assert doc["source_file"].endswith(".md")
        assert doc["chunks"], f"{doc['doc_id']} has no sections"


def test_missing_knowledge_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        KnowledgeRetriever(tmp_path / "does_not_exist")


def test_tokenizer_keeps_trade_and_rule_ids():
    tokens = tokenize("Why was T-1001 blocked by DEMO_NOTIONAL_MISMATCH?")

    assert "t-1001" in tokens
    assert "demo_notional_mismatch" in tokens


# 2. T-1001 evidence
def test_why_t1001_blocked_returns_notional_rule(retriever):
    results = retriever.search("Why was T-1001 blocked?")

    top = results[0]
    assert top["doc_id"] == "KB-001"
    assert top["section"] == "Example: T-1001"
    assert "BLOCK" in top["text"]
    assert "DEMO_NOTIONAL_MISMATCH" in top["text"]


def test_t1001_action_returns_escalation_and_guidance(retriever):
    results = retriever.search(
        "What action should be taken for T-1001?", top_k=5
    )

    doc_ids = top_doc_ids(results)
    assert "KB-005" in doc_ids
    assert "KB-001" in doc_ids


def test_t1001_amendment_history(retriever):
    results = retriever.search("How was the T-1001 notional corrected?")

    amendment = [r for r in results if r["doc_id"] == "KB-003"]
    assert amendment, top_doc_ids(results)
    assert "VAL-90BA7E7183AC" in amendment[0]["text"]


def test_t1001_reporting_eligibility(retriever):
    results = retriever.search("Is T-1001 eligible for reporting?")

    assert results[0]["doc_id"] == "KB-004"


def test_t1001_escalation(retriever):
    results = retriever.search("Who should T-1001 be escalated to?")

    assert results[0]["doc_id"] == "KB-005"
    assert results[0]["section"] == "Escalation Path"


# 3. Other topics
@pytest.mark.parametrize(
    "question,expected_doc",
    [
        ("What does DQ-004 mean?", "KB-002"),
        ("How are amendments approved?", "KB-003"),
        ("What happens if revalidation fails?", "KB-003"),
    ],
)
def test_topic_questions_route_to_correct_note(retriever, question, expected_doc):
    results = retriever.search(question)

    assert results[0]["doc_id"] == expected_doc, top_doc_ids(results)


def test_unrelated_question_returns_no_evidence(retriever):
    results = retriever.search("What is the weather in Paris?")

    assert results == []
    assert format_evidence(results) == (
        "No relevant knowledge base evidence found."
    )


# 4. Source references
def test_results_carry_source_references(retriever):
    results = retriever.search("Why was T-1001 blocked?")

    for result in results:
        assert result["source"].startswith("KB_")
        assert "#" in result["source"]
        assert result["citation"].startswith(f"[{result['doc_id']} v")
        assert result["version"] in result["citation"]

    assert results[0]["source"] == (
        "KB_001_Notional_Validation.md#Example: T-1001"
    )


def test_format_evidence_includes_citations(retriever):
    results = retriever.search("Why was T-1001 blocked?", top_k=2)
    evidence = format_evidence(results)

    for result in results:
        assert result["citation"] in evidence
        assert result["source"] in evidence
