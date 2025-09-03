"""
News Processor Tool - Autonomous news collection, categorization and summarization.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .rss_feed_tool import rss_multiple_feeds_tool
import re
import json
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
    confidence_score: float = 0.0


class NewsDigest(BaseModel):
    """Complete news digest output."""
    categories: Dict[str, List[Dict[str, Any]]]
    total_articles: int
    interesting_count: int
    category_summaries: Dict[str, str]
    top_stories: List[Dict[str, Any]]
    processing_info: Dict[str, Any]


# News categories for classification
NEWS_CATEGORIES = [
    "Technology",
    "Politics", 
    "Business",
    "Science",
    "Health",
    "Sports",
    "Entertainment",
    "World News",
    "Other"
]

# Curated news sources for comprehensive coverage
NEWS_SOURCES = {
    "general": [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "http://rss.cnn.com/rss/edition.rss", 
        "https://feeds.reuters.com/reuters/topNews",
        "https://feeds.nbcnews.com/nbcnews/public/news"
    ],
    "technology": [
        "https://techcrunch.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.theverge.com/rss/index.xml"
    ],
    "business": [
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://feeds.reuters.com/news/business"
    ],
    "science": [
        "https://www.sciencedaily.com/rss/all.xml",
        "https://feeds.nature.com/nature/rss/current"
    ],
    "politics": [
        "https://feeds.reuters.com/Reuters/PoliticsNews",
        "http://feeds.bbci.co.uk/news/politics/rss.xml"
    ]
}

# Keywords for smart categorization
CATEGORY_KEYWORDS = {
    "Technology": [
        "ai", "artificial intelligence", "tech", "software", "app", "digital", 
        "cyber", "data", "computer", "internet", "blockchain", "cryptocurrency",
        "startup", "innovation", "machine learning", "robot", "automation"
    ],
    "Politics": [
        "election", "government", "president", "congress", "senate", "political",
        "vote", "policy", "minister", "parliament", "campaign", "democrat", 
        "republican", "legislation", "court", "supreme court"
    ],
    "Business": [
        "stock", "market", "economy", "finance", "company", "business", "trade",
        "profit", "revenue", "investment", "banking", "merger", "acquisition",
        "earnings", "inflation", "gdp", "unemployment"
    ],
    "Science": [
        "research", "study", "discovery", "scientist", "laboratory", "experiment",
        "breakthrough", "scientific", "medicine", "physics", "chemistry", "biology"
    ],
    "Health": [
        "health", "medical", "disease", "treatment", "hospital", "doctor", 
        "patient", "medicine", "vaccine", "drug", "therapy", "clinical",
        "pandemic", "virus", "bacteria"
    ],
    "Sports": [
        "game", "match", "team", "player", "championship", "sport", "football",
        "basketball", "soccer", "baseball", "tennis", "golf", "olympics",
        "tournament", "league", "coach"
    ],
    "Entertainment": [
        "movie", "music", "celebrity", "film", "show", "entertainment", "actor",
        "singer", "hollywood", "netflix", "streaming", "concert", "album",
        "theater", "tv", "series"
    ],
    "World News": [
        "war", "conflict", "international", "country", "nation", "global",
        "world", "border", "diplomatic", "treaty", "crisis", "refugee",
        "terrorism", "military", "peace"
    ]
}

# High-impact keywords that make articles "interesting"
INTERESTING_KEYWORDS = [
    "breakthrough", "first", "new", "major", "significant", "historic", "record",
    "crisis", "emergency", "urgent", "breaking", "exclusive", "revealed",
    "billion", "million", "huge", "massive", "dramatic", "shocking", "unprecedented",
    "announced", "launches", "discovers", "confirms", "warns", "alert"
]


def extract_article_content(url: str, max_length: int = 3000) -> str:
    """Extract full article content from URL with enhanced error handling."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
            element.decompose()
        
        # Try multiple content selectors in order of preference
        content_selectors = [
            'article',
            '.article-content', 
            '.post-content',
            '.entry-content',
            '.story-content',
            '.article-body',
            '#content',
            '.content',
            'main'
        ]
        
        content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content = elements[0].get_text(separator=' ', strip=True)
                break
        
        # Fallback: get all paragraph text
        if not content or len(content) < 100:
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        # Clean up content
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\[.*?\]', '', content)  # Remove [edit] tags
        
        return content[:max_length] if content else ""
        
    except Exception as e:
        return f"Content extraction failed: {str(e)}"


def categorize_article(title: str, description: str = "") -> tuple[str, float]:
    """Categorize article using keyword matching with confidence score."""
    try:
        # Handle None values
        title = title or ""
        description = description or ""
        
        text = f"{title} {description}".lower()
        
        if not text.strip():
            return "Other", 0.1
        
        category_scores = {}
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text:
                    # Weight by keyword length (longer keywords = more specific)
                    keyword_score = len(keyword.split())
                    score += keyword_score
                    matched_keywords.append(keyword)
            
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'keywords': matched_keywords
                }
        
        if category_scores:
            best_category = max(category_scores, key=lambda x: category_scores[x]['score'])
            max_score = category_scores[best_category]['score']
            # Normalize confidence (simple approach)
            confidence = min(max_score / 3.0, 1.0)
            return best_category, confidence
        
        return "Other", 0.1
        
    except Exception as e:
        # Fallback to Other category if anything fails
        return "Other", 0.1


def is_article_interesting(title: str, description: str = "") -> tuple[bool, float]:
    """Determine if article is interesting with confidence score."""
    try:
        # Handle None values
        title = title or ""
        description = description or ""
        
        text = f"{title} {description}".lower()
        
        if not text.strip():
            return False, 0.0
        
        interest_score = 0
        matches = []
        
        for keyword in INTERESTING_KEYWORDS:
            if keyword in text:
                interest_score += 1
                matches.append(keyword)
        
        # Additional scoring factors
        if any(phrase in text for phrase in ["first time", "never before", "world's first"]):
            interest_score += 2
        
        if any(symbol in text for symbol in ["$", "billion", "million"]):
            interest_score += 1
        
        # Breaking news indicators
        if any(word in text for word in ["breaking", "urgent", "alert", "emergency"]):
            interest_score += 1.5
        
        # Normalize score
        confidence = min(interest_score / 3.0, 1.0)
        is_interesting = interest_score >= 1
        
        return is_interesting, confidence
        
    except Exception as e:
        # Fallback to not interesting if anything fails
        return False, 0.0
    """Categorize article using keyword matching with confidence score."""
    # Handle None values
    title = title or ""
    description = description or ""
    text = f"{title} {description}".lower()
    
    category_scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                # Weight by keyword length (longer keywords = more specific)
                score += len(keyword.split())
        
        if score > 0:
            category_scores[category] = score
    
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        max_score = category_scores[best_category]
        # Normalize confidence (simple approach)
        confidence = min(max_score / 3.0, 1.0)
        return best_category, confidence
    
    return "Other", 0.1


def is_article_interesting(title: str, description: str = "") -> tuple[bool, float]:
    """Determine if article is interesting with confidence score."""
    # Handle None values
    title = title or ""
    description = description or ""
    text = f"{title} {description}".lower()
    
    interest_score = 0
    matches = []
    
    for keyword in INTERESTING_KEYWORDS:
        if keyword in text:
            interest_score += 1
            matches.append(keyword)
    
    # Additional scoring factors
    if any(word in text for word in ["first time", "never before", "world's first"]):
        interest_score += 2
    
    if any(word in text for word in ["$", "billion", "million"]):
        interest_score += 1
    
    # Normalize score
    confidence = min(interest_score / 3.0, 1.0)
    is_interesting = interest_score >= 1
    
    return is_interesting, confidence


def create_smart_summary(content: str, title: str, max_sentences: int = 3) -> str:
    """Create intelligent summary focusing on key information."""
    # Handle None values
    content = content or ""
    title = title or "Untitled Article"
    
    if not content or len(content) < 50:
        return f"Brief article: {title}"
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if len(sentences) <= max_sentences:
        return '. '.join(sentences).strip() + '.'
    
    # Simple scoring: prefer sentences with key terms
    key_terms = ["said", "announced", "reported", "according", "will", "plans", "new", "first"]
    
    scored_sentences = []
    for i, sentence in enumerate(sentences[:10]):  # Only consider first 10 sentences
        score = 0
        # Earlier sentences get higher score
        score += (10 - i) * 0.1
        # Sentences with key terms get higher score
        for term in key_terms:
            if term in sentence.lower():
                score += 0.3
        
        scored_sentences.append((sentence, score))
    
    # Select top sentences
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    selected = [s[0] for s in scored_sentences[:max_sentences]]
    
    # Maintain original order
    summary_sentences = []
    for sentence in sentences:
        if sentence in selected:
            summary_sentences.append(sentence)
        if len(summary_sentences) >= max_sentences:
            break
    
    summary = '. '.join(summary_sentences).strip()
    if not summary.endswith('.'):
        summary += '.'
    
    return summary


def autonomous_news_processor_tool():
    """Create autonomous news processing tool for the news agent."""
    
    def process_daily_news(
        hours_back: int = Field(default=24, description="Hours back to fetch news"),
        max_articles_per_source: int = Field(default=8, description="Max articles per RSS source"),
        include_sources: List[str] = Field(default=["general", "technology", "business"], description="Source categories to include"),
        min_interest_threshold: float = Field(default=0.3, description="Minimum threshold for interesting articles")
    ) -> Dict[str, Any]:
        """
        Autonomously process daily news: fetch, categorize, summarize interesting articles.
        
        This tool orchestrates the complete news processing workflow:
        1. Fetches headlines from multiple RSS sources
        2. Categorizes articles using keyword matching
        3. Identifies interesting articles
        4. Extracts full content for interesting articles
        5. Creates summaries
        6. Structures output by category
        
        Returns complete news digest ready for main agent consumption.
        """
        start_time = time.time()
        processing_log = []
        
        try:
            # Step 1: Collect RSS feed URLs
            processing_log.append("📡 Collecting RSS feed sources...")
            processing_log.append(f"   Requested source categories: {include_sources}")
            all_feed_urls = []
            for source_category in include_sources:
                if source_category in NEWS_SOURCES:
                    category_feeds = NEWS_SOURCES[source_category]
                    all_feed_urls.extend(category_feeds)
                    processing_log.append(f"   ✓ Added {len(category_feeds)} feeds from '{source_category}':")
                    for feed_url in category_feeds:
                        processing_log.append(f"     - {feed_url}")
                else:
                    processing_log.append(f"   ⚠️ Unknown source category: '{source_category}'")
            
            processing_log.append(f"   Total feed URLs collected: {len(all_feed_urls)}")
            
            if not all_feed_urls:
                processing_log.append("   ❌ No valid feed URLs found!")
                return {
                    "error": "No valid news sources found",
                    "available_sources": list(NEWS_SOURCES.keys()),
                    "processing_log": processing_log
                }
            
            # Step 2: Fetch articles from RSS feeds
            processing_log.append(f"📰 Fetching articles from {len(all_feed_urls)} RSS feeds...")
            processing_log.append(f"   Time range: Last {hours_back} hours")
            processing_log.append(f"   Max articles per source: {max_articles_per_source}")
            
            try:
                rss_scraper = rss_multiple_feeds_tool()
                processing_log.append("   ✓ RSS scraper tool initialized")
                
                rss_results = rss_scraper(all_feed_urls, max_articles_per_source, hours_back)
                processing_log.append("   ✓ RSS scraper completed")
                
                if "error" in rss_results:
                    processing_log.append(f"   ❌ RSS scraping failed: {rss_results['error']}")
                    return {
                        "error": f"RSS fetching failed: {rss_results['error']}", 
                        "processing_log": processing_log
                    }
                
                raw_articles = rss_results.get("items", [])
                processing_log.append(f"   ✓ Successfully collected {len(raw_articles)} articles")
                
                if "feed_results" in rss_results:
                    processing_log.append("   Feed-by-feed results:")
                    for feed_url, result in rss_results["feed_results"].items():
                        if "error" in result:
                            processing_log.append(f"     ❌ {feed_url}: {result['error']}")
                        else:
                            processing_log.append(f"     ✓ {feed_url}: {result.get('items_count', 0)} articles")
                
            except Exception as e:
                processing_log.append(f"   ❌ Exception during RSS fetching: {str(e)}")
                processing_log.append(f"   Exception type: {type(e).__name__}")
                return {
                    "error": f"RSS fetching exception: {str(e)}", 
                    "processing_log": processing_log
                }
            
            if not raw_articles:
                processing_log.append("   ⚠️ No articles found in the specified time range")
                return {
                    "success": True,
                    "message": "No articles found in the specified time range",
                    "total_articles": 0,
                    "processing_log": processing_log
                }
            
            # Step 3: Process each article
            processing_log.append("🔍 Processing and categorizing articles...")
            processing_log.append(f"   Starting analysis of {len(raw_articles)} articles")
            
            categorized_articles = {}
            interesting_articles = []
            processed_count = 0
            error_count = 0
            
            for i, article in enumerate(raw_articles):
                try:
                    if i % 10 == 0:  # Progress update every 10 articles
                        processing_log.append(f"   Progress: {i}/{len(raw_articles)} articles processed")
                    
                    # Validate article data
                    if not article.get('title'):
                        processing_log.append(f"   ⚠️ Skipping article {i+1}: No title")
                        continue
                    
                    article_title = article['title']
                    article_desc = article.get('description', '') or ''
                    article_link = article.get('link', '')
                    article_source = article.get('source', 'Unknown')
                    
                    # Log article being processed (truncated for readability)
                    title_preview = article_title[:60] + "..." if len(article_title) > 60 else article_title
                    processing_log.append(f"   Processing: '{title_preview}' from {article_source}")
                    
                    # Categorize article
                    try:
                        category, cat_confidence = categorize_article(article_title, article_desc)
                        processing_log.append(f"     Category: {category} (confidence: {cat_confidence:.2f})")
                    except Exception as e:
                        processing_log.append(f"     ❌ Categorization failed: {str(e)}")
                        category, cat_confidence = "Other", 0.1
                    
                    # Check if interesting
                    try:
                        is_interesting, interest_confidence = is_article_interesting(article_title, article_desc)
                        processing_log.append(f"     Interesting: {is_interesting} (confidence: {interest_confidence:.2f})")
                    except Exception as e:
                        processing_log.append(f"     ❌ Interest detection failed: {str(e)}")
                        is_interesting, interest_confidence = False, 0.0
                    
                    # Create news article object
                    try:
                        news_article = NewsArticle(
                            title=article_title,
                            link=article_link,
                            category=category,
                            source=article_source,
                            published=article.get('published'),
                            is_interesting=is_interesting and interest_confidence >= min_interest_threshold,
                            confidence_score=max(cat_confidence, interest_confidence)
                        )
                        processing_log.append(f"     ✓ Created NewsArticle object")
                    except Exception as e:
                        processing_log.append(f"     ❌ Failed to create NewsArticle: {str(e)}")
                        continue
                    
                    # Add to category
                    if category not in categorized_articles:
                        categorized_articles[category] = []
                        processing_log.append(f"     Created new category: {category}")
                    categorized_articles[category].append(news_article)
                    
                    # Track interesting articles for full processing
                    if news_article.is_interesting:
                        interesting_articles.append(news_article)
                        processing_log.append(f"     ⭐ Added to interesting articles list")
                    
                    processed_count += 1
                    
                except Exception as e:
                    error_count += 1
                    processing_log.append(f"   ❌ Error processing article {i+1}: {str(e)}")
                    processing_log.append(f"   Article data: {article}")
                    continue
            
            processing_log.append(f"   ✓ Processing complete: {processed_count} articles processed, {error_count} errors")
            processing_log.append(f"   ✓ Categories found: {list(categorized_articles.keys())}")
            processing_log.append(f"   ✓ Interesting articles: {len(interesting_articles)}")
            
            # Step 4: Extract full content and summarize interesting articles
            if interesting_articles:
                processing_log.append("📖 Extracting content for interesting articles...")
                processing_log.append(f"   Processing {len(interesting_articles)} interesting articles")
                summarized_count = 0
                extraction_errors = 0
                
                for j, article in enumerate(interesting_articles):
                    try:
                        article_title_short = article.title[:50] + "..." if len(article.title) > 50 else article.title
                        processing_log.append(f"   [{j+1}/{len(interesting_articles)}] Processing: {article_title_short}")
                        
                        if not article.link:
                            processing_log.append(f"     ⚠️ No link available for article")
                            article.summary = f"Summary unavailable: No link provided for '{article.title}'"
                            continue
                        
                        processing_log.append(f"     🔗 Extracting content from: {article.link}")
                        
                        # Extract full content
                        content = extract_article_content(article.link)
                        processing_log.append(f"     ✓ Extracted {len(content)} characters")
                        
                        if content and len(content) > 100 and not content.startswith("Content extraction failed"):
                            processing_log.append(f"     📝 Creating summary...")
                            # Create summary
                            summary = create_smart_summary(content, article.title)
                            article.summary = summary
                            summarized_count += 1
                            processing_log.append(f"     ✓ Summary created ({len(summary)} chars)")
                        else:
                            processing_log.append(f"     ⚠️ Content extraction insufficient: {content[:100]}...")
                            article.summary = f"Summary unavailable: Content could not be extracted from {article.source}"
                        
                        # Small delay to be respectful to servers
                        time.sleep(0.5)
                        
                    except Exception as e:
                        extraction_errors += 1
                        error_msg = f"Could not process article: {str(e)}"
                        article.summary = error_msg
                        processing_log.append(f"     ❌ Extraction error: {str(e)}")
                        processing_log.append(f"     Exception type: {type(e).__name__}")
                        continue
                
                processing_log.append(f"   ✓ Content extraction complete: {summarized_count} successful, {extraction_errors} errors")
            else:
                processing_log.append("📖 No interesting articles found - skipping content extraction")
            
            # Step 5: Create category summaries and top stories
            processing_log.append("📊 Creating category summaries and identifying top stories...")
            category_summaries = {}
            top_stories = []
            
            for category, articles in categorized_articles.items():
                processing_log.append(f"   Processing category '{category}' with {len(articles)} articles")
                
                # Sort by confidence score
                articles.sort(key=lambda x: x.confidence_score, reverse=True)
                processing_log.append(f"     Sorted by confidence (highest: {articles[0].confidence_score:.2f})")
                
                # Create category summary
                interesting_in_category = [a for a in articles if a.is_interesting]
                total_in_category = len(articles)
                
                if interesting_in_category:
                    top_titles = [a.title for a in interesting_in_category[:3]]
                    category_summaries[category] = f"{len(interesting_in_category)} interesting stories out of {total_in_category} total. Top stories: {'; '.join(top_titles)}"
                    processing_log.append(f"     ✓ {len(interesting_in_category)} interesting articles in this category")
                else:
                    top_titles = [a.title for a in articles[:2]]
                    category_summaries[category] = f"{total_in_category} stories including: {'; '.join(top_titles)}"
                    processing_log.append(f"     ✓ No particularly interesting articles in this category")
                
                # Add top stories from this category
                for article in articles[:2]:  # Top 2 from each category
                    if article.is_interesting:
                        top_stories.append({
                            "title": article.title,
                            "category": article.category,
                            "source": article.source,
                            "summary": article.summary,
                            "confidence": article.confidence_score
                        })
                        processing_log.append(f"     ⭐ Added to top stories: {article.title[:40]}...")
            
            # Sort top stories by confidence
            top_stories.sort(key=lambda x: x['confidence'], reverse=True)
            top_stories = top_stories[:10]  # Keep only top 10
            processing_log.append(f"   ✓ Selected {len(top_stories)} top stories overall")
            
            # Step 6: Prepare final output
            processing_time = round(time.time() - start_time, 2)
            processing_log.append(f"📋 Preparing final output...")
            processing_log.append(f"   Processing completed in {processing_time} seconds")
            
            # Convert to serializable format
            serializable_categories = {}
            total_serialized = 0
            
            for category, articles in categorized_articles.items():
                try:
                    serializable_categories[category] = [
                        {
                            "title": a.title,
                            "link": a.link,
                            "source": a.source,
                            "is_interesting": a.is_interesting,
                            "summary": a.summary,
                            "published": a.published,
                            "confidence": round(a.confidence_score, 3)
                        }
                        for a in articles
                    ]
                    total_serialized += len(articles)
                    processing_log.append(f"   ✓ Serialized {len(articles)} articles for category '{category}'")
                except Exception as e:
                    processing_log.append(f"   ❌ Failed to serialize category '{category}': {str(e)}")
                    serializable_categories[category] = []
            
            processing_log.append(f"   ✓ Total articles serialized: {total_serialized}")
            processing_log.append("✅ Processing completed successfully!")
            
            final_result = {
                "success": True,
                "categories": serializable_categories,
                "total_articles": len(raw_articles),
                "processed_articles": processed_count,
                "interesting_count": len(interesting_articles),
                "category_summaries": category_summaries,
                "top_stories": top_stories,
                "processing_info": {
                    "sources_used": len(all_feed_urls),
                    "source_categories": include_sources,
                    "time_range_hours": hours_back,
                    "processing_time_seconds": processing_time,
                    "min_interest_threshold": min_interest_threshold,
                    "errors_encountered": error_count + extraction_errors if 'extraction_errors' in locals() else error_count
                },
                "processing_log": processing_log
            }
            
            processing_log.append(f"📊 Final stats: {final_result['total_articles']} total, {final_result['processed_articles']} processed, {final_result['interesting_count']} interesting")
            
            return final_result
            
        except Exception as e:
            processing_time = round(time.time() - start_time, 2) if 'start_time' in locals() else 0
            processing_log.append(f"💥 FATAL ERROR after {processing_time} seconds")
            processing_log.append(f"   Error type: {type(e).__name__}")
            processing_log.append(f"   Error message: {str(e)}")
            processing_log.append(f"   Error occurred in main processing loop")
            
            # Try to provide more context about where the error occurred
            import traceback
            tb_lines = traceback.format_exc().split('\n')
            processing_log.append("   Stack trace (last 5 lines):")
            for line in tb_lines[-6:-1]:  # Last 5 non-empty lines
                if line.strip():
                    processing_log.append(f"     {line.strip()}")
            
            return {
                "error": f"News processing failed: {str(e)}",
                "error_type": type(e).__name__,
                "processing_log": processing_log,
                "partial_success": False,
                "processing_time_seconds": processing_time
            }
    
    # Set function metadata
    process_daily_news.__name__ = "process_daily_news"
    process_daily_news.__doc__ = "Autonomously fetch, categorize and summarize daily news from multiple sources"
    
    return process_daily_news


# Export the main tool for the news agent
__all__ = ['autonomous_news_processor_tool']
