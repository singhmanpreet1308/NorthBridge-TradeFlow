
"""Pipeline tests with a fake LLM and fake prediction API (no network)."""

import pytest

from assistant.ops_assistant import (
    answer_question,
    check_citations,
    extract_trade_id,
)
from assistant.retriever import KnowledgeRetriever


FAKE_PREDICTION = {
    "status": "success",
    "prediction": {
        "trade_id": "T-1001",
        "risk_score": 0.0788,
        "risk_band": "Not Flagged",
        "prediction": 0,
        "threshold": 0.1,
        "model_version": "1.0.0",
    },
}


@pytest.fixture(scope="module")
def retriever():
    return KnowledgeRetriever()


class FakeLLM:
    """Records the messages it receives and returns a canned answer."""

    def __init__(self, answer="**Answer** - see [KB-001 v1.1 - Example: T-1001]."):
        self.answer = answer
        self.messages = None

    def __call__(self, messages):
        self.messages = messages
        return {"status": "success", "content": self.answer}

    @property
    def evidence(self):
        return self.messages[1]["content"]


def ask(question, retriever, llm, predict=lambda trade: FAKE_PREDICTION):
    return answer_question(
        question, retriever=retriever, llm_fn=llm, predict_fn=predict
    )


# 1. Evidence gathering
def test_extract_trade_id():
    assert extract_trade_id("why was t-1001 blocked?") == "T-1001"
    assert extract_trade_id("How do amendments work?") is None


def test_t1001_evidence_pack_contains_full_history(retriever):
    llm = FakeLLM()
    result = ask("Why was T-1001 blocked?", retriever, llm)

    assert result["status"] == "success"
    assert "[QUARANTINE BATCH-" in llm.evidence
    assert "[CURATED T-1001 v2]" in llm.evidence
    assert '"validation_status": "BLOCK"' in llm.evidence
    assert '"validation_status": "PASS"' in llm.evidence
    assert "DEMO_NOTIONAL_MISMATCH" in llm.evidence


def test_rule_ids_from_history_steer_retrieval(retriever):
    result = ask("Why was T-1001 blocked?", retriever, FakeLLM())

    assert result["kb_sources"][0] == (
        "KB_001_Notional_Validation.md#Example: T-1001"
    )


# 2. Rule 2: model risk kept separate from validation
def test_model_risk_in_its_own_section(retriever):
    llm = FakeLLM()
    ask("Why was T-1001 blocked?", retriever, llm)

    validation_part, model_part = llm.evidence.split("== MODEL RISK")
    assert "risk_score" not in validation_part
    assert '"risk_score": 0.0788' in model_part
    assert '"scored_version": 2' in model_part


# 3. Rule 4: missing evidence is declared
def test_unknown_trade_is_marked_not_available(retriever):
    llm = FakeLLM()
    result = ask("Why was T-9999 blocked?", retriever, llm)

    assert "NOT AVAILABLE: No trade records found for T-9999" in llm.evidence
    assert result["model_risk"]["status"] == "unavailable"


def test_prediction_api_down_is_marked_not_available(retriever):
    llm = FakeLLM()
    down = lambda trade: {
        "status": "error",
        "message": "Cannot connect to the prediction API.",
    }
    result = ask("Why was T-1001 blocked?", retriever, llm, predict=down)

    assert "NOT AVAILABLE: Cannot connect to the prediction API." in llm.evidence
    assert result["model_risk"]["status"] == "unavailable"


def test_llm_failure_returns_error_not_answer(retriever):
    failing = lambda messages: {"status": "error", "message": "LLM API returned HTTP 401."}
    result = ask("Why was T-1001 blocked?", retriever, failing)

    assert result["status"] == "error"
    assert "answer" not in result


# 4. Rules 3 and 5: citations and read-only prompt
def test_system_prompt_states_grounding_rules(retriever):
    llm = FakeLLM()
    ask("Why was T-1001 blocked?", retriever, llm)
    system = llm.messages[0]["content"]

    assert "Never claim to have executed, approved, amended" in system
    assert "MODEL RISK in its own section" in system
    assert "say so" in system


def test_valid_citations_pass_check(retriever):
    answer = (
        "Blocked [QUARANTINE BATCH-558321D0060990D3]. "
        "Rule [KB-001 v1.1 - Example: T-1001]. Score [MODEL 1.0.0]."
    )
    result = ask("Why was T-1001 blocked?", retriever, FakeLLM(answer))

    assert result["unknown_citations"] == []
    assert result["warnings"] == []


def test_invented_citation_is_flagged(retriever):
    answer = "Per [KB-009 v2.0 - Secret Policy] the trade was blocked."
    result = ask("Why was T-1001 blocked?", retriever, FakeLLM(answer))

    assert result["unknown_citations"] == ["KB-009 v2.0 - Secret Policy"]
    assert any("not cite any knowledge note" in w for w in result["warnings"])


def test_grouped_citations_are_split():
    allowed = {"QUARANTINE BATCH-A", "QUARANTINE BATCH-B", "KB-001 v1.1 - Purpose"}
    check = check_citations(
        "See [QUARANTINE BATCH-A, QUARANTINE BATCH-B] and [KB-001 v1.1 - Purpose].",
        allowed,
        kb_results=[{}],
    )

    assert check["unknown_citations"] == []
    assert len(check["citations_used"]) == 3
