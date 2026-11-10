
"""Lightweight keyword retriever over the versioned knowledge base.

Each Markdown note is split into sections (one chunk per "## " heading)
and ranked with BM25. No embeddings or external services are used, so
results are deterministic and every chunk keeps its source reference.
"""

import math
import re
from collections import Counter
from pathlib import Path


DEFAULT_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"

METADATA_FIELDS = {"version", "domain", "rule id", "source"}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "has", "have", "how", "i", "in", "is", "it", "its", "of",
    "on", "or", "should", "that", "the", "this", "to", "was", "were",
    "what", "when", "where", "which", "who", "why", "will", "with",
}

# Keeps identifiers such as T-1001, DQ-004 and DEMO_NOTIONAL_MISMATCH whole
TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*")


# Operator wording -> vocabulary used in the KB notes (query side only)
QUERY_SYNONYMS = {
    "action": ["guidance", "steps", "escalate"],
    "next": ["guidance", "steps"],
    "fix": ["amendment", "correction"],
    "resolve": ["amendment", "escalate", "guidance"],
    "rejected": ["block"],
    "submit": ["reporting"],
}

STEM_LENGTH = 5


# 1. Text normalisation
def _stem(token):
    # Prefix truncation: approve/approved/approval -> "appro",
    # escalate/escalation -> "escal". Identifiers are left whole.
    if token.isalpha() and len(token) > STEM_LENGTH:
        return token[:STEM_LENGTH]
    return token


def tokenize(text):
    """Lowercase, keep compound IDs, also index their parts, drop stopwords."""
    tokens = []

    for token in TOKEN_PATTERN.findall(text.lower()):
        tokens.append(token)

        parts = re.split(r"[-_]", token)
        if len(parts) > 1:
            tokens.extend(parts)

    return [
        _stem(token) for token in tokens
        if token not in STOPWORDS and len(token) > 1
    ]


def expand_query(query):
    words = TOKEN_PATTERN.findall(query.lower())
    extra = [syn for word in words for syn in QUERY_SYNONYMS.get(word, [])]
    return " ".join([query, *extra])


# 2. Knowledge base loading
def parse_note(path):
    """Split one KB note into metadata and section chunks."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()

    title = path.stem
    metadata = {}
    chunks = []
    section = None
    body = []

    def flush():
        text = "\n".join(body).strip()
        if section and text:
            chunks.append({"section": section, "text": text})

    for line in lines:
        if line.startswith("# ") and not chunks and section is None:
            title = line[2:].strip()
            continue

        if line.startswith("## "):
            flush()
            section = line[3:].strip()
            body = []
            continue

        if section is None:
            key, sep, value = line.partition(":")
            if sep and key.strip().lower() in METADATA_FIELDS:
                metadata[key.strip().lower().replace(" ", "_")] = value.strip()
            continue

        body.append(line)

    flush()

    doc_id = title.split(":", 1)[0].strip() if ":" in title else path.stem

    return {
        "doc_id": doc_id,
        "title": title,
        "version": metadata.get("version", "unversioned"),
        "domain": metadata.get("domain", ""),
        "rule_id": metadata.get("rule_id", ""),
        "source_file": path.name,
        "chunks": chunks,
    }


def load_knowledge_base(knowledge_dir=DEFAULT_KNOWLEDGE_DIR):
    knowledge_dir = Path(knowledge_dir)

    if not knowledge_dir.is_dir():
        raise FileNotFoundError(
            f"Knowledge directory not found: {knowledge_dir}"
        )

    files = sorted(knowledge_dir.glob("KB_*.md"))

    if not files:
        raise FileNotFoundError(
            f"No KB_*.md notes found in {knowledge_dir}"
        )

    return [parse_note(file) for file in files]


# 3. BM25 retriever
class KnowledgeRetriever:

    def __init__(self, knowledge_dir=DEFAULT_KNOWLEDGE_DIR, k1=1.5, b=0.75):
        self.documents = load_knowledge_base(knowledge_dir)
        self.k1 = k1
        self.b = b
        self.chunks = []

        for doc in self.documents:
            for chunk in doc["chunks"]:
                # Title and heading are indexed with the body so a question
                # about "amendments" reaches every section of KB-003.
                indexed_text = " ".join([
                    doc["title"], chunk["section"], chunk["text"],
                ])
                tokens = tokenize(indexed_text)

                self.chunks.append({
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "version": doc["version"],
                    "domain": doc["domain"],
                    "source_file": doc["source_file"],
                    "section": chunk["section"],
                    "text": chunk["text"],
                    "term_freq": Counter(tokens),
                    "length": len(tokens),
                })
                if not self.chunks:
                 raise ValueError("Knowledge base contains no retrievable sections.")

        self.avg_length = (
            sum(c["length"] for c in self.chunks) / len(self.chunks)
        )

        doc_freq = Counter()
        for chunk in self.chunks:
            doc_freq.update(chunk["term_freq"].keys())

        n = len(self.chunks)
        self.idf = {
            term: math.log(1 + (n - df + 0.5) / (df + 0.5))
            for term, df in doc_freq.items()
        }

    def _score(self, query_terms, chunk):
        score = 0.0
        norm = self.k1 * (
            1 - self.b + self.b * chunk["length"] / self.avg_length
        )

        for term in query_terms:
            tf = chunk["term_freq"].get(term, 0)
            if tf:
                score += self.idf[term] * tf * (self.k1 + 1) / (tf + norm)

        return score

    def search(self, query, top_k=3, min_score=0.5):
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        """Return the top matching sections with source references."""
        query_terms = set(tokenize(expand_query(query)))

        if not query_terms:
            return []

        scored = [
            (self._score(query_terms, chunk), chunk)
            for chunk in self.chunks
        ]

        scored = [item for item in scored if item[0] >= min_score]
        scored.sort(key=lambda item: item[0], reverse=True)

        return [
            {
                "doc_id": chunk["doc_id"],
                "title": chunk["title"],
                "version": chunk["version"],
                "section": chunk["section"],
                "score": round(score, 3),
                "text": chunk["text"],
                "source": f"{chunk['source_file']}#{chunk['section']}",
                "citation": (
                    f"[{chunk['doc_id']} v{chunk['version']} - "
                    f"{chunk['section']}]"
                ),
            }
            for score, chunk in scored[:top_k]
        ]


def format_evidence(results):
    """Render retrieved sections as cited evidence for the assistant."""
    if not results:
        return "No relevant knowledge base evidence found."

    return "\n\n".join(
        f"{r['citation']} ({r['source']})\n{r['text']}"
        for r in results
    )
