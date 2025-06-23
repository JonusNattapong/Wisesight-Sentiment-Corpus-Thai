import os
import json
import time
import re
import random
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Union # Added Union back for completeness
from bs4 import BeautifulSoup
import asyncio

from dotenv import load_dotenv # Moved to top

# --- Playwright for complex JS websites ---
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# --- yt-dlp for YouTube ---
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    # Functions using yt_dlp will need to check this flag or handle ImportError

# --- Crawl4AI for general web crawling ---
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.models import CrawlResult
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    # Warning will be printed if the function is called without the library

# --- Pandas for CSV output ---
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Load environment variables
load_dotenv()

# Get API keys (now optional)
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

# --- Helper: Proxy rotation, User-Agent randomization, Delay ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]
def get_random_user_agent():
    return random.choice(USER_AGENTS)

def delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def get_proxies():
    # Example: return a list of proxies, or [] if not used
    return []

def get_random_proxy():
    proxies = get_proxies()
    return random.choice(proxies) if proxies else None

# --- Playwright fetch ---
def fetch_with_playwright(url, wait_selector=None, timeout=30000, user_agent=None, headless=True, wait_until="networkidle", scroll_to_load_all=False):
    """Enhanced Playwright fetch with better page interaction and privacy protection"""
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError("playwright is not installed. Please install it with: pip install playwright")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=user_agent or get_random_user_agent(),
            viewport={'width': 1280, 'height': 1024},
            # Add privacy protection
            extra_http_headers={
                'DNT': '1',  # Do Not Track
                'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8'
            }
        )
        
        page = context.new_page()
        try:
            # Reduced timeout for Facebook to prevent hanging
            actual_timeout = timeout
            if "facebook.com" in url:
                actual_timeout = min(timeout, 15000)  # Max 15 seconds for Facebook
                print(f"[INFO] Using reduced timeout ({actual_timeout/1000}s) for Facebook")
            
            page.goto(url, timeout=actual_timeout, wait_until=wait_until)
            
            if wait_selector:
                try:
                    print(f"[DEBUG] Waiting for selector: {wait_selector}")
                    page.wait_for_selector(wait_selector, timeout=actual_timeout)
                except Exception as e:
                    print(f"[WARN] Selector wait timeout: {e}")            # Enhanced scrolling for loading all content
            if scroll_to_load_all and ("pantip.com" in url or "youtube.com" in url):
                platform_name = "Pantip" if "pantip.com" in url else "YouTube"
                print(f"[DEBUG] Loading all comments with enhanced scrolling for {platform_name}...")
                
                # Special handling for YouTube
                if "youtube.com" in url:
                    # First, scroll to comments section and activate it
                    try:
                        print("[DEBUG] Activating YouTube comments section...")
                        # Try multiple ways to get to comments
                        page.evaluate("""
                            // Scroll to comments section
                            const comments = document.querySelector('#comments, ytd-comments, #comment-teaser');
                            if (comments) {
                                comments.scrollIntoView({behavior: 'smooth'});
                            }
                            
                            // Wait a bit
                            setTimeout(() => {
                                // Click on comments to activate lazy loading
                                const clickTargets = document.querySelectorAll('#comments, ytd-comments, #comment-teaser, ytd-item-section-renderer');
                                clickTargets.forEach(target => {
                                    try { target.click(); } catch(e) {}
                                });
                            }, 1000);
                        """)
                        delay(3, 4)  # Wait for activation
                    except Exception as e:
                        print(f"[DEBUG] Comments activation failed: {e}")
                
                # Get initial height and comment count
                previous_height = page.evaluate("document.body.scrollHeight")
                previous_comment_count = 0
                
                # Scroll multiple times to load lazy content
                max_scrolls = 25 if "youtube.com" in url else 10  # Much more scrolls for YouTube
                no_change_count = 0
                successful_scrolls = 0
                
                for scroll_num in range(max_scrolls):
                    try:
                        # Scroll down gradually
                        page.evaluate("""
                            const scrollStep = window.innerHeight * 0.8;
                            window.scrollBy(0, scrollStep);                        """)
                        
                        # Wait for content to load
                        wait_time = (3, 5) if "youtube.com" in url else (2, 3)
                        delay(*wait_time)
                        
                        # For YouTube, try to trigger more comments loading
                        if "youtube.com" in url and scroll_num % 3 == 0:
                            try:
                                # Count current comments
                                current_comment_count = page.evaluate("""() => {
                                    const commentSelectors = [
                                        '#content-text',
                                        'ytd-comment-renderer #content-text',
                                        'ytd-comment-thread-renderer #content-text'
                                    ];
                                    let total = 0;
                                    commentSelectors.forEach(selector => {
                                        total += document.querySelectorAll(selector).length;
                                    });
                                    return total;
                                }""")
                                
                                if current_comment_count > previous_comment_count:
                                    print(f"[DEBUG] Comments loaded: {current_comment_count} (+{current_comment_count - previous_comment_count})")
                                    previous_comment_count = current_comment_count
                                    successful_scrolls += 1
                                    no_change_count = 0
                                else:
                                    no_change_count += 1
                                    
                            except Exception as e:
                                print(f"[DEBUG] Comment counting failed: {e}")
                        
                        # Check if new content loaded
                        new_height = page.evaluate("document.body.scrollHeight")
                        
                        if new_height == previous_height:
                            no_change_count += 1
                            print(f"[DEBUG] Scroll {scroll_num + 1}: No new content")
                        else:
                            no_change_count = 0
                            print(f"[DEBUG] Scroll {scroll_num + 1}: New content loaded ({new_height - previous_height} pixels)")
                            previous_height = new_height
                            successful_scrolls += 1
                            
                        # Advanced button clicking for YouTube
                        if "youtube.com" in url:
                            try:
                                clicked_something = page.evaluate("""() => {
                                    const buttonSelectors = [
                                        'button:has-text("Show more replies")',
                                        'button:has-text("โหลดเพิ่ม")',
                                        'button:has-text("แสดงเพิ่ม")',
                                        'button:has-text("Load more")',
                                        'button:has-text("Show more")',
                                        'ytd-continuation-item-renderer button',
                                        '#more-replies',
                                        '.load-more-button',
                                        '.show-more-button',
                                        'paper-button[role="button"]',
                                        '[role="button"]:has-text("more")',
                                        '[role="button"]:has-text("เพิ่ม")'
                                    ];
                                    
                                    let clicked = false;
                                    for (const selector of buttonSelectors) {
                                        try {
                                            const buttons = document.querySelectorAll(selector);
                                            for (const button of buttons) {
                                                if (button.offsetParent !== null) { // Visible element
                                                    button.click();
                                                    clicked = true;
                                                    break;
                                                }
                                            }
                                            if (clicked) break;
                                        } catch (e) {}
                                    }
                                    return clicked;
                                }""")
                                
                                if clicked_something:
                                    print(f"[DEBUG] Clicked load more button")
                                    delay(3, 4)  # Wait after clicking
                                    
                            except Exception as e:
                                print(f"[DEBUG] Button clicking failed: {e}")
                        
                        # If no new content for several consecutive scrolls, try one more aggressive approach
                        if no_change_count >= 4:
                            if "youtube.com" in url and scroll_num < max_scrolls - 5:
                                print("[DEBUG] Trying aggressive comment loading...")
                                try:
                                    # Force all lazy elements to load
                                    page.evaluate("""
                                        // Trigger intersection observer for all elements
                                        const elements = document.querySelectorAll('ytd-continuation-item-renderer, lazy-list-renderer, ytd-comment-thread-renderer');
                                        elements.forEach(el => {
                                            el.scrollIntoView();
                                            // Trigger events
                                            ['scroll', 'wheel', 'touchstart'].forEach(eventType => {
                                                el.dispatchEvent(new Event(eventType, {bubbles: true}));
                                            });
                                        });
                                    """)
                                    delay(4, 6)
                                    no_change_count = 0  # Reset counter after aggressive attempt
                                except:
                                    pass
                            else:
                                print("[DEBUG] No more content to load")
                                break
                                
                    except Exception as e:
                        print(f"[DEBUG] Scroll error: {e}")
                        continue
                
                print(f"[DEBUG] Scrolling completed. Successful scrolls: {successful_scrolls}")
                
            else:
                # Original scrolling behavior for other platforms
                scroll_attempts = 1 if "facebook.com" in url else 3
                for _ in range(scroll_attempts):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    delay(0.5, 1)  # Shorter delay for Facebook
                
            html = page.content()
            
        except Exception as e:
            print(f"[ERROR] Page interaction failed: {e}")
            html = ""
            
        finally:
            context.close()
            browser.close()
            
        return html

def extract_twitter_data(url, fetch_profile=False):
    """Extract data from Twitter/X posts using enhanced Playwright"""
    html = fetch_with_playwright(
        url, 
        wait_selector="article[data-testid='tweet']",
        timeout=45000,  # Increased timeout
        wait_until="networkidle"
    )
    
    if not html:
        print("[ERROR] Failed to fetch page content")
        return {}
        
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    
    try:
        # Updated selectors for X's UI
        tweet_selectors = [
            "article[data-testid='tweet'] div[data-testid='tweetText']",
            "article div[lang]",  # Broader tweet text selector
            "div[data-testid='tweetText']"  # Direct tweet text
        ]
        
        # Extract main tweet
        main_tweet = None
        for selector in tweet_selectors:
            tweets = soup.select(selector)
            if tweets:
                main_tweet = tweets[0]
                break
                
        if main_tweet:
            # Clean and store tweet text
            text = main_tweet.get_text(strip=True)
            if text:
                data["tweet"] = text
                print(f"[DEBUG] Found main tweet: {text[:100]}...")
                
            # Get author info
            author_container = soup.select_one("div[data-testid='User-Name']")
            if author_container:
                data["profile"] = author_container.get_text(strip=True)
                print(f"[DEBUG] Found author: {data['profile']}")
        
        # Extract replies - using multiple passes with different selectors
        replies = []
        seen_texts = set()
        
        # First try specific reply selectors
        reply_containers = soup.select("article[data-testid='tweet']:not(:first-child)")
        
        if not reply_containers:
            # Fallback to broader selectors
            reply_containers = soup.select("div[data-testid='cellInnerDiv']")
        
        print(f"[DEBUG] Found {len(reply_containers)} potential replies")
        
        for container in reply_containers:
            try:
                # Try multiple text selectors
                text_element = (
                    container.select_one("div[data-testid='tweetText']") or
                    container.select_one("div[lang]") or
                    container.select_one("div[dir='auto']")
                )
                
                if not text_element:
                    continue
                    
                text = text_element.get_text(strip=True)
                
                # Skip if empty, too short, or duplicate
                if not text or len(text) < 2 or text in seen_texts:
                    continue
                
                # Skip if it matches the main tweet
                if data.get("tweet") == text:
                    continue
                
                # Get author with fallbacks
                author = "Unknown"
                author_el = (
                    container.select_one("div[data-testid='User-Name']") or
                    container.select_one("a[role='link'] div[dir='auto']")
                )
                if author_el:
                    author = author_el.get_text(strip=True)
                
                replies.append({
                    "text": text,
                    "author": author
                })
                seen_texts.add(text)
                
            except Exception as e:
                print(f"[WARN] Error extracting reply: {e}")
                continue
        
        data["replies"] = replies
        print(f"[INFO] Successfully extracted {len(replies)} replies")
        
    except Exception as e:
        print(f"[ERROR] Failed to extract Twitter data: {e}")
    
    return data

# --- Facebook ---
def extract_facebook_data(url, fetch_profile=False):
    """Extract data from Facebook posts using Playwright"""
    html = fetch_with_playwright(
        url, 
        wait_selector="[role='article'], [role='main']",
        timeout=30000
    )
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    
    try:
        # Extract main post text with better selectors
        post_selectors = [
            # Main post content selectors
            "div[data-ad-preview='message']",
            "div[data-ad-comet-preview='message']",
            "div.xdj266r", 
            "div[dir='auto']:not([aria-hidden='true'])"
        ]
        
        for selector in post_selectors:
            post = soup.select_one(selector)
            if post and post.get_text(strip=True):
                # Filter out metadata text
                text = post.get_text(strip=True)
                if not any(x in text.lower() for x in [
                    "ความรู้สึก", "แชร์", "ครั้ง", "comments",
                    "likes", "shares", "view", "ความคิดเห็น"
                ]):
                    data["post"] = text
                    break
        
        # Extract comments with better filtering
        comments = []
        seen_texts = set()  # Track unique comments
        
        comment_containers = soup.select("div.x1y1aw1k, ul[role='list'] > li")
        for container in comment_containers:
            try:
                # Find comment text
                text_elements = container.select(
                    "div[dir='auto']:not([aria-hidden='true'])"
                )
                
                for element in text_elements:
                    text = element.get_text(strip=True)
                    
                    # Skip if empty, too short, or duplicate
                    if not text or len(text) < 2 or text in seen_texts:
                        continue
                        
                    # Skip metadata/UI text
                    if any(x in text.lower() for x in [
                        "ความรู้สึก", "แชร์", "ครั้ง", "comments",
                        "likes", "shares", "view", "ความคิดเห็น",
                        "ผู้เขียน", "ตอบกลับ", "reply", "author"
                    ]):
                        continue
                    
                    # Find author (look for nearest link with role='link')
                    author = "Unknown"
                    author_el = container.find_previous(
                        lambda tag: tag.name == "a" 
                        and tag.get("role") == "link"
                        and not tag.select_one("img")  # Exclude profile picture links
                    )
                    if author_el:
                        author = author_el.get_text(strip=True)
                    
                    comments.append({
                        "text": text,
                        "author": author
                    })
                    seen_texts.add(text)
                    
            except Exception as e:
                print(f"[WARN] Error extracting comment: {e}")
                continue
        
        data["comments"] = comments
        
        # Extract profile info if requested
        if fetch_profile:
            profile_selectors = [
                "a[aria-current='page']",
                "h2 strong span",
                "a[role='link'][tabindex='0']"
            ]
            for selector in profile_selectors:
                profile = soup.select_one(selector)
                if profile:
                    data["profile"] = profile.get_text(strip=True)
                    break
    
    except Exception as e:
        print(f"[WARN] Error extracting Facebook data: {e}")
    
    return data

# Function to help fill missing data
def refill_facebook_comments(url: str, max_retries: int = 3) -> List[Dict[str, Any]]:
    """Try to get more comments with multiple retries"""
    attempts = 0
    comments = []
    
    while attempts < max_retries and len(comments) < 1:
        try:
            data = extract_facebook_data(url)
            if data.get("comments"):
                comments.extend(data["comments"])
            attempts += 1
            time.sleep(2)  # Wait between retries
        except Exception:
            attempts += 1
            
    return comments

# --- Twitter/X ---
def extract_twitter_data(url, fetch_profile=False):
    """Extract data from Twitter/X posts using enhanced Playwright"""
    html = fetch_with_playwright(
        url, 
        wait_selector="article[data-testid='tweet']",
        timeout=45000,  # Increased timeout
        wait_until="networkidle"
    )
    
    if not html:
        print("[ERROR] Failed to fetch page content")
        return {}
        
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    
    try:
        # Updated selectors for X's UI
        tweet_selectors = [
            "article[data-testid='tweet'] div[data-testid='tweetText']",
            "article div[lang]",  # Broader tweet text selector
            "div[data-testid='tweetText']"  # Direct tweet text
        ]
        
        # Extract main tweet
        main_tweet = None
        for selector in tweet_selectors:
            tweets = soup.select(selector)
            if tweets:
                main_tweet = tweets[0]
                break
                
        if main_tweet:
            # Clean and store tweet text
            text = main_tweet.get_text(strip=True)
            if text:
                data["tweet"] = text
                print(f"[DEBUG] Found main tweet: {text[:100]}...")
                
            # Get author info
            author_container = soup.select_one("div[data-testid='User-Name']")
            if author_container:
                data["profile"] = author_container.get_text(strip=True)
                print(f"[DEBUG] Found author: {data['profile']}")
        
        # Extract replies - using multiple passes with different selectors
        replies = []
        seen_texts = set()
        
        # First try specific reply selectors
        reply_containers = soup.select("article[data-testid='tweet']:not(:first-child)")
        
        if not reply_containers:
            # Fallback to broader selectors
            reply_containers = soup.select("div[data-testid='cellInnerDiv']")
        
        print(f"[DEBUG] Found {len(reply_containers)} potential replies")
        
        for container in reply_containers:
            try:
                # Try multiple text selectors
                text_element = (
                    container.select_one("div[data-testid='tweetText']") or
                    container.select_one("div[lang]") or
                    container.select_one("div[dir='auto']")
                )
                
                if not text_element:
                    continue
                    
                text = text_element.get_text(strip=True)
                
                # Skip if empty, too short, or duplicate
                if not text or len(text) < 2 or text in seen_texts:
                    continue
                
                # Skip if it matches the main tweet
                if data.get("tweet") == text:
                    continue
                
                # Get author with fallbacks
                author = "Unknown"
                author_el = (
                    container.select_one("div[data-testid='User-Name']") or
                    container.select_one("a[role='link'] div[dir='auto']")
                )
                if author_el:
                    author = author_el.get_text(strip=True)
                
                replies.append({
                    "text": text,
                    "author": author
                })
                seen_texts.add(text)
                
            except Exception as e:
                print(f"[WARN] Error extracting reply: {e}")
                continue
        
        data["replies"] = replies
        print(f"[INFO] Successfully extracted {len(replies)} replies")
        
    except Exception as e:
        print(f"[ERROR] Failed to extract Twitter data: {e}")
    
    return data

async def extract_twitter_with_crawl4ai(tweet_url: str, include_sentiment: bool = False) -> Optional[List[Dict[str, Any]]]:
    """Extract Twitter/X post and replies using Crawl4AI"""
    if not CRAWL4AI_AVAILABLE:
        return None

    try:
        # Configure browser
        browser_config = BrowserConfig(
            headless=True,
            slow_mo=50,
            viewport={'width': 1280, 'height': 720}
        )
        
        # Configure extraction
        run_config = CrawlerRunConfig(
            wait_for_selectors=["article[data-testid='tweet']"],
            click_selectors=[
                "div[role='button']",  # More replies
                "span[role='button']"   # Show replies
            ],
            wait_for_scroll_bottom=True,
            scroll_timeout=10000,
            extract_rules={
                'main_tweet': {
                    'selector': "article[data-testid='tweet']:first-child",
                    'fields': {
                        'text': {'selector': "div[data-testid='tweetText']", 'type': 'text'},
                        'author': {'selector': "div[data-testid='User-Name']", 'type': 'text'},
                        'time': {'selector': "time", 'type': 'text'}
                    }
                },
                'replies': {
                    'selector': "article[data-testid='tweet']:not(:first-child)",
                    'type': 'list',
                    'fields': {
                        'text': {'selector': "div[data-testid='tweetText']", 'type': 'text'},
                        'author': {'selector': "div[data-testid='User-Name']", 'type': 'text'},
                        'time': {'selector': "time", 'type': 'text'}
                    }
                }
            }
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=tweet_url, config=run_config)
            
            if not result or not result.extracted_content:
                return None

            content = result.extracted_content
            comments = []

            # Add main tweet
            if content.get('main_tweet'):
                main_tweet = {
                    "text": sanitize_text(content['main_tweet'].get('text', '')),
                    "created_at": datetime.now().isoformat(),
                    "platform": "twitter",
                    "post_url": tweet_url,
                    "post_type": "tweet",
                    "author": content['main_tweet'].get('author', 'Unknown'),
                    "timestamp": content['main_tweet'].get('time', ''),
                    "is_spam": False
                }
                if include_sentiment:
                    main_tweet["sentiment"] = analyze_sentiment(main_tweet["text"])
                comments.append(main_tweet)

            # Add replies
            for reply in content.get('replies', []):
                if not reply.get('text'):
                    continue
                
                entry = {
                    "text": sanitize_text(reply['text']),
                    "created_at": datetime.now().isoformat(),
                    "platform": "twitter",
                    "post_url": tweet_url,
                    "post_type": "reply",
                    "author": reply.get('author', 'Unknown'),
                    "timestamp": reply.get('time', ''),
                    "is_spam": False
                }
                
                if include_sentiment:
                    entry["sentiment"] = analyze_sentiment(entry["text"])
                
                comments.append(entry)

            return comments

    except Exception as e:
        print(f"[ERROR] Crawl4AI Twitter/X extraction failed: {e}")
        return None

def extract_twitter_comments(
    url: str,
    max_results: int = 100,
    include_sentiment: bool = False,
    **kwargs  # Add kwargs to handle additional parameters like lang
) -> List[Dict[str, Any]]:
    """Extract comments from Twitter/X posts
    
    Args:
        url: Tweet URL
        max_results: Maximum number of comments to return
        include_sentiment: Whether to perform sentiment analysis
        **kwargs: Additional parameters (e.g., lang)
    """
    try:
        # Try Crawl4AI first if available
        if CRAWL4AI_AVAILABLE:
            print("[INFO] Attempting to use Crawl4AI for Twitter/X...")
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except (ImportError, RuntimeError):
                pass
            
            posts = asyncio.run(extract_twitter_with_crawl4ai(url, include_sentiment))
            if posts:
                print(f"[INFO] Successfully extracted {len(posts)} tweets/replies using Crawl4AI")
                return posts[:max_results]
            print("[INFO] Crawl4AI extraction failed, falling back to Playwright...")

        # Fall back to Playwright method
        print("[INFO] Using Playwright for Twitter/X extraction...")
        data = extract_twitter_data(url)
        comments = []

        # Add main tweet
        if "tweet" in data:
            main_tweet = {
                "text": sanitize_text(data["tweet"]),
                "created_at": datetime.now().isoformat(),
                "platform": "twitter",
                "post_url": url,
                "post_type": "tweet",
                "author": data.get("profile", "Unknown"),
                "is_spam": False
            }
            if include_sentiment:
                main_tweet["sentiment"] = analyze_sentiment(main_tweet["text"])
            comments.append(main_tweet)

        # Add replies
        for reply in data.get("replies", []):
            if not reply.get("text"):
                continue
            
            entry = {
                "text": sanitize_text(reply["text"]),
                "created_at": datetime.now().isoformat(),
                "platform": "twitter",
                "post_url": url,
                "post_type": "reply",
                "author": reply.get("author", "Unknown"),
                "is_spam": False
            }
            
            if include_sentiment:
                entry["sentiment"] = analyze_sentiment(entry["text"])
            
            comments.append(entry)

        print(f"[INFO] Extracted {len(comments)} tweets/replies using Playwright")
        return comments[:max_results]

    except Exception as e:
        print(f"[ERROR] Failed to extract Twitter/X comments: {e}")
        return []

# --- Instagram ---
def extract_instagram_data(url, fetch_profile=False):
    html = fetch_with_playwright(url, wait_selector="article")
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    # Example: extract post caption
    caption = soup.select_one("div[role='button'] ~ div > span")
    if caption:
        data["caption"] = caption.get_text(strip=True)
    # Example: extract comments
    comments = []
    for c in soup.select("ul ul > div > li > div > div > div > span"):
        text = c.get_text(strip=True)
        if text:
            comments.append({"text": text})
    data["comments"] = comments
    # Example: extract profile
    if fetch_profile:
        profile = soup.select_one("header a")
        if profile:
            data["profile"] = profile.get_text(strip=True)
    return data

# --- Reddit ---
def extract_reddit_data(url, fetch_profile=False):
    html = fetch_with_playwright(url, wait_selector="div[data-test-id='post-content']")
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    # Example: extract post
    post = soup.select_one("div[data-test-id='post-content']")
    if post:
        data["post"] = post.get_text(separator="\n", strip=True)
    # Example: extract comments
    comments = []
    for c in soup.select("div[data-test-id='comment']"):
        text = c.get_text(separator="\n", strip=True)
        if text:
            comments.append({"text": text})
    data["comments"] = comments
    # Example: extract profile
    if fetch_profile:
        profile = soup.select_one("a[data-click-id='user']")
        if profile:
            data["profile"] = profile.get_text(strip=True)
    return data

# --- YouTube (yt-dlp) ---
def extract_youtube_data(url, fetch_profile=False, download_video=False):
    if not YTDLP_AVAILABLE:
        print("[ERROR] yt-dlp library is not installed. Please install it: pip install yt-dlp")
        return None
    ydl_opts = {
        "quiet": True,
        "skip_download": not download_video,
        "extract_flat": False,
        "forcejson": True,
        "dump_single_json": True,
        "writesubtitles": False,
        "writeinfojson": True,
        "writeautomaticsub": False,
        "nocheckcertificate": True,
        "proxy": get_random_proxy(),
        "user_agent": get_random_user_agent(),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=download_video)
    return info

# --- Unified interface ---
def extract_social_data(platform, url, fetch_profile=False, download_video=False):
    """
    Unified interface to extract post/comments/profile from supported platforms.
    """
    delay(1, 3)  # Respectful delay
    if platform == "facebook":
        return extract_facebook_data(url, fetch_profile=fetch_profile)
    elif platform in ["twitter", "x"]:
        return extract_twitter_data(url, fetch_profile=fetch_profile)
    elif platform == "instagram":
        return extract_instagram_data(url, fetch_profile=fetch_profile)
    elif platform == "reddit":
        return extract_reddit_data(url, fetch_profile=fetch_profile)
    elif platform == "youtube":
        return extract_youtube_data(url, fetch_profile=fetch_profile, download_video=download_video)
    else:
        raise ValueError(f"Platform '{platform}' not supported.")

# --- Legal & Ethical best practices ---
# - Always check and comply with each site's Terms of Service.
# - Use rate limiting and delays (e.g., time.sleep) between requests.
# - Respect robots.txt.
# - Use proxy rotation and random user agents for scraping.
# - Never overload or harm target servers.

# Helper function to sanitize text
def sanitize_text(text: str, remove_personal_info: bool = True) -> str:
    """Clean text from unwanted characters and formatting with privacy protection"""
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    if remove_personal_info:
        # Remove potential phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        text = re.sub(r'\b0\d{8,9}\b', '[PHONE]', text)  # Thai phone format
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Remove Line IDs
        text = re.sub(r'line\s*id\s*[:=]\s*\w+', '[LINE_ID]', text, flags=re.IGNORECASE)
        text = re.sub(r'@\w+', '[SOCIAL_ID]', text)
        
        # Remove potential addresses (Thai)
        text = re.sub(r'\d+/\d+.*?(ตำบล|อำเภอ|จังหวัด)', '[ADDRESS]', text)
    
    # Fix spacing
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def spam_filter(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out spam comments using basic heuristics"""
    filtered = []
    spam_patterns = [
        # Common spam patterns (Thai and English)
        r'ดูได้ที่|click here|คลิกเลย',
        r'line\s*id|line\s*@|ไลน์',
        r'\d{3,}.*\d{3,}',  # Multiple numbers (e.g., phone numbers)
        r'www\.|\.com|\.net|http|bit\.ly',
        r'ผลิตภัณฑ์|สนใจติดต่อ|สั่งซื้อ',
        r'ราคา.*บาท|บาท.*ราคา',
        r'promotion|โปรโมชั่น|ส่วนลด',
        r'vip|premium|member',
        r'subscribe|สมัครสมาชิก',
        r'free|ฟรี',
        r'casino|เว็บพนัน|บาคาร่า|สล็อต',
        r'viagra|ยาเพิ่ม',
        r'weight.*loss|ลดน้ำหนัก|ลดความอ้วน',
        # Add more patterns as needed
    ]
    
    # Combine patterns
    spam_regex = re.compile('|'.join(spam_patterns), re.IGNORECASE)
    
    for comment in comments:
        text = comment.get('text', '').lower()
        
        # Skip empty comments
        if not text:
            continue
            
        # Check for spam patterns
        if spam_regex.search(text):
            comment['is_spam'] = True
            continue
            
        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[!@#$%^&*()_+=\[\]{};:"/\\|,.<>?~\d]', text)) / len(text)
        if special_char_ratio > 0.3:  # More than 30% special characters
            comment['is_spam'] = True
            continue
            
        # Check for repetitive characters
        if re.search(r'(.)\1{4,}', text):  # Same character repeated 5+ times
            comment['is_spam'] = True
            continue
            
        # Check for very short or very long comments
        if len(text) < 5 or len(text) > 5000:
            comment['is_spam'] = True
            continue
        
        # Not spam
        comment['is_spam'] = False
        filtered.append(comment)
    
    return filtered

def analyze_sentiment(text: str, lang: str = "th") -> str:
    """
    Basic sentiment analysis for Thai and English text
    
    Args:
        text: Text to analyze
        lang: Language code ("th" for Thai, "en" for English)
        
    Returns:
        Sentiment label ("positive", "negative", "neutral")
    """
    # Lowercased text for matching
    text_lower = text.lower()
    
    # Thai and English positive/negative word lists
    pos_words = {
        # Thai positive words
        "ดี", "เยี่ยม", "สุดยอด", "ชอบ", "สนุก", "รัก", "ขอบคุณ", 
        "ยอดเยี่ยม", "เก่ง", "น่ารัก", "เจ๋ง", "ว้าว", "โคตรดี",
        "ประทับใจ", "พอใจ", "สวย", "เลิศ",
        # English positive words
        "good", "great", "excellent", "happy", "love", "awesome",
        "perfect", "thanks", "amazing", "wonderful", "best"
    }
    
    neg_words = {
        # Thai negative words
        "แย่", "เลว", "ไม่ดี", "เกลียด", "น่าเบื่อ", "น่ารำคาญ",
        "ผิดหวัง", "เสียใจ", "โกรธ", "ไม่พอใจ", "แย่มาก",
        # English negative words
        "bad", "awful", "terrible", "sad", "hate", "poor", "boring",
        "worst", "horrible", "disappointing"
    }
    
    # Special cases for Thai
    if "555" in text or "ฮ่าๆ" in text or "😂" in text or "🤣" in text:
        return "positive"
    
    if "❤️" in text or "❤" in text or "👍" in text:
        return "positive"
        
    if "👎" in text or "😡" in text or "🤬" in text:
        return "negative"
    
    # Count positive and negative words
    pos_count = sum(1 for word in pos_words if word in text_lower)
    neg_count = sum(1 for word in neg_words if word in text_lower)
    
    # Determine sentiment
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    else:
        return "neutral"

def advanced_thai_sentiment_analysis(text: str) -> Dict[str, Any]:
    """
    Advanced Thai sentiment analysis with comprehensive schema
    
    Args:
        text: Thai text to analyze
        
    Returns:
        Dictionary with detailed sentiment analysis including emotion, intent, intensity, context
    """
    text_lower = text.lower()
    
    # Emotion mapping patterns
    emotion_patterns = {
        "joy": {
            "keywords": ["ดีใจ", "สุข", "ปลื้ม", "ยินดี", "เฮง", "555", "ฮ่าๆ", "เจ๋ง", "สุดยอด", "เยี่ยม"],
            "emojis": ["😊", "😁", "😂", "🤣", "😆", "🥳", "❤️", "👍"]
        },
        "sadness": {
            "keywords": ["เศร้า", "เสียใจ", "น่าเศร้า", "ใจเสีย", "ท้อ", "หดหู่", "ผิดหวัง"],
            "emojis": ["😢", "😭", "😔", "💔", "😞"]
        },
        "anger": {
            "keywords": ["โกรธ", "เกลียด", "ห่วยแตก", "แย่", "น่ารำคาญ", "เลว", "บ้า", "ฟาด"],
            "emojis": ["😡", "🤬", "😠", "👎"]
        },
        "fear": {
            "keywords": ["กลัว", "เครียด", "วิตก", "กังวล", "ตื่น", "หวาดเสีย", "ตกใจ"],
            "emojis": ["😰", "😨", "😱", "😟"]
        },
        "excited": {
            "keywords": ["ตื่นเต้น", "ว้าว", "มาก", "สุดๆ", "โคตร", "วิ้ง", "อีหยัง"],
            "emojis": ["🤩", "😍", "🔥", "⚡"]
        },
        "neutral": {
            "keywords": ["ปกติ", "ธรรมดา", "โอเค", "พอ", "ใช้ได้"],
            "emojis": ["😐", "😶"]
        }
    }
    
    # Intent mapping patterns
    intent_patterns = {
        "question": {
            "keywords": ["ไหม", "หรือ", "เหรอ", "ไง", "อะไร", "ทำไม", "อย่างไร", "เมื่อไหร่", "ที่ไหน", "ใคร"],
            "punctuation": ["?", "？"]
        },
        "request": {
            "keywords": ["ช่วย", "กรุณา", "โปรด", "ขอ", "ได้ไหม", "หน่อย", "ดัง", "นะ"],
            "context": ["ได้ไหม", "หน่อยนะ", "กรุณา"]
        },
        "complain": {
            "keywords": ["แย่", "ห่วย", "เลว", "ไม่ดี", "น่ารำคาญ", "ผิดหวัง", "เกลียด"],
            "context": ["ไม่ควร", "ไม่น่า", "แย่มาก"]
        },
        "praise": {
            "keywords": ["ดี", "เยี่ยม", "สุดยอด", "เก่ง", "น่ารัก", "ประทับใจ", "ชอบ"],
            "context": ["ดีจัง", "เยี่ยมมาก", "สุดยอดเลย"]
        },
        "sarcasm": {
            "keywords": ["อ่อ", "เหรอ", "จริงๆ", "555", "ล้อเล่น"],
            "patterns": ["อ่อ.*ดี", "จริงๆ.*เนอะ", "ใช่.*มั้ง", "แน่นอน.*จัง"]
        },
        "inform": {
            "keywords": ["คือ", "เป็น", "มี", "ได้", "จะ", "แล้ว", "กำลัง"],
            "default": True  # Default intent if no others match
        }
    }
    
    # Context patterns
    context_patterns = {
        "formal": ["ครับ", "ค่ะ", "คะ", "ขอแสดงความนับถือ", "ด้วยความเคารพ", "กรุณา"],
        "informal": ["555", "ฮ่า", "อ่ะ", "นะ", "วะ", "เฮ้ย", "ไอ้", "โว้ย"],
        "slang": ["โคตร", "ปัง", "ชิล", "เฟล", "เบร็ค", "แจ่ม", "เจ๋ง"],
        "personal": ["ฉัน", "กู", "มึง", "เรา", "กัน", "ตัว"]
    }
    
    # Intensity indicators
    intensity_high = ["มาก", "โคตร", "สุด", "ปัง", "แรง", "เลว", "ห่วย", "แจ่ม"]
    intensity_medium = ["ค่อนข้าง", "พอสมควร", "ปานกลาง", "นิดหน่อย"]
    intensity_low = ["เล็กน้อย", "นิดเดียว", "หน่อย", "เบาๆ"]
    
    # Analysis
    result = {
        "text": text,
        "emotion": "neutral",
        "intent": "inform",
        "intensity": "medium",
        "context": "informal",
        "target": None,
        "sentiment_score": 0.0,
        "notes": ""
    }
    
    # Detect emotion
    emotion_scores = {}
    for emotion, patterns in emotion_patterns.items():
        score = 0
        # Check keywords
        for keyword in patterns["keywords"]:
            if keyword in text_lower:
                score += 1
        # Check emojis
        for emoji in patterns.get("emojis", []):
            if emoji in text:
                score += 1
        emotion_scores[emotion] = score
    
    # Select highest scoring emotion
    if emotion_scores:
        result["emotion"] = max(emotion_scores, key=emotion_scores.get)
        if emotion_scores[result["emotion"]] == 0:
            result["emotion"] = "neutral"
    
    # Detect intent
    intent_scores = {}
    for intent, patterns in intent_patterns.items():
        score = 0
        # Check keywords
        for keyword in patterns.get("keywords", []):
            if keyword in text_lower:
                score += 1
        # Check patterns (regex-like)
        for pattern in patterns.get("patterns", []):
            if re.search(pattern, text_lower):
                score += 2
        # Check punctuation
        for punct in patterns.get("punctuation", []):
            if punct in text:
                score += 1
        intent_scores[intent] = score
    
    # Select highest scoring intent
    if intent_scores and max(intent_scores.values()) > 0:
        result["intent"] = max(intent_scores, key=intent_scores.get)
    
    # Detect sarcasm (special case)
    sarcasm_indicators = ["อ่อ", "เหรอ", "จริงๆ เนอะ", "ใช่ๆ", "แน่นอน"]
    if any(indicator in text_lower for indicator in sarcasm_indicators):
        positive_words = ["ดี", "เยี่ยม", "สุดยอด"]
        if any(word in text_lower for word in positive_words):
            result["intent"] = "sarcasm"
            result["emotion"] = "complex"
    
    # Detect intensity
    if any(word in text_lower for word in intensity_high):
        result["intensity"] = "high"
    elif any(word in text_lower for word in intensity_medium):
        result["intensity"] = "medium"
    elif any(word in text_lower for word in intensity_low):
        result["intensity"] = "low"
    
    # Detect context
    if any(word in text_lower for word in context_patterns["formal"]):
        result["context"] = "formal"
    elif any(word in text_lower for word in context_patterns["slang"]):
        result["context"] = "slang"
    elif any(word in text_lower for word in context_patterns["personal"]):
        result["context"] = "personal"
    else:
        result["context"] = "informal"
    
    # Calculate sentiment score
    sentiment_mapping = {
        "joy": 0.8,
        "excited": 0.9,
        "sadness": -0.6,
        "anger": -0.8,
        "fear": -0.4,
        "neutral": 0.0,
        "complex": -0.2  # Slightly negative for sarcasm/complex emotions
    }
    
    base_score = sentiment_mapping.get(result["emotion"], 0.0)
    
    # Adjust by intensity
    intensity_multiplier = {
        "low": 0.5,
        "medium": 1.0,
        "high": 1.5
    }
    
    result["sentiment_score"] = round(
        base_score * intensity_multiplier.get(result["intensity"], 1.0), 2
    )
    
    # Ensure score is within bounds
    result["sentiment_score"] = max(-1.0, min(1.0, result["sentiment_score"]))
    
    # Extract target (simple noun extraction)
    # This is a basic implementation - could be enhanced with NLP libraries
    target_patterns = [
        r'ร้าน\w*', r'อาหาร\w*', r'บริการ\w*', r'สินค้า\w*',
        r'ภาพยนตร์\w*', r'หนัง\w*', r'เพลง\w*', r'คน\w*'
    ]
    
    for pattern in target_patterns:
        match = re.search(pattern, text)
        if match:
            result["target"] = match.group()
            break
    
    # Generate notes
    notes = []
    if result["emotion"] == "complex":
        notes.append("อารมณ์ซับซ้อน")
    if result["intent"] == "sarcasm":
        notes.append("มีความเหน็บแนม")
    if result["intensity"] == "high":
        notes.append("อารมณ์รุนแรง")
    
    result["notes"] = ", ".join(notes) if notes else ""
    
    return result

def batch_advanced_sentiment_analysis(
    comments: List[Dict[str, Any]], 
    text_field: str = "text",
    use_ml: bool = False
) -> List[Dict[str, Any]]:
    """
    Apply advanced sentiment analysis to a batch of comments
    
    Args:
        comments: List of comment dictionaries
        text_field: Field name containing the text to analyze
        use_ml: Whether to use ML-enhanced sentiment analysis
        
    Returns:
        List of comments with added sentiment analysis fields
    """
    enriched_comments = []
    
    for comment in comments:
        if text_field not in comment or not comment[text_field]:
            continue
            
        # Apply appropriate sentiment analysis
        if use_ml:
            sentiment_data = ml_enhanced_sentiment_analysis(comment[text_field], comments)
        else:
            sentiment_data = advanced_thai_sentiment_analysis(comment[text_field])
          # Merge with original comment data
        enriched_comment = comment.copy()
        enriched_comment.update({
            "emotion": sentiment_data["emotion"],
            "intent": sentiment_data["intent"],
            "intensity": sentiment_data["intensity"],
            "context": sentiment_data["context"],
            "target": sentiment_data["target"],
            "sentiment_score": sentiment_data["sentiment_score"],
            "sentiment": sentiment_data.get("sentiment", "neutral"),  # Add sentiment field
            "analysis_notes": sentiment_data["notes"]
        })
        
        # Add ML-specific fields if using ML
        if use_ml and sentiment_data.get('ml_enhanced', False):
            enriched_comment.update({
                "ml_confidence": sentiment_data.get("confidence", 0),
                "ml_probabilities": sentiment_data.get("ml_probabilities", {}),
                "model_type": sentiment_data.get("model_type", "unknown"),
                "ml_enhanced": True
            })
        else:
            enriched_comment["ml_enhanced"] = False
        
        enriched_comments.append(enriched_comment)
    
    return enriched_comments

def save_advanced_sentiment_data(
    comments: List[Dict[str, Any]],
    output_path: str,
    format: str = "jsonl"
) -> str:
    """
    Save comments with advanced sentiment analysis to file
    
    Args:
        comments: List of analyzed comments
        output_path: Output file path
        format: File format ("jsonl", "csv")
        
    Returns:
        Path to saved file
    """
    if not comments:
        print("[WARN] No comments to save")
        return output_path
    
    try:
        if format.lower() == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for comment in comments:
                    f.write(json.dumps(comment, ensure_ascii=False) + "\n")
        
        elif format.lower() == "csv":
            if not PANDAS_AVAILABLE:
                print("[ERROR] pandas library is required for CSV format")
                return ""
            
            df = pd.DataFrame(comments)
            df.to_csv(output_path, index=False, encoding="utf-8")
        
        print(f"[INFO] Saved {len(comments)} analyzed comments to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Failed to save advanced sentiment data: {e}")
        return ""

def save_comments_for_training(
    comments: List[Dict[str, Any]],
    output_path: str,
    format: str = "jsonl",
    text_field: str = "text",
    label_field: Optional[str] = "sentiment",
    exclude_spam: bool = True,
    save_spam_separately: bool = False
) -> str:
    """
    Save extracted comments to a file in the specified format.
    
    Args:
        comments: List of comments to save
        output_path: Output file path
        format: File format ("jsonl", "csv", "txt")
        text_field: Field name for the comment text
        label_field: Field name for the label (e.g., sentiment)
        exclude_spam: Whether to exclude spam comments
        save_spam_separately: Whether to save spam comments to a separate file
        
    Returns:
        Path to the saved file
    """
    if exclude_spam:
        comments = [c for c in comments if not c.get("is_spam", False)]
    
    # Separate spam comments if needed
    spam_comments = [c for c in comments if c.get("is_spam", False)]
    if save_spam_separately and spam_comments:
        spam_path = output_path.replace(".", "_spam.")
        if spam_path == output_path:  # If there's no file extension
            spam_path = f"{output_path}_spam"
            
        if format.lower() == "jsonl":
            with open(spam_path, "w", encoding="utf-8") as f:
                for comment in spam_comments:
                    if text_field in comment:
                        f.write(json.dumps(comment, ensure_ascii=False) + "\n")
        
        elif format.lower() == "csv":
            if not PANDAS_AVAILABLE:
                print("[ERROR] pandas library is not installed. Skipping saving spam comments as CSV.")
            else:
                df = pd.DataFrame(spam_comments)
                df.to_csv(spam_path, index=False, encoding="utf-8")
        
        elif format.lower() == "txt":
            with open(spam_path, "w", encoding="utf-8") as f:
                for comment in spam_comments:
                    if text_field in comment:
                        f.write(comment[text_field] + "\n")
        
        print(f"[INFO] Saved {len(spam_comments)} spam comments to: {spam_path}")
    
    # Save main comments
    if not comments:
        print("[WARN] No comments to save")
        return output_path
    
    try:
        if format.lower() == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for comment in comments:
                    if text_field in comment:
                        f.write(json.dumps(comment, ensure_ascii=False) + "\n")
    
        elif format.lower() == "csv":
            if not PANDAS_AVAILABLE:
                print("[ERROR] pandas library is not installed, but required for CSV format. Skipping CSV save.")
                print("Please install it with: pip install pandas")
                # Save as JSONL as fallback
                fallback_path = output_path.replace(".csv", "_fallback.jsonl")
                print(f"[INFO] Attempting to save as JSONL to: {fallback_path}")
                return save_comments_for_training(
                    comments, fallback_path, "jsonl", 
                    text_field, label_field, exclude_spam, False
                )

            df = pd.DataFrame(comments)
            df.to_csv(output_path, index=False, encoding="utf-8")
        
        elif format.lower() == "txt":
            with open(output_path, "w", encoding="utf-8") as f:
                for comment in comments:
                    if text_field in comment:
                        f.write(comment[text_field] + "\n")
        
        print(f"[INFO] Saved {len(comments)} comments to: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"[ERROR] Failed to save comments: {e}")
        return ""

# --- Combined Function ---
def extract_social_media_comments(
    platform: str,
    query: Union[str, List[str]], 
    max_results: int = None,  # None means unlimited
    include_sentiment: bool = False,
    filter_spam: bool = True,
    silent: bool = True,
    include_advanced_sentiment: bool = False,
    use_ml_sentiment: bool = False,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Extract comments from various social media platforms
      Args:
        platform: Platform name ("twitter", "x", "reddit", "youtube", "pantip", "facebook", "threads", "file")
        query: Search query/ID or list of queries/URLs (depends on platform)
        max_results: Maximum number of comments to return (total across all queries), None for unlimited
        include_sentiment: Whether to perform basic sentiment analysis
        filter_spam: Whether to filter out spam comments
        silent: Whether to suppress log messages
        include_advanced_sentiment: Whether to perform advanced Thai sentiment analysis
        use_ml_sentiment: Whether to use ML-enhanced sentiment analysis (requires include_advanced_sentiment)
        **kwargs: Additional platform-specific parameters
        
    Returns:
        List of comments in dictionary format    """
    
    platform = platform.lower()
    all_comments = []
    
    # Handle both single query and multiple queries
    queries = query if isinstance(query, list) else [query]
    
    if not silent and len(queries) > 1:
        print(f"[INFO] Processing {len(queries)} {platform} URLs/queries...")
    
    # Handle unlimited results
    if max_results is None:
        initial_fetch = None
        max_per_query = None
    else:
        # คำนวณจำนวนข้อมูลที่ต้องดึงเพิ่ม (เผื่อพบสแปม)
        initial_fetch = max_results
        if filter_spam:
            # เพิ่มจำนวนการดึงข้อมูลเริ่มต้นเป็น 150% ของที่ต้องการ
            initial_fetch = int(max_results * 1.5)
        
        # Calculate max results per query for multiple queries
        max_per_query = initial_fetch if len(queries) == 1 else max(1, initial_fetch // len(queries))
    
    try:
        for i, single_query in enumerate(queries):
            if not silent and len(queries) > 1:
                print(f"[INFO] Processing {i+1}/{len(queries)}: {single_query[:50]}...")
            
            comments = []
            
            # Call the appropriate extraction function based on platform
            if platform == "twitter" or platform == "x":
                if not silent and len(queries) == 1:
                    print("[INFO] Extracting data from Twitter/X...")
                comments = extract_twitter_comments(
                    single_query, 
                    max_results=max_per_query,
                    include_sentiment=include_sentiment
                )
            elif platform == "threads":
                if not silent and len(queries) == 1:
                    print("[INFO] Extracting data from Threads...")
                comments = extract_threads_comments(
                    single_query,
                    max_results=max_per_query,
                    include_sentiment=include_sentiment,
                    timeout=kwargs.get("timeout", 20)
                )
            elif platform == "reddit":
                if not silent and len(queries) == 1:
                    print("[INFO] Extracting data from Reddit...")
                comments = extract_reddit_comments(
                    single_query,
                    limit=max_per_query,
                    time_filter=kwargs.get("time_filter", "week"),
                    include_sentiment=include_sentiment
                )
            elif platform == "youtube":
                if not silent and len(queries) == 1:
                    print("[INFO] Extracting data from YouTube...")
                comments = extract_youtube_comments(
                    single_query,
                    max_results=max_per_query,
                    include_sentiment=include_sentiment
                )
            elif platform == "pantip":
                if not silent and len(queries) == 1:
                    print("[INFO] Extracting data from Pantip...")
                comments = extract_pantip_comments(
                    single_query,
                    max_results=max_per_query,
                    include_sentiment=include_sentiment
                )
            elif platform == "facebook":
                if not silent and len(queries) == 1:
                    print("[INFO] Extracting data from Facebook...")
                comments = extract_facebook_comments(
                    single_query,
                    max_results=max_per_query,
                    include_sentiment=include_sentiment
                )
            elif platform == "file":
                if not silent and len(queries) == 1:
                    print("[INFO] Loading comments from file...")                # Load comments from a local file (JSONL format)
                try:
                    with open(single_query, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                comment = json.loads(line)
                                comments.append(comment)
                            except json.JSONDecodeError:
                                continue
                    
                    if not silent and len(queries) == 1:
                        print(f"[INFO] Loaded {len(comments)} comments from file")
                except Exception as e:
                    if not silent:
                        print(f"[ERROR] Failed to load comments from file: {e}")
                    comments = []
            
            else:
                if not silent:
                    print(f"[ERROR] Unsupported platform: {platform}")
                continue  # Skip this query and continue with next
            
            # Add source information to each comment
            for comment in comments:
                if "source_query" not in comment:
                    comment["source_query"] = single_query
                if "query_index" not in comment:
                    comment["query_index"] = i
            
            # Aggregate results
            all_comments.extend(comments)
            
            if not silent and len(queries) > 1:
                print(f"[INFO] Extracted {len(comments)} comments from query {i+1}")
        
        # Deduplicate comments based on text similarity
        if len(queries) > 1 and all_comments:
            original_count = len(all_comments)
            all_comments = deduplicate_comments(all_comments)
            if not silent:
                print(f"[INFO] Removed {original_count - len(all_comments)} duplicate comments")
          # Advanced Thai Sentiment Analysis (ถ้าเปิดใช้งาน)
        if include_advanced_sentiment and all_comments:
            if not silent:
                if use_ml_sentiment:
                    print(f"[INFO] Applying ML-Enhanced Thai Sentiment Analysis...")
                else:
                    print(f"[INFO] Applying Advanced Thai Sentiment Analysis...")
            all_comments = batch_advanced_sentiment_analysis(all_comments, use_ml=use_ml_sentiment)
            if not silent:
                print(f"[INFO] Advanced sentiment analysis completed!")
        
        # Spam Filtering
        if filter_spam and all_comments:
            if not silent:
                print(f"[INFO] Filtering out spam comments...")
            all_comments = spam_filter(all_comments)
          # Limit results to max_results (only if max_results is specified)
        if max_results is not None and max_results > 0 and len(all_comments) > max_results:
            all_comments = all_comments[:max_results]
        
        if not silent:
            sentiment_info = ""
            if include_advanced_sentiment:
                sentiment_info = " with Advanced Thai Sentiment"
            elif include_sentiment:
                sentiment_info = " with basic sentiment"
            source_info = f" from {len(queries)} sources" if len(queries) > 1 else ""
            print(f"[INFO] Extracted {len(all_comments)} total comments from {platform.capitalize()}{source_info}{sentiment_info}")
        
        return all_comments
    
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return []

# Make sure all extract functions are defined before this main function
def extract_pantip_comments(
    topic_id: str,
    max_results: int = None,  # None means unlimited
    include_sentiment: bool = False
) -> List[Dict[str, Any]]:
    """Extract comments from Pantip topic with improved timeout handling"""
    comments = []
    
    # Handle both topic ID and full URL
    if topic_id.startswith("http"):
        url = topic_id
        topic_id = topic_id.split("/")[-1]
    else:
        url = f"https://pantip.com/topic/{topic_id}"
    
    try:
        print(f"[DEBUG] Fetching Pantip topic: {url}")
          # Use longer timeout for Pantip and enable scrolling for more comments
        html = fetch_with_playwright(
            url,
            wait_selector="div.display-post-wrapper, article, .post-item",
            timeout=60000,  # Increased to 60 seconds
            headless=True,
            wait_until="domcontentloaded",  # Changed from networkidle
            scroll_to_load_all=True  # Enable scrolling to load all comments
        )
        
        if not html:
            print("[ERROR] Failed to load Pantip page")
            return []
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Try multiple selectors for Pantip content
        main_selectors = [
            "div.display-post-story",
            "div.post-story", 
            "article .content",
            ".topic-display-post-story"
        ]
        
        # Extract main post
        main_post_text = ""
        for selector in main_selectors:
            main_post = soup.select_one(selector)
            if main_post:
                main_post_text = sanitize_text(main_post.get_text(strip=True))
                break
        
        if main_post_text and len(main_post_text) > 10:
            comment_data = {
                "text": main_post_text,
                "platform": "pantip",
                "post_type": "topic",
                "topic_id": topic_id,
                "url": url,
                "created_at": datetime.now().isoformat(),
                "is_spam": False
            }
            
            if include_sentiment:
                comment_data["sentiment"] = analyze_sentiment(main_post_text, "th")
            
            comments.append(comment_data)
          # Try multiple selectors for replies
        reply_selectors = [
            "div.display-post-wrapper div.display-post-story",
            ".comment-item .comment-content",
            ".reply-item .reply-content",
            ".post-reply .reply-story"
        ]
        
        replies_found = []
        for selector in reply_selectors:
            replies = soup.select(selector)
            if replies:
                replies_found = replies
                break
        
        print(f"[DEBUG] Found {len(replies_found)} potential replies")
        
        # Process all replies if max_results is None, otherwise limit
        max_replies = len(replies_found) if max_results is None else (max_results - 1)  # -1 for main post
        
        for reply in replies_found[:max_replies]:
            try:
                reply_text = sanitize_text(reply.get_text(strip=True))
                  # Skip if too short or similar to main post
                if len(reply_text) < 5 or reply_text == main_post_text:
                    continue
                
                comment_data = {
                    "text": reply_text,
                    "platform": "pantip",
                    "post_type": "reply",
                    "topic_id": topic_id,
                    "url": url,
                    "created_at": datetime.now().isoformat(),
                    "is_spam": False
                }
                
                if include_sentiment:
                    comment_data["sentiment"] = analyze_sentiment(reply_text, "th")
                
                comments.append(comment_data)
                
            except Exception as e:
                print(f"[WARN] Error extracting Pantip reply: {e}")
                continue
                
        print(f"[INFO] Extracted {len(comments)} comments from Pantip")
        
        # Return all comments if max_results is None, otherwise limit
        if max_results is None:
            return comments
        else:
            return comments[:max_results]
        
    except Exception as e:
        print(f"[ERROR] Pantip extraction failed: {e}")
        return []

def extract_facebook_comments(
    url: str,
    max_results: int = 100,
    include_sentiment: bool = False
) -> List[Dict[str, Any]]:
    """Extract comments from Facebook posts using web scraping with privacy protection"""
    try:
        print("[INFO] Extracting Facebook comments with privacy protection...")
        print("[WARNING] Facebook has strong anti-bot detection. This may fail or be slow.")
        
        # Use shorter timeout for Facebook
        data = extract_facebook_data(url)
        comments = []

        # Add main post (anonymized)
        if "post" in data:
            main_post = {
                "text": sanitize_text(data["post"], remove_personal_info=True),
                "created_at": datetime.now().isoformat(),
                "platform": "facebook",
                "post_url": "[REDACTED]",  # Don't store actual URL for privacy
                "post_type": "post",
                "author": "Anonymous",  # Anonymize author
                "is_spam": False
            }
            if include_sentiment:
                main_post["sentiment"] = analyze_sentiment(main_post["text"])
            comments.append(main_post)

        # Add comments (anonymized)
        for i, comment in enumerate(data.get("comments", [])):
            if not comment.get("text"):
                continue
            
            entry = {
                "text": sanitize_text(comment["text"], remove_personal_info=True),
                "created_at": datetime.now().isoformat(),
                "platform": "facebook",
                "post_url": "[REDACTED]",  # Privacy protection
                "post_type": "comment",
                "author": f"User_{i+1}",  # Anonymize authors
                "is_spam": False
            }
            
            if include_sentiment:
                entry["sentiment"] = analyze_sentiment(entry["text"])
            
            comments.append(entry)

        print(f"[INFO] Extracted {len(comments)} Facebook comments (anonymized)")
        return comments[:max_results]

    except Exception as e:
        print(f"[ERROR] Failed to extract Facebook comments: {e}")
        return []

def extract_threads_comments(
    url: str,
    max_results: int = 100,
    include_sentiment: bool = False,
    timeout: int = 20
) -> List[Dict[str, Any]]:
    """Extract comments from Threads posts (simplified implementation)"""
    print("[INFO] Threads extraction is experimental and may not work")
    return []

def extract_reddit_comments(
    query: str,
    limit: int = 100,
    time_filter: str = "week",
    include_sentiment: bool = False
) -> List[Dict[str, Any]]:
    """Extract comments from Reddit (simplified implementation)"""
    print("[INFO] Reddit extraction requires API setup - not implemented yet")
    return []

def extract_youtube_comments(
    video_id: str,
    max_results: int = None,  # None means unlimited
    include_sentiment: bool = False
) -> List[Dict[str, Any]]:
    """Extract comments from YouTube video using enhanced Playwright with aggressive scrolling"""
    comments = []
    
    # Handle both video ID and full URL
    if video_id.startswith("http"):
        url = video_id
        # Extract video ID from URL
        if "watch?v=" in video_id:
            video_id = video_id.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in video_id:
            video_id = video_id.split("youtu.be/")[1].split("?")[0]
        else:
            print("[ERROR] Invalid YouTube URL format")
            return []
    else:
        url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        print(f"[DEBUG] Fetching YouTube video: {url}")
        
        # Use enhanced scrolling with longer timeout for better comment loading
        html = fetch_with_playwright(
            url,
            wait_selector="#comments, ytd-comments, #comment-teaser, ytd-item-section-renderer",
            timeout=90000,  # Increased to 90 seconds
            headless=True,
            wait_until="domcontentloaded",
            scroll_to_load_all=True  # Enable aggressive scrolling to load all comments
        )
        
        if not html:
            print("[ERROR] Failed to load YouTube page")
            return []
            
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract video title and info
        video_title = ""
        title_selectors = [
            "h1.ytd-video-primary-info-renderer",
            "h1.ytd-watch-metadata #title h1",
            "h1.title",
            "h1[data-testid='video-title']",
            "#watch-title h1",
            "ytd-watch-metadata h1"
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                video_title = sanitize_text(title_element.get_text(strip=True))
                break
          # Enhanced comment extraction with more precise selectors
        found_comments = []
          # Strategy 1: Most precise comment text selectors (prioritize these)
        precise_selectors = [
            "ytd-comment-thread-renderer ytd-comment-renderer #content-text span:not([class*='button']):not([class*='link'])",  # Main comments, exclude buttons/links
            "ytd-comment-replies-renderer ytd-comment-renderer #content-text span:not([class*='button'])", # Reply comments, exclude buttons
            "ytd-comment-renderer #content-text yt-formatted-string[is-empty='false']",  # Non-empty formatted comment text
            "#content-text yt-formatted-string:not([class*='metadata']):not([class*='button'])",  # Formatted text, exclude metadata
            "ytd-comment-renderer #content-text span[dir='auto']:not([class*='published']):not([class*='author'])",  # Auto-dir spans, exclude metadata
        ]
        
        for selector in precise_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"[DEBUG] Found {len(elements)} comments using precise selector: {selector}")
                # Additional filtering at selector level for precise selectors
                filtered_elements = []
                for element in elements:
                    text = element.get_text(strip=True)
                    # Pre-filter at selector level for obvious non-comments
                    if (text and len(text) > 15 and 
                        not re.match(r'^\d+[\s\.,]*[kmbtพันหมื่นแสนล้าน]', text.lower()) and
                        'ที่ผ่านมา' not in text and 'ago' not in text.lower() and
                        'การดู' not in text and 'views' not in text.lower() and
                        not text.startswith('#') and not text.startswith('@')):
                        filtered_elements.append(element)
                
                if filtered_elements:
                    found_comments.extend(filtered_elements)
                    print(f"[DEBUG] After pre-filtering: {len(filtered_elements)} valid elements from precise selector")
                    break  # If we found good comments, don't try other selectors
          # Strategy 2: If no good comments found, try broader selectors with aggressive filtering
        if not found_comments:
            print("[DEBUG] No comments from precise selectors, trying broader approach...")
            
            broader_selectors = [
                "ytd-comment-thread-renderer #content-text span[dir='auto']",  # Thread level with direction
                "ytd-comment-renderer #content-text:not([class*='metadata'])",  # Comment level, exclude metadata
                "#content-text yt-formatted-string:not([class*='badge']):not([class*='button'])",  # Exclude badges and buttons
                "ytd-comment-view-model #content-text span",  # Comment view model
            ]
            
            for selector in broader_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"[DEBUG] Found {len(elements)} elements using broader selector: {selector}")
                    # Very aggressive pre-filtering for broader selectors
                    filtered_elements = []
                    for element in elements:
                        text = element.get_text(strip=True)
                        # Strict pre-filter for broader selectors
                        if (text and len(text) > 20 and  # Longer minimum for broader selectors
                            len(text.split()) >= 4 and  # More words required
                            not re.match(r'^\d+[\s\.,]*[kmbtพันหมื่นแสนล้าน]', text.lower()) and
                            'ที่ผ่านมา' not in text and 'ago' not in text.lower() and
                            'การดู' not in text and 'views' not in text.lower() and
                            'ครั้ง' not in text and 'ความคิดเห็น' not in text and
                            not text.startswith('#') and not text.startswith('@') and
                            not any(ui in text.lower() for ui in ['phimthai', 'tomtat', 'subscribe', 'like', 'share']) and
                            # Must contain meaningful content (Thai or substantial English)
                            (any('\u0e00' <= c <= '\u0e7f' for c in text) or  # Contains Thai
                             len([c for c in text if c.isalpha()]) >= 15)):  # Or substantial alphabetic content
                            filtered_elements.append(element)
                    
                    if filtered_elements:
                        found_comments.extend(filtered_elements)
                        print(f"[DEBUG] After aggressive pre-filtering: {len(filtered_elements)} valid elements")
                        break
        
        # Strategy 3: Last resort - very conservative extraction with maximum filtering
        if not found_comments:
            print("[DEBUG] No comments found, trying last resort extraction with maximum filtering...")
            
            # Only look for spans that might contain user comments, but be very selective
            potential_comment_elements = soup.select("span[dir='auto']:not([class*='published']):not([class*='author']):not([class*='metadata'])")
            
            if not potential_comment_elements:
                # Even more desperate - any spans with auto direction
                potential_comment_elements = soup.select("span[dir='auto']")
                print(f"[DEBUG] Last resort: found {len(potential_comment_elements)} span[dir='auto'] elements")
            
            strict_filtered = []
            for element in potential_comment_elements:
                text = element.get_text(strip=True)
                
                # Maximum strict filtering for last resort
                if (text and 
                    len(text) >= 25 and  # Much longer minimum
                    len(text.split()) >= 5 and  # At least 5 words
                    len([c for c in text if c.isalpha()]) >= 15 and  # Substantial alphabetic content
                    # Must NOT match any metadata patterns
                    not re.match(r'^\d+', text) and  # Doesn't start with numbers
                    not re.search(r'\d+.*?(เดือน|วัน|ปี|ชั่วโมง|นาที|วินาที|ago|hour|day|week|month|year)', text) and
                    not re.search(r'(การดู|view|ครั้ง|subscriber|ผู้ติดตาม)', text, re.IGNORECASE) and
                    # Must NOT be pure hashtags/mentions or contain them prominently
                    not re.match(r'^[#@]', text) and
                    not any(forbidden in text.lower() for forbidden in [
                        'phimthai', 'tomtat', 'subscribe', 'like', 'share', 'reply', 'comment',
                        'ที่ผ่านมา', 'ago', 'การดู', 'ครั้ง', 'ความคิดเห็น', 'ตอบกลับ',
                        'notification', 'bell', 'playlist', 'k ', 'm ', 'พัน', 'หมื่น', 'แสน', 'ล้าน'
                    ]) and
                    # Must contain meaningful content - Thai characters OR substantial English
                    (any('\u0e00' <= c <= '\u0e7f' for c in text) or  # Contains Thai
                     (len([c for c in text if c.isalpha()]) >= 20 and  # Substantial English content
                      not re.match(r'^[A-Z\s]+$', text)))  # Not all caps (likely titles/headings)
                ):
                    strict_filtered.append(element)
            
            found_comments = strict_filtered
            if found_comments:
                print(f"[DEBUG] Last resort with maximum filtering found {len(found_comments)} potential comments")
            else:
                print("[DEBUG] No valid comments found with any strategy - this video may have no comments or comments are disabled")# Remove duplicates while preserving order
        unique_comments = []
        seen_texts = set()
        for idx, element in enumerate(found_comments):
            raw_text = element.get_text(strip=True)
            text = sanitize_text(raw_text)
            
            # Debug: Log deduplication process for first few elements
            if idx < 5:
                print(f"[DEBUG] Dedup {idx+1}: Raw='{raw_text[:30]}...', Sanitized='{text[:30]}...', Length={len(text)}")            # Enhanced filtering for comments vs metadata  
            # Check for UI/metadata patterns that should be filtered out
            ui_patterns = [
                r'^\d+[\s\.,]*[kmbtพันหมื่นแสนล้าน]',  # View counts like "1.8 หมื่น"
                r'^\d+\s*(เดือน|วัน|ปี|ชั่วโมง|นาที|วินาที|ago|hour|minute|day|week|month|year)',  # Timestamps
                r'^\d+[\s\.,]*ครั้ง',  # "ครั้ง" patterns
                r'^#\w+$',  # Pure hashtags
                r'^@\w+$',  # Pure mentions
                r'การดู.*ครั้ง',  # "การดู X ครั้ง" patterns
                r'\d+\s*(เดือน|วัน|ปี)ที่ผ่านมา$',  # Thai time ago patterns
                r'^\d+[\s\.,]*(k|m|พัน|หมื่น|แสน|ล้าน).*ครั้ง',  # Complex view count patterns
                r'^[\d\.,]+\s*(k|m|b|พัน|หมื่น|แสน|ล้าน)\s*(การดู|ครั้ง|views?)',  # More view patterns
                r'^\d+[\s\.,]*[kmb]\s*(views?|การดู)',  # English view patterns
                r'^(subscribe|like|share|comment|reply|ติดตาม|กด|แชร์|แสดงความคิดเห็น)$',  # Action words
                r'^(playlist|เพลย์ลิสต์|รายการเพลง)$',  # Playlist indicators
                r'^(notification|การแจ้งเตือน|แจ้งเตือน)$',  # Notification text
                r'^\d+\s*(subscriber|ผู้ติดตาม)',  # Subscriber counts
            ]
            
            # UI/metadata keywords to filter out (exact matches and contains)
            ui_exact_keywords = [
                'การดู', 'ครั้ง', 'ความคิดเห็น', 'ตอบกลับ', 'แสดงความคิดเห็น',
                'เดือนที่ผ่านมา', 'วันที่ผ่านมา', 'ปีที่ผ่านมา', 'ชั่วโมงที่ผ่านมา', 
                'นาทีที่ผ่านมา', 'วินาทีที่ผ่านมา', 'ที่ผ่านมา',
                'subscribe', 'notification', 'playlist', 'settings', 'views', 'subscribers',
                'ติดตาม', 'กระดิ่ง', 'การแจ้งเตือน', 'เพลย์ลิสต์', 'การตั้งค่า',
                'phimthaihay', 'tomtatphim', 'like', 'share', 'reply', 'comment',
                'bell icon', 'sort by', 'เรียงลำดับ', 'top comments', 'newest first'
            ]
            
            # Partial matches for UI elements
            ui_contains_keywords = [
                'การดู', 'ครั้ง', 'ที่ผ่านมา', 'ago', 'phimthai', 'tomtat',
                'subscribe', 'notification', 'playlist', 'views', 'subscriber'
            ]
              # Check if text matches any UI pattern
            matches_ui_pattern = any(re.match(pattern, text, re.IGNORECASE) for pattern in ui_patterns)
            
            # Check if text is exactly a UI keyword
            is_exact_ui_keyword = text.lower() in [kw.lower() for kw in ui_exact_keywords]
            
            # Check if text contains UI keywords and is short (likely metadata)
            contains_ui_keyword = (
                len(text) <= 50 and  # Only check short text for contains
                any(kw.lower() in text.lower() for kw in ui_contains_keywords)
            )
            
            # More aggressive filtering for obvious metadata
            is_metadata = (
                # Pure numbers or number-heavy content
                re.match(r'^\d+[\s\.,]*[a-zA-Zก-๙]*$', text) or
                # Time-related patterns
                re.search(r'\d+.*?(เดือน|วัน|ปี|ชั่วโมง|นาที|ago|hour|day|week|month|year)', text) or
                # View count patterns
                re.search(r'(การดู|view|ครั้ง)', text, re.IGNORECASE) or
                # Single hashtags or mentions
                re.match(r'^[#@]\w+$', text) or
                # Pure category/tag text
                text.lower() in ['phimthaihay', 'tomtatphim', 'hashtag'] or
                # Interface elements
                text.lower() in ['comment', 'reply', 'like', 'share', 'subscribe', 'ความคิดเห็น']            )
            
            is_valid_comment = (
                text and 
                text not in seen_texts and 
                len(text) >= 10 and  # Increased minimum length for substantial comments
                len(text.split()) >= 3 and  # Must have at least 3 words
                not matches_ui_pattern and  # Doesn't match UI patterns
                not is_exact_ui_keyword and  # Not an exact UI keyword
                not contains_ui_keyword and  # Doesn't contain UI keywords in short text
                not is_metadata and  # Not obvious metadata
                not text.startswith('#') and  # Skip hashtags
                not text.startswith('@') and  # Skip mentions
                len([c for c in text if c.isalpha()]) >= 8 and  # Must have substantial alphabetic content
                # Additional content validation
                not re.match(r'^\d+[\s\.,]*\w*$', text) and  # Not just numbers with optional suffix
                # Ensure it's not just UI button text or labels
                not text.lower() in ['comments', 'replies', 'show more', 'show less', 'sort by', 'newest', 'top comments'] and
                # Thai UI text filtering
                not text.lower() in ['ความคิดเห็น', 'การตอบกลับ', 'แสดงเพิ่มเติม', 'แสดงน้อยลง', 'เรียงลำดับ']            )
            
            if is_valid_comment:
                unique_comments.append(element)
                seen_texts.add(text)
            elif idx < 10:  # Debug first 10 filtered items
                filter_reasons = []
                if matches_ui_pattern:
                    filter_reasons.append("matches UI pattern")
                if is_exact_ui_keyword:
                    filter_reasons.append("exact UI keyword")
                if contains_ui_keyword:
                    filter_reasons.append("contains UI keyword")
                if is_metadata:
                    filter_reasons.append("detected as metadata")
                if len(text) < 10:
                    filter_reasons.append(f"too short ({len(text)} chars)")
                if len(text.split()) < 3:
                    filter_reasons.append(f"too few words ({len(text.split())} words)")
                if text in seen_texts:
                    filter_reasons.append("duplicate")
                
                reason = ", ".join(filter_reasons) if filter_reasons else "unknown reason"
                print(f"[DEBUG] Filtered out comment {idx+1}: '{text[:30]}...' (Reason: {reason})")
        
        print(f"[DEBUG] Deduplication and filtering: {len(found_comments)} -> {len(unique_comments)} valid comments")
        found_comments = unique_comments
        print(f"[DEBUG] Found {len(found_comments)} unique potential comments")        
        
        # Process comments with enhanced metadata extraction
        max_comments = len(found_comments) if max_results is None else max_results
        processed_count = 0
        skipped_count = 0
        
        for idx, comment_element in enumerate(found_comments):
            if max_results is not None and processed_count >= max_comments:
                break
                
            try:
                # Extract comment text
                raw_text = comment_element.get_text(strip=True)
                comment_text = sanitize_text(raw_text)
                
                # Debug: Log processing details for first few comments
                if idx < 5:
                    print(f"[DEBUG] Comment {idx+1}: Raw='{raw_text[:50]}...', Sanitized='{comment_text[:50]}...', Length={len(comment_text)}")
                
                # Skip if too short or empty - but be less aggressive
                if len(comment_text) < 2:  # Reduced from 3 to 2
                    skipped_count += 1
                    if idx < 10:  # Debug first 10 skipped
                        print(f"[DEBUG] Skipped comment {idx+1}: too short (length={len(comment_text)})")
                    continue
                
                # Enhanced author extraction with multiple strategies
                author = "Unknown"
                
                # Strategy 1: Look in the same comment thread container
                comment_container = (
                    comment_element.find_parent("ytd-comment-thread-renderer") or
                    comment_element.find_parent("ytd-comment-renderer") or
                    comment_element.find_parent("div", {"id": re.compile(r"comment|thread")})
                )
                
                if comment_container:
                    author_selectors = [
                        "#author-text span",              # Standard author text
                        "#author-text",                   # Direct author text
                        ".ytd-comment-renderer #author-text",  # Scoped author
                        "#header-author #author-text",    # Header author
                        ".comment-author-text",           # Legacy author
                        "a[href*='@'] span",             # Author links
                        "[id*='author'] span",            # Any author-related ID
                        "yt-formatted-string[is-empty='false']"  # Non-empty formatted strings
                    ]
                    
                    for author_selector in author_selectors:
                        author_element = comment_container.select_one(author_selector)
                        if author_element:
                            author_text = sanitize_text(author_element.get_text(strip=True))
                            if author_text and len(author_text) < 50:  # Reasonable author name length
                                author = author_text
                                break
                
                # Enhanced timestamp extraction
                timestamp = ""
                if comment_container:
                    timestamp_selectors = [
                        ".published-time-text a",         # Published time link
                        "#published-time-text",           # Direct published time
                        ".published-time-text",           # Published time class
                        "a[href*='lc=']",                 # Comment permalink
                        "[id*='published-time']",         # Any published time ID
                        "span[title*='ago']",             # Relative time spans
                        "span[title*='ที่แล้ว']"          # Thai relative time
                    ]
                    
                    for time_selector in timestamp_selectors:
                        time_element = comment_container.select_one(time_selector)
                        if time_element:
                            # Try to get either text content or title attribute
                            timestamp = (
                                time_element.get('title') or 
                                time_element.get_text(strip=True)
                            )
                            if timestamp:
                                break
                
                # Enhanced likes extraction
                likes = 0
                if comment_container:
                    likes_selectors = [
                        "#vote-count-middle",             # Vote count middle
                        ".vote-count-middle",             # Vote count class
                        "#like-button #text",             # Like button text
                        "[id*='vote-count']",             # Any vote count ID
                        "button[aria-label*='like'] #text"  # Like button aria
                    ]
                    
                    for likes_selector in likes_selectors:
                        likes_element = comment_container.select_one(likes_selector)
                        if likes_element:
                            likes_text = likes_element.get_text(strip=True)
                            if likes_text:
                                try:
                                    # Extract numbers from likes text
                                    likes_match = re.search(r'(\d+)', likes_text.replace(',', ''))
                                    if likes_match:
                                        likes = int(likes_match.group(1))
                                        break
                                except:
                                    pass
                
                # Enhanced reply detection
                is_reply = False
                reply_indicators = [
                    "ytd-comment-replies-renderer",      # Reply renderer
                    "[id*='replies']",                   # Reply-related IDs
                    ".ytd-comment-view-model"            # Comment view model (often replies)
                ]
                
                for indicator in reply_indicators:
                    if comment_container and comment_container.select_one(indicator):
                        is_reply = True
                        break
                
                comment_data = {
                    "text": comment_text,
                    "platform": "youtube",
                    "post_type": "reply" if is_reply else "comment",
                    "video_id": video_id,
                    "video_title": video_title,
                    "url": url,
                    "author": author,
                    "timestamp": timestamp,
                    "likes": likes,
                    "created_at": datetime.now().isoformat(),
                    "is_spam": False                }
                
                if include_sentiment:
                    comment_data["sentiment"] = analyze_sentiment(comment_text, "th")
                
                comments.append(comment_data)
                processed_count += 1
                
                # Debug: Log progress for first few processed comments
                if processed_count <= 5:
                    print(f"[DEBUG] Successfully processed comment {processed_count}: '{comment_text[:50]}...'")
                
            except Exception as e:
                print(f"[WARN] Error extracting YouTube comment {idx+1}: {e}")
                continue
        
        print(f"[DEBUG] YouTube extraction summary:")
        print(f"  - Found elements: {len(found_comments)}")
        print(f"  - Processed successfully: {processed_count}")
        print(f"  - Skipped (too short): {skipped_count}")
        print(f"  - Final comments list: {len(comments)}")
        
        print(f"[INFO] Extracted {len(comments)} comments from YouTube")
        
        # Return all comments if max_results is None, otherwise limit
        if max_results is None:
            return comments
        else:
            return comments[:max_results]
        
    except Exception as e:
        print(f"[ERROR] YouTube extraction failed: {e}")
        return []

def deduplicate_comments(comments: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Remove duplicate comments based on text similarity
    
    Args:
        comments: List of comment dictionaries
        similarity_threshold: Similarity threshold for considering comments as duplicates (0.0 to 1.0)
        
    Returns:
        List of unique comments
    """
    if not comments:
        return comments
    
    unique_comments = []
    seen_texts = set()
    
    for comment in comments:
        text = comment.get("text", "").strip().lower()
        
        # Skip empty texts
        if not text:
            continue
        
        # Simple exact match check first
        if text in seen_texts:
            continue
            
        # Check similarity with existing comments for near-duplicates
        is_duplicate = False
        for existing_comment in unique_comments:
            existing_text = existing_comment.get("text", "").strip().lower()
            
            # Simple similarity check: if one text is substring of another with high overlap
            if existing_text and text != existing_text:
                # Calculate similarity based on common words
                words1 = set(text.split())
                words2 = set(existing_text.split())
                
                if words1 and words2:
                    intersection = len(words1.intersection(words2))
                    union = len(words1.union(words2))
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity >= similarity_threshold:
                        is_duplicate = True
                        break
        
        if not is_duplicate:
            seen_texts.add(text)
            unique_comments.append(comment)
    
    return unique_comments

# --- ML-Enhanced Sentiment Analysis ---
try:
    from ml_sentiment_analysis import create_ml_enhanced_sentiment_analyzer
    ML_SENTIMENT_AVAILABLE = True
except ImportError:
    ML_SENTIMENT_AVAILABLE = False

# Global ML model instance
_ml_sentiment_model = None

def get_ml_sentiment_model(training_data: Optional[List[Dict[str, Any]]] = None):
    """Get or create ML sentiment model"""
    global _ml_sentiment_model
    
    if _ml_sentiment_model is None and ML_SENTIMENT_AVAILABLE:
        try:
            print("[INFO] Initializing ML-enhanced sentiment analyzer...")
            _ml_sentiment_model = create_ml_enhanced_sentiment_analyzer(training_data)
            print("[INFO] ML sentiment analyzer ready!")
        except Exception as e:
            print(f"[WARNING] Failed to initialize ML model: {e}")
            _ml_sentiment_model = None
    
    return _ml_sentiment_model

def ml_enhanced_sentiment_analysis(text: str, training_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    ML-enhanced Thai sentiment analysis
    
    Args:
        text: Thai text to analyze
        training_data: Optional training data for model improvement
        
    Returns:
        Dictionary with enhanced sentiment analysis
    """
    # Get ML model
    ml_model = get_ml_sentiment_model(training_data)
    
    if ml_model is not None:
        try:
            # Use ML model
            ml_result = ml_model.predict_sentiment(text)
            
            # Combine with rule-based analysis for complete schema
            rule_result = advanced_thai_sentiment_analysis(text)
            
            # Merge results (ML takes precedence for sentiment/score)
            enhanced_result = rule_result.copy()
            enhanced_result.update({
                'sentiment': ml_result['sentiment'],
                'sentiment_score': ml_result['sentiment_score'],
                'confidence': ml_result['confidence'],
                'ml_probabilities': ml_result['probabilities'],
                'model_type': ml_result['model_type'],
                'ml_enhanced': True
            })
            
            # Adjust emotion based on ML sentiment
            if ml_result['sentiment'] == 'positive' and rule_result['emotion'] in ['anger', 'sadness']:
                enhanced_result['emotion'] = 'joy'
            elif ml_result['sentiment'] == 'negative' and rule_result['emotion'] in ['joy', 'excited']:
                enhanced_result['emotion'] = 'anger'
            
            # Add confidence-based notes
            if ml_result['confidence'] > 0.8:
                enhanced_result['notes'] = f"ความเชื่อมั่นสูง, {enhanced_result['notes']}"
            elif ml_result['confidence'] < 0.6:
                enhanced_result['notes'] = f"ความเชื่อมั่นต่ำ, {enhanced_result['notes']}"
            
            return enhanced_result
            
        except Exception as e:
            print(f"[WARNING] ML sentiment analysis failed: {e}")
            # Fallback to rule-based
            result = advanced_thai_sentiment_analysis(text)
            result['ml_enhanced'] = False
            result['fallback_reason'] = str(e)
            return result
    else:
        # No ML model available, use rule-based
        result = advanced_thai_sentiment_analysis(text)
        result['ml_enhanced'] = False
        result['fallback_reason'] = "ML model not available"
        return result