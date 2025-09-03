"""
RSS Feed Tool - Scrapes and processes RSS feeds for news content.
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class RSSFeedItem(BaseModel):
    """Model for RSS feed items."""
    title: str
    link: str
    description: str
    published: Optional[str] = None
    source: str


def rss_feed_scraper_tool():
    """Create RSS feed scraper tool for news collection."""
    
    def scrape_rss_feed(
        feed_url: str = Field(description="RSS feed URL to scrape"),
        max_items: int = Field(default=10, description="Maximum number of items to retrieve"),
        hours_back: int = Field(default=24, description="Only get items from last N hours")
    ) -> List[Dict]:
        """
        Scrape RSS feed and return recent news items.
        
        Args:
            feed_url: The RSS feed URL to scrape
            max_items: Maximum number of items to return (default: 10)
            hours_back: Only return items from the last N hours (default: 24)
            
        Returns:
            List of news items with title, link, description, published date, and source
        """
        try:
            # Parse the RSS feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                return {"error": f"Invalid RSS feed: {feed_url}"}
            
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            items = []
            feed_title = getattr(feed.feed, 'title', 'Unknown Source')
            
            for entry in feed.entries[:max_items]:
                # Parse published date
                published_date = None
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        # Check if all elements are not None
                        if all(x is not None for x in entry.published_parsed[:6]):
                            published_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        # Check if all elements are not None
                        if all(x is not None for x in entry.updated_parsed[:6]):
                            published_date = datetime(*entry.updated_parsed[:6])
                except (TypeError, ValueError) as e:
                    # If date parsing fails, we'll include the article anyway
                    published_date = None
                
                # Filter by time if we have a valid date
                if published_date is not None and published_date < cutoff_time:
                    continue
                
                # Extract content
                description = ""
                if hasattr(entry, 'summary'):
                    description = entry.summary
                elif hasattr(entry, 'description'):
                    description = entry.description
                
                item = RSSFeedItem(
                    title=getattr(entry, 'title', 'No Title'),
                    link=getattr(entry, 'link', ''),
                    description=description,
                    published=getattr(entry, 'published', None),
                    source=feed_title
                )
                
                items.append(item.model_dump())
            
            return {
                "success": True,
                "feed_title": feed_title,
                "items_count": len(items),
                "items": items
            }
            
        except Exception as e:
            return {"error": f"Failed to scrape RSS feed: {str(e)}"}
    
    # Return the tool function with metadata
    scrape_rss_feed.__name__ = "scrape_rss_feed"
    scrape_rss_feed.__doc__ = "Scrape RSS feed and return recent news items"
    
    return scrape_rss_feed


def rss_multiple_feeds_tool():
    """Create tool to scrape multiple RSS feeds at once."""
    
    def scrape_multiple_feeds(
        feed_urls: List[str] = Field(description="List of RSS feed URLs to scrape"),
        max_items_per_feed: int = Field(default=5, description="Max items per feed"),
        hours_back: int = Field(default=24, description="Only get items from last N hours")
    ) -> Dict:
        """
        Scrape multiple RSS feeds and return combined results.
        
        Args:
            feed_urls: List of RSS feed URLs to scrape
            max_items_per_feed: Maximum items to get from each feed
            hours_back: Only return items from the last N hours
            
        Returns:
            Combined results from all feeds with source information
        """
        all_items = []
        feed_results = {}
        
        # Get the single feed scraper
        single_scraper = rss_feed_scraper_tool()
        
        for feed_url in feed_urls:
            result = single_scraper(feed_url, max_items_per_feed, hours_back)
            
            if "error" in result:
                feed_results[feed_url] = {"error": result["error"]}
            else:
                feed_results[feed_url] = {
                    "success": True,
                    "feed_title": result["feed_title"],
                    "items_count": result["items_count"]
                }
                all_items.extend(result["items"])
        
        # Sort by published date (newest first) - handle None values
        def get_sort_key(item):
            published = item.get('published', '')
            # If published is None or empty, put at the end
            if not published:
                return ''
            return published
        
        try:
            all_items.sort(key=get_sort_key, reverse=True)
        except Exception:
            # If sorting fails, just continue without sorting
            pass
        
        return {
            "success": True,
            "total_items": len(all_items),
            "feeds_processed": len(feed_urls),
            "feed_results": feed_results,
            "items": all_items
        }
    
    scrape_multiple_feeds.__name__ = "scrape_multiple_feeds"
    scrape_multiple_feeds.__doc__ = "Scrape multiple RSS feeds and return combined results"
    
    return scrape_multiple_feeds


def rss_search_tool():
    """Create tool to search within RSS feed content."""
    
    def search_rss_content(
        feed_url: str = Field(description="RSS feed URL to search"),
        search_terms: List[str] = Field(description="Keywords to search for"),
        max_items: int = Field(default=20, description="Maximum items to search through"),
        hours_back: int = Field(default=48, description="Search in items from last N hours")
    ) -> Dict:
        """
        Search for specific keywords within RSS feed content.
        
        Args:
            feed_url: RSS feed URL to search
            search_terms: List of keywords to search for
            max_items: Maximum items to search through
            hours_back: Search in items from the last N hours
            
        Returns:
            Items that match the search terms
        """
        # Get items from RSS feed
        scraper = rss_feed_scraper_tool()
        result = scraper(feed_url, max_items, hours_back)
        
        if "error" in result:
            return result
        
        matching_items = []
        
        for item in result["items"]:
            # Search in title and description
            title_lower = item["title"].lower()
            desc_lower = item["description"].lower()
            
            for term in search_terms:
                term_lower = term.lower()
                if term_lower in title_lower or term_lower in desc_lower:
                    # Add search context
                    item["matched_term"] = term
                    matching_items.append(item)
                    break  # Don't add the same item multiple times
        
        return {
            "success": True,
            "search_terms": search_terms,
            "total_searched": result["items_count"],
            "matches_found": len(matching_items),
            "items": matching_items
        }
    
    search_rss_content.__name__ = "search_rss_content"
    search_rss_content.__doc__ = "Search for keywords within RSS feed content"
    
    return search_rss_content


# Popular RSS feeds for testing
POPULAR_NEWS_FEEDS = {
    "bbc_news": "http://feeds.bbci.co.uk/news/rss.xml",
    "cnn_top": "http://rss.cnn.com/rss/edition.rss",
    "reuters": "https://www.reuters.com/rssFeed/topNews",
    "techcrunch": "https://techcrunch.com/feed/",
    "hacker_news": "https://hnrss.org/frontpage"
}
