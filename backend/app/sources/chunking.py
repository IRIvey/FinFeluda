"""
Boundary-aware chunking.

The naive approach (slice every N characters) cuts mid-sentence and
separates facts from their qualifying clauses -- e.g. "Revenue grew
12%" gets split from "...but only in the enterprise segment, which
represents 8% of total revenue", changing what the fact actually
means. This module splits on paragraph/sentence boundaries first,
then packs those units into chunks up to a target size, only falling
back to a hard character cut if a single sentence is pathologically
long (e.g. a wall of text with no punctuation, which does happen with
scraped HTML).

Chunk size is tier-dependent: a Reddit thread benefits from larger
chunks (conversational text loses meaning when sliced thin), while
a dense financial filing benefits from smaller chunks (more precise
retrieval, less dilution of the embedding per the "embedding diluted
by oversized chunks" problem).
"""
import re
from app.schemas.source_document import ConfidenceTier

# Tuned per source density, not a single global default.
# (target_chars, overlap_chars)
TIER_CHUNK_PROFILE: dict[ConfidenceTier, tuple[int, int]] = {
    ConfidenceTier.AUTHORITATIVE: (700, 100),     # dense filings -- smaller, precise chunks
    ConfidenceTier.OFFICIAL: (900, 120),
    ConfidenceTier.CORROBORATING: (1000, 150),
    ConfidenceTier.UNVERIFIED_SIGNAL: (1200, 150),  # conversational text -- needs more room
}

DEFAULT_PROFILE = (1000, 150)

# Split on paragraph breaks first, then sentence breaks within a paragraph.
# The lookbehind/lookahead cover both Latin terminators (.!?) and the Bangla
# dari (।) -- Bangla has no letter case, so the lookahead also accepts the
# Bengali Unicode block (ঀ-৿) alongside capitals/digits, otherwise
# a Bangla-only paragraph never matches and falls through to the hard-slice
# fallback below instead of splitting cleanly on sentence boundaries.
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?।])\s+(?=[A-Z0-9ঀ-৿])")


def _split_into_sentences(paragraph: str) -> list[str]:
    paragraph = paragraph.strip()
    if not paragraph:
        return []
    sentences = _SENTENCE_SPLIT.split(paragraph)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text_by_boundary(
    text: str,
    confidence_tier: ConfidenceTier = ConfidenceTier.CORROBORATING,
) -> list[str]:
    """
    Pack whole sentences into chunks up to the tier's target size,
    carrying a small sentence-level overlap between consecutive
    chunks so a fact split across a chunk boundary still has its
    immediate context in at least one chunk. Never cuts a sentence
    in half except as a last-resort fallback for pathologically long
    sentences (no punctuation at all -- common in scraped HTML/markup
    leftovers).
    """
    target_size, overlap_size = TIER_CHUNK_PROFILE.get(confidence_tier, DEFAULT_PROFILE)

    paragraphs = _PARAGRAPH_SPLIT.split(text)
    sentences: list[str] = []
    for para in paragraphs:
        sentences.extend(_split_into_sentences(para))

    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    i = 0
    while i < len(sentences):
        sentence = sentences[i]

        # Fallback: a single sentence longer than the whole target size
        # (no real sentence boundaries found, e.g. raw scraped text) --
        # hard-slice just that one sentence rather than blowing the budget.
        if len(sentence) > target_size:
            if current:
                chunks.append(" ".join(current))
                current, current_len = [], 0
            for start in range(0, len(sentence), target_size):
                chunks.append(sentence[start:start + target_size])
            i += 1
            continue

        if current_len + len(sentence) + 1 > target_size and current:
            chunks.append(" ".join(current))

            # Carry overlap: keep trailing sentences from the previous
            # chunk whose combined length is within overlap_size, so
            # context isn't lost at the boundary.
            overlap_sentences: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > overlap_size:
                    break
                overlap_sentences.insert(0, s)
                overlap_len += len(s)

            current = overlap_sentences
            current_len = overlap_len

        current.append(sentence)
        current_len += len(sentence) + 1
        i += 1

    if current:
        chunks.append(" ".join(current))

    return chunks
