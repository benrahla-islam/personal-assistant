"""
News Processor Tool - Simplified news collection, categorization and summarization.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from .rss_feed_tool import rss_multiple_feeds_tool
import re
import time


class NewsArticle(BaseModel):
    """Model for processed news articles."""
    title: str
    link: str
    category: str
    source: str
    summary: Optional[str] = None
    is_interesting: bool = False
    published: Optional[str] = None


# Curated news sources
NEWS_SOURCES = {
    "general": [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "http://rss.cnn.com/rss/edition.rss", 
        "https://feeds.reuters.com/reuters/topNews",
    ],
    "technology": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml"
    ],
    "business": [
        "https://feeds.reuters.com/news/business"
    ],
    "science": [
        "https://www.sciencedaily.com/rss/all.xml",
    ]
}

# Keywords for smart categorization
CATEGORY_KEYWORDS = {
    "Technology": ["ai", "tech", "software", "app", "digital", "cyber", "data", "internet", "blockchain"],
    "Politics": ["election", "government", "president", "congress", "political", "vote", "policy"],
    "Business": ["stock", "market", "economy", "finance", "company", "business", "trade", "profit"],
    "Science": ["research", "study", "discovery", "scientist", "experiment", "scientific"],
    "Health": ["health", "medical", "disease", "treatment", "hospital", "doctor", "vaccine"],
    "Sports": ["game", "match", "team", "player", "championship", "sport", "football", "basketball"],
    "Entertainment": ["movie", "music", "celebrity", "film", "show", "entertainment", "actor"],
    "World News": ["war", "conflict", "international", "country", "global", "world", "diplomatic"]
}

# Keywords that make articles interesting
INTERESTING_KEYWORDS = [
    "breakthrough", "first", "major", "significant", "historic", "breaking", 
    "exclusive", "billion", "million", "announces", "launches", "discovers"
]


def categorize_article(title: str, description: str = "") -> str:
    """Categorize article using keyword matching."""
    text = f"{title or ''} {description or ''}".lower()
    
    if not text.strip():
        return "Other"
    
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            category_scores[category] = score
    
    return max(category_scores, key=category_scores.get) if category_scores else "Other"


def is_article_interesting(title: str, description: str = "") -> bool:
    """Determine if article is interesting."""
    text = f"{title or ''} {description or ''}".lower()
    return any(keyword in text for keyword in INTERESTING_KEYWORDS)


def extract_article_content(url: str) -> str:
    """Extract article content from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content
        content = ""
        for selector in ['article', '.article-content', '.post-content', 'main']:
            elements = soup.select(selector)
            if elements:
                content = elements[0].get_text(separator=' ', strip=True)
                break
        
        # Fallback to paragraphs
        if not content or len(content) < 100:
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        # Clean up
        content = re.sub(r'\s+', ' ', content)
        return content[:3000] if content else ""
        
    except Exception as e:
        return f"Content extraction failed: {str(e)}"


def create_summary(content: str, title: str) -> str:
    """Create simple summary from content."""
    if not content or len(content) < 50:
        return f"Brief article: {title}"
    
    # Get first few sentences
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if len(sentences) <= 3:
        return '. '.join(sentences).strip() + '.'
    
    # Return first 3 sentences
    summary = '. '.join(sentences[:3]).strip()
    return summary + '.' if not summary.endswith('.') else summary


def autonomous_news_processor_tool():
    """Create simplified autonomous news processing tool."""
    
    def process_daily_news(
        hours_back: int = Field(default=24, description="Hours back to fetch news"),
        max_articles: int = Field(default=20, description="Maximum number of articles to process"),
        source_categories: str = Field(default="general,technology", description="Comma-separated source categories (general, technology, business, science)")
    ) -> Dict[str, Any]:
        """
        Fetch and process daily news from multiple sources.
        
        Returns categorized news with summaries for interesting articles.
        """
        start_time = time.time()
        
        try:
            # Parse source categories - handle string input
            if isinstance(source_categories, str):
                categories = [c.strip() for c in source_categories.split(',')]
            else:
                categories = ["general", "technology"]
            
            # Collect feed URLs
            feed_urls = []
            for category in categories:
                if category in NEWS_SOURCES:
                    feed_urls.extend(NEWS_SOURCES[category])
            
            if not feed_urls:
                return {
                    "error": "No valid news sources found",
                    "available_sources": list(NEWS_SOURCES.keys())
                }
            
            # Fetch articles from RSS feeds
            rss_scraper = rss_multiple_feeds_tool()
            rss_results = rss_scraper(feed_urls, max_articles // len(feed_urls), hours_back)
            
            if "error" in rss_results:
                return {"error": f"RSS fetching failed: {rss_results['error']}"}
            
            raw_articles = rss_results.get("items", [])
            
            if not raw_articles:
                return {
                    "success": True,
                    "message": "No articles found in the specified time range",
                    "total_articles": 0
                }
            
            # Process articles
            categorized = {}
            interesting = []
            
            for article in raw_articles[:max_articles]:
                title = article.get('title', '')
                if not title:
                    continue
                
                description = article.get('description', '') or ''
                link = article.get('link', '')
                source = article.get('source', 'Unknown')
                
                # Categorize
                category = categorize_article(title, description)
                
                # Check if interesting
                is_int = is_article_interesting(title, description)
                
                # Create article object
                news_article = NewsArticle(
                    title=title,
                    link=link,
                    category=category,
                    source=source,
                    published=article.get('published'),
                    is_interesting=is_int
                )
                
                # Add to category
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(news_article)
                
                # Track interesting articles
                if is_int:
                    interesting.append(news_article)
            
            # Extract content for interesting articles (limit to top 5)
            for article in interesting[:5]:
                if article.link:
                    content = extract_article_content(article.link)
                    if content and len(content) > 100 and not content.startswith("Content extraction failed"):
                        article.summary = create_summary(content, article.title)
                    else:
                        article.summary = f"Summary unavailable for: {article.title}"
                    time.sleep(0.5)  # Be nice to servers
            
            # Create category summaries
            category_summaries = {}
            top_stories = []
            
            for category, articles in categorized.items():
                interesting_in_cat = [a for a in articles if a.is_interesting]
                
                if interesting_in_cat:
                    top_titles = [a.title[:60] for a in interesting_in_cat[:2]]
                    category_summaries[category] = f"{len(interesting_in_cat)} interesting stories: {'; '.join(top_titles)}"
                else:
                    top_titles = [a.title[:60] for a in articles[:2]]
                    category_summaries[category] = f"{len(articles)} stories including: {'; '.join(top_titles)}"
                
                # Add top stories
                for a in articles[:2]:
                    if a.is_interesting and a.summary:
                        top_stories.append({
                            "title": a.title,
                            "category": a.category,
                            "source": a.source,
                            "summary": a.summary
                        })
            
            # Prepare output
            serializable_categories = {
                cat: [
                    {
                        "title": a.title,
                        "link": a.link,
                        "source": a.source,
                        "is_interesting": a.is_interesting,
                        "summary": a.summary,
                        "published": a.published
                    }
                    for a in articles
                ]
                for cat, articles in categorized.items()
            }
            
            return {
                "success": True,
                "categories": serializable_categories,
                "total_articles": len(raw_articles),
                "interesting_count": len(interesting),
                "category_summaries": category_summaries,
                "top_stories": top_stories[:10],
                "processing_info": {
                    "sources_used": len(feed_urls),
                    "source_categories": categories,
                    "time_range_hours": hours_back,
                    "processing_time_seconds": round(time.time() - start_time, 2)
                }
            }
            
        except Exception as e:
            return {
                "error": f"News processing failed: {str(e)}",
                "error_type": type(e).__name__
            }
    
    return process_daily_news


# Export the main tool
__all__ = ['autonomous_news_processor_tool']
