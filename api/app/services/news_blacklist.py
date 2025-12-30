"""
News Blacklist Configuration
Filters out irrelevant content for Bay Area tech workers
"""

# Keywords that indicate irrelevant content (hard filter)
BLACKLIST_KEYWORDS = [
    # Politics (unless big tech related)
    "election", "president", "congress", "senate", "house", "vote", "ballot",
    "democrat", "republican", "trump", "biden", "political party",
    
    # War/conflicts (unless tech/market impact)
    "war", "conflict", "invasion", "attack", "bombing", "military strike",
    
    # Crime (unless tech company related)
    "murder", "shooting", "robbery", "theft", "arrest", "trial", "court case",
    
    # Celebrity/gossip
    "celebrity", "actor", "actress", "movie", "film", "oscar", "grammy",
    "entertainment news", "gossip",
    
    # Sports (unless tech company sponsorship)
    "sports", "football", "basketball", "soccer", "baseball", "nfl", "nba",
    "championship", "tournament", "olympics",
    
    # General world news (unless tech impact)
    "weather", "hurricane", "earthquake", "natural disaster",
    
    # Generic Show HN (unless AI/devtools)
    "show hn",
]

# Domains to block
BLACKLIST_DOMAINS = [
    "facebook.com", "twitter.com", "linkedin.com", "reddit.com",
    "youtube.com", "tiktok.com", "instagram.com", "pinterest.com",
    "pornhub.com", "xhamster.com",  # Adult content
]

# Keywords that indicate big tech relevance (positive signal)
BIG_TECH_KEYWORDS = [
    # Companies
    "openai", "google", "meta", "microsoft", "nvidia", "apple", "amazon",
    "tesla", "anthropic", "xai", "apple inc", "microsoft corp", "nvidia corp",
    "alphabet", "meta platforms", "amazon.com",
    
    # AI/LLM
    "ai", "artificial intelligence", "llm", "large language model", "gpt",
    "claude", "gemini", "chatgpt", "agi", "neural network", "machine learning",
    "deep learning", "transformer", "inference", "training", "model",
    
    # Tech infrastructure
    "gpu", "cuda", "datacenter", "cloud", "aws", "azure", "gcp",
    "semiconductor", "chip", "tsmc", "intel", "amd",
    
    # Markets/career
    "earnings", "guidance", "revenue", "profit", "layoff", "hiring",
    "stock", "share", "nasdaq", "dow", "s&p", "market",
    "sec", "doj", "antitrust", "regulation", "lawsuit",
    
    # Startups/funding
    "startup", "funding", "series a", "series b", "ipo", "unicorn",
    "venture capital", "vc", "investment",
]

# Tags mapping
TAG_MAPPINGS = {
    "openai": "AI",
    "google": "GOOG",
    "meta": "META",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "apple": "AAPL",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "anthropic": "AI",
    "xai": "AI",
    "llm": "LLM",
    "gpt": "LLM",
    "claude": "LLM",
    "gemini": "LLM",
    "gpu": "Chips",
    "cuda": "Chips",
    "semiconductor": "Chips",
    "chip": "Chips",
    "tsmc": "Chips",
    "intel": "Chips",
    "amd": "Chips",
    "cloud": "Cloud",
    "aws": "Cloud",
    "azure": "Cloud",
    "gcp": "Cloud",
    "datacenter": "Cloud",
    "security": "Security",
    "cybersecurity": "Security",
    "earnings": "Earnings",
    "layoff": "Layoffs",
    "hiring": "Layoffs",
    "antitrust": "Regulation",
    "sec": "Regulation",
    "doj": "Regulation",
    "regulation": "Regulation",
    "lawsuit": "Regulation",
    "startup": "Startups",
    "funding": "Startups",
    "ipo": "Startups",
    "vc": "Startups",
}

# Allowed tags (max 3 per item)
ALLOWED_TAGS = [
    "AI", "LLM", "NVDA", "MSFT", "META", "GOOG", "AAPL", "AMZN", "TSLA",
    "Chips", "Cloud", "Security", "Earnings", "Layoffs", "Regulation", "Startups"
]


def should_blacklist(title: str, description: str = "", domain: str = "") -> bool:
    """
    Check if content should be blacklisted
    Returns True if should be filtered out
    """
    text = f"{title} {description}".lower()
    domain_lower = domain.lower()
    
    # Check domain blacklist
    for blocked_domain in BLACKLIST_DOMAINS:
        if blocked_domain in domain_lower:
            return True
    
    # Check keyword blacklist
    for keyword in BLACKLIST_KEYWORDS:
        if keyword in text:
            # Exception: if it's also big tech related, allow it
            if any(big_tech in text for big_tech in BIG_TECH_KEYWORDS):
                continue
            return True
    
    return False


def extract_tags(title: str, description: str = "") -> list[str]:
    """
    Extract tags from title and description
    Returns max 3 tags
    """
    text = f"{title} {description}".lower()
    found_tags = set()
    
    # Check tag mappings
    for keyword, tag in TAG_MAPPINGS.items():
        if keyword in text and tag in ALLOWED_TAGS:
            found_tags.add(tag)
            if len(found_tags) >= 3:
                break
    
    return list(found_tags)[:3]


def is_big_tech_related(title: str, description: str = "") -> bool:
    """Check if content is related to big tech/AI/markets"""
    text = f"{title} {description}".lower()
    return any(keyword in text for keyword in BIG_TECH_KEYWORDS)
