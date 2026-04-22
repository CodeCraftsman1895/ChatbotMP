import requests
from readability import Document
from bs4 import BeautifulSoup
import urllib.robotparser
from urllib.parse import urlparse
import time
import requests_cache

# Enable caching for requests
requests_cache.install_cache('article_cache', expire_after=3600)  # Cache for 1 hour

user_agent = 'Mozilla/5.0 (compatible; ChatbotArticleExtractor/1.0; +https://example.com/bot)'

def extract_article(link: str) -> dict:
    """
    Extract readable text from a web article URL.

    Args:
        link (str): URL of the article.

    Returns:
        dict: {"content": str, "error": str or None}
    """
    if not link or not isinstance(link, str):
        return {"content": "", "error": "Invalid or missing link"}
    
    try:
        parsed = urlparse(link)
        if not parsed.scheme or not parsed.netloc:
            return {"content": "", "error": "Invalid URL format"}
    except Exception:
        return {"content": "", "error": "Invalid URL"}
    
    try:
        parsed = urlparse(link)
        if 'wikipedia.org' in parsed.netloc:
            # Use Wikipedia API for ethical extraction
            title = parsed.path.split('/wiki/')[-1]
            api_url = f"https://{parsed.netloc}/api/rest_v1/page/summary/{title}"
            time.sleep(1)
            response = requests.get(api_url, headers={'User-Agent': user_agent})
            response.raise_for_status()
            data = response.json()
            content = data.get('extract', '')
            return {"content": content, "error": None}
        else:
            # For other sites, check robots.txt
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                if not rp.can_fetch(user_agent, link):
                    return {"content": "", "error": f"Robots.txt disallows access to {link}"}
            except Exception as e:
                return {"content": "", "error": f"Failed to read robots.txt: {e}"}
            
            # Add a delay to be respectful to the server
            time.sleep(1)
            
            response = requests.get(link, headers={'User-Agent': user_agent})
            response.raise_for_status()  # Raise an error for bad status codes
            
            doc = Document(response.text)
            html = doc.summary()

            soup = BeautifulSoup(html, "html.parser")
            content = soup.get_text()
            return {"content": content, "error": None}
    except requests.exceptions.RequestException as e:
        return {"content": "", "error": f"Request failed: {e}"}
    except Exception as e:
        return {"content": "", "error": f"Article extraction failed: {e}"}
