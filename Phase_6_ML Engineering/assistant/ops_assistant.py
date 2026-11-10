
"""Evidence-grounded AI Operations Assistant.

Workflow:
    question -> trade lookup -> validation history -> ML prediction
             -> BM25 retrieval -> LLM -> cited answer

Grounding rules (enforced in code where possible, and in the prompt):
    1. Observed facts come only from retrieved trade records.
    2. Model risk is reported separately from validation outcomes.
    3. Rules and procedures are explained with knowledge-note citations.
    4. Missing evidence is stated, never invented.
    5. The assistant is read-only: no amendments, approvals or submissions.
       (This module only reads files and calls read-only endpoints.)
"""

import json
import re
from pathlib import Path

from assistant.llm_client import chat_completion
from assistant.prediction_client import predict_trade_risk, prepare_trade_features
from assistant.retriever import KnowledgeRetriever
from assistant.trade_lookup import get_curated_trade, get_quarantine_history


PHASE6_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PHASE6_ROOT.parent

DEFAULT_BACKUP_DIR = (
    PROJECT_ROOT / "Phase_3_Data Engineering and Governance"
    / "azure_backup" / "quarantine" / "trades"
)
DEFAULT_CURATED_FILE = PHASE6_ROOT / "data" / "t1001_curated_v2.csv"

TRADE_ID_PATTERN = re.compile(r"\bT-\d+\b", re.IGNORECASE)
CITATION_PATTERN = re.compile(r"\[([^\[\]]+)\]")

# Only the fields an operator needs; checksums etc. are left out
TRADE_FIELDS = [
    "trade_id", "trade_version", "trade_status", "notional_amount",
    "currency", "product_type", "counterparty_id", "effective_date",
    "maturity_date", "amendment_reason", "created_by",
]
VALIDATION_FIELDS = [
    "detected_rules", "validation_status", "validation_run_id",
    "validated_at_utc", "source_file",
]

SYSTEM_PROMPT = """You are the NorthBridge TradeFlow AI Operations Assistant.
You help trade operations staff understand why trades were blocked and
what documented procedure applies. You are strictly read-only.

Answer ONLY from the EVIDENCE provided. Follow these rules:

1. Observed facts (notional, version, status, rule IDs, run IDs, dates)
   must come from TRADE RECORDS or VALIDATION HISTORY. Cite the evidence
   tag in square brackets, e.g. [CURATED T-1001 v2].
2. Report MODEL RISK in its own section. Never present the model score as
   a validation result, and never use it to explain why a trade was
   blocked. Validation outcomes come from validation rules only.
3. When explaining a rule or procedure, cite the knowledge note exactly as
   tagged, e.g. [KB-001 v1.1 - Example: T-1001].
4. If evidence needed to answer is missing or marked NOT AVAILABLE, say so
   explicitly. Do not guess, and do not use outside knowledge to fill gaps.
5. Never claim to have executed, approved, amended, cancelled or submitted
   anything. You may only recommend steps for an authorised human.
6. Distinguish trade history from the CURRENT state (highest trade_version).
   If the latest version already passed revalidation, say the exception is
   resolved and do not recommend steps that the evidence shows are complete.

Use only citation tags that appear in the evidence, one tag per bracket,
and cite every factual sentence, including in the Answer section.
Format the answer as:

**Answer** - 2-4 sentence direct answer.
**Validation evidence** - facts from trade records and validation history.
**Model risk (separate from validation)** - score, band, threshold, version, or why unavailable.
**Recommended next steps (human action required)** - cited procedure steps.
**Evidence gaps** - anything missing, or "None"."""


# 1. Evidence gathering
def extract_trade_id(question):
    match = TRADE_ID_PATTERN.search(question)
    return match.group(0).upper() if match else None


def _pick(record, fields):
    return {field: record.get(field) for field in fields if field in record}


def _clean(value):
    # pandas NaN -> None so JSON stays readable
    return None if isinstance(value, float) and value != value else value


def gather_trade_evidence(trade_id, backup_dir, curated_file):
    """Return tagged trade records and validation events (rule 1)."""
    evidence = {"records": [], "gaps": []}

    try:
        quarantine = get_quarantine_history(trade_id, backup_dir)
        for event in quarantine["validation_events"]:
            tag = f"QUARANTINE {event['batch_id']}"
            evidence["records"].append({
                "tag": tag,
                "layer": "quarantine",
                "trade": {k: _clean(v) for k, v in _pick(event, TRADE_FIELDS).items()},
                "validation": {k: _clean(v) for k, v in _pick(event, VALIDATION_FIELDS).items()},
            })
    except FileNotFoundError as exc:
        evidence["gaps"].append(f"Quarantine history not available: {exc}")

    try:
        for record in get_curated_trade(trade_id, curated_file):
            tag = f"CURATED {trade_id} v{int(record['trade_version'])}"
            evidence["records"].append({
                "tag": tag,
                "layer": "curated",
                "trade": {k: _clean(v) for k, v in _pick(record, TRADE_FIELDS).items()},
                "validation": {k: _clean(v) for k, v in _pick(record, VALIDATION_FIELDS).items()},
                "_raw": record,
            })
    except FileNotFoundError as exc:
        evidence["gaps"].append(f"Curated records not available: {exc}")

    if not evidence["records"]:
        evidence["gaps"].append(
            f"No trade records found for {trade_id} in quarantine or curated data."
        )

    return evidence


def gather_model_risk(trade_evidence, predict_fn=predict_trade_risk):
    """Score the latest trade version; kept apart from validation (rule 2)."""
    records = trade_evidence["records"]

    if not records:
        return {"status": "unavailable", "reason": "No trade record to score."}

    latest = max(records, key=lambda r: int(r["trade"]["trade_version"]))
    source = latest.get("_raw") or {**latest["trade"], **latest["validation"]}

    try:
        features = prepare_trade_features(source)
    except ValueError as exc:
        return {"status": "unavailable", "reason": str(exc)}

    result = predict_fn(features)

    if result["status"] != "success":
        return {"status": "unavailable", "reason": result["message"]}

    return {
        "status": "available",
        "tag": f"MODEL {result['prediction']['model_version']}",
        "scored_version": int(latest["trade"]["trade_version"]),
        **result["prediction"],
    }


def build_retrieval_query(question, trade_evidence):
    """Add detected rule IDs to the query so the matching KB note is found."""
    rules = set()
    for record in trade_evidence["records"]:
        detected = record["validation"].get("detected_rules") or "[]"
        try:
            rules.update(json.loads(detected))
        except (TypeError, ValueError):
            pass

    return " ".join([question, *sorted(rules)])


# 2. Prompt construction
def format_evidence_pack(trade_id, trade_evidence, model_risk, kb_results):
    lines = ["EVIDENCE", ""]

    lines.append("== TRADE RECORDS AND VALIDATION HISTORY ==")
    if trade_id is None:
        lines.append("NOT AVAILABLE: no trade ID was given in the question.")
    for record in trade_evidence["records"]:
        lines.append(f"[{record['tag']}]")
        lines.append("  trade: " + json.dumps(record["trade"], default=str))
        lines.append("  validation: " + json.dumps(record["validation"], default=str))
    for gap in trade_evidence["gaps"]:
        lines.append(f"NOT AVAILABLE: {gap}")

    lines.append("")
    lines.append("== MODEL RISK (predictive score, NOT a validation outcome) ==")
    if model_risk["status"] == "available":
        lines.append(f"[{model_risk['tag']}]")
        lines.append("  " + json.dumps({
            k: model_risk[k] for k in (
                "trade_id", "scored_version", "risk_score", "risk_band",
                "prediction", "threshold", "model_version",
            )
        }))
    else:
        lines.append(f"NOT AVAILABLE: {model_risk['reason']}")

    lines.append("")
    lines.append("== KNOWLEDGE NOTES ==")
    if not kb_results:
        lines.append("NOT AVAILABLE: no relevant knowledge note was retrieved.")
    for result in kb_results:
        lines.append(f"{result['citation']} (source: {result['source']})")
        lines.append(result["text"])
        lines.append("")

    return "\n".join(lines)


# 3. Answer verification
def allowed_citations(trade_evidence, model_risk, kb_results):
    tags = {record["tag"] for record in trade_evidence["records"]}
    if model_risk["status"] == "available":
        tags.add(model_risk["tag"])
    tags.update(result["citation"].strip("[]") for result in kb_results)
    return tags


def check_citations(answer, allowed, kb_results):
    """Flag invented citations and answers that skip the knowledge notes."""
    # "[A, B]" or "[A; B]" counts as two citations
    used = {
        part.strip()
        for bracket in CITATION_PATTERN.findall(answer)
        for part in re.split(r"[;,](?=\s*(?:KB-|QUARANTINE|CURATED|MODEL))", bracket)
    }
    # "[NOT AVAILABLE]" marks a stated evidence gap (rule 4), not a citation
    used.discard("NOT AVAILABLE")
    unknown = sorted(used - allowed)
    kb_cited = any(tag.startswith("KB-") for tag in used & allowed)

    warnings = []
    if unknown:
        warnings.append(f"Answer cites evidence that was not provided: {unknown}")
    if kb_results and not kb_cited:
        warnings.append("Answer does not cite any knowledge note.")

    return {
        "citations_used": sorted(used & allowed),
        "unknown_citations": unknown,
        "warnings": warnings,
    }


# 4. Orchestration
def answer_question(
    question,
    trade_id=None,
    backup_dir=DEFAULT_BACKUP_DIR,
    curated_file=DEFAULT_CURATED_FILE,
    retriever=None,
    top_k=5,
    llm_fn=chat_completion,
    predict_fn=predict_trade_risk,
):
    trade_id = trade_id or extract_trade_id(question)
    retriever = retriever or KnowledgeRetriever()

    # Trade lookup + validation history
    if trade_id:
        trade_evidence = gather_trade_evidence(trade_id, backup_dir, curated_file)
    else:
        trade_evidence = {"records": [], "gaps": []}

    # ML prediction (separate channel)
    model_risk = (
        gather_model_risk(trade_evidence, predict_fn)
        if trade_id else
        {"status": "unavailable", "reason": "No trade ID in the question."}
    )

    # BM25 retrieval
    kb_results = retriever.search(
        build_retrieval_query(question, trade_evidence), top_k=top_k
    )

    evidence_pack = format_evidence_pack(
        trade_id, trade_evidence, model_risk, kb_results
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{evidence_pack}\n\nQUESTION: {question}"},
    ]

    llm_result = llm_fn(messages)

    if llm_result["status"] != "success":
        return {
            "status": "error",
            "question": question,
            "trade_id": trade_id,
            "message": llm_result["message"],
            "evidence_pack": evidence_pack,
        }

    answer = llm_result["content"]
    verification = check_citations(
        answer,
        allowed_citations(trade_evidence, model_risk, kb_results),
        kb_results,
    )

    return {
        "status": "success",
        "question": question,
        "trade_id": trade_id,
        "answer": answer,
        **verification,
        "model_risk": {k: v for k, v in model_risk.items()},
        "kb_sources": [r["source"] for r in kb_results],
        "evidence_pack": evidence_pack,
    }
