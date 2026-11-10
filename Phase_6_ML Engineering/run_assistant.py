
"""Ask the AI Operations Assistant a question from the command line.

Usage (from the Phase 6 folder, with the prediction API running):
    python run_assistant.py "Why was T-1001 blocked and what should happen next?"
    python run_assistant.py --show-evidence "Is T-1001 eligible for reporting?"
"""

import argparse

from assistant.ops_assistant import answer_question


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("question")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--show-evidence", action="store_true",
        help="Print the evidence pack sent to the LLM",
    )
    args = parser.parse_args()

    result = answer_question(args.question, top_k=args.top_k)

    if args.show_evidence:
        print(result["evidence_pack"])
        print("=" * 70)

    if result["status"] != "success":
        print("Assistant error:", result["message"])
        return

    print(result["answer"])
    print("\n" + "-" * 70)
    print("Citations used:", ", ".join(result["citations_used"]) or "none")
    print("KB sources retrieved:", ", ".join(result["kb_sources"]) or "none")

    for warning in result["warnings"]:
        print("WARNING:", warning)


if __name__ == "__main__":
    main()
