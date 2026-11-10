
import sys
from pathlib import Path

# Make the Phase 6 root importable when this file is run directly
# (python assistant/test_retriever.py or the VS Code Run button)
PHASE6_ROOT = Path(__file__).resolve().parent.parent
if str(PHASE6_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE6_ROOT))

from assistant.retriever import (
    KnowledgeRetriever,
    format_evidence,
)


# Initialise knowledge retriever
retriever = KnowledgeRetriever()

# Test questions
questions = [
    "Why was T-1001 originally blocked?",
    "What is DEMO_NOTIONAL_MISMATCH?",
    "What action should operations take for a notional mismatch?",
    "How should an approved trade amendment be handled?",
    "What should happen before simulated reporting?",
]


for question in questions:

    print("\n" + "=" * 60)
    print("QUESTION:", question)

    results = retriever.search(
        query=question,
        top_k=3
    )

    print("\nRETRIEVED EVIDENCE:")
    print(format_evidence(results))
