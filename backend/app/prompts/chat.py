"""TEAMMATE SCOPE -- RAG chat prompt builder."""

def build_chat_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[SOURCE: {c['source_name']} | TIER {c['confidence_tier']}]\n{c['text']}"
        for c in retrieved_chunks
    )
    return f"""
Answer the question using ONLY the source material below. Cite which source(s)
you used. If the answer isn't in the sources, say so.

QUESTION: {question}

SOURCE MATERIAL:
{context}
"""
