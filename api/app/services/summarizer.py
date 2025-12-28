from typing import Optional, Tuple
import re


def summarize_article(text: Optional[str], title: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate summary and bullet points from article text
    
    Returns:
        Tuple of (summary, bullets_json_string)
    """
    if not text:
        return None, None
    
    # Simple extractive summarization
    sentences = re.split(r'[.!?]\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if not sentences:
        return None, None
    
    # Summary: first 1-2 sentences
    summary = '. '.join(sentences[:2])
    if summary and not summary.endswith('.'):
        summary += '.'
    
    # Bullets: top 3-6 sentences (prefer longer, informative ones)
    # Score sentences by length and keyword presence
    scored_sentences = []
    keywords = ['because', 'however', 'although', 'important', 'key', 'main', 'significant']
    
    for i, sent in enumerate(sentences[2:8]):  # Skip first 2 (already in summary)
        score = len(sent)
        if any(kw in sent.lower() for kw in keywords):
            score += 50
        scored_sentences.append((score, sent))
    
    scored_sentences.sort(reverse=True, key=lambda x: x[0])
    bullets = [sent for _, sent in scored_sentences[:6]]
    
    bullets_json = None
    if bullets:
        import json
        bullets_json = json.dumps(bullets)
    
    return summary, bullets_json

