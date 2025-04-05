import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import re
import os
import logging
import feedparser
from urllib.parse import urljoin
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NewsCrawlerBase(ABC):
    """Base class for news crawlers"""
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.output_dir = os.path.abspath('hk_news')
        os.makedirs(self.output_dir, exist_ok=True)

    @abstractmethod
    def parse_feed(self):
        pass

    @abstractmethod
    def extract_article_content(self, url):
        pass

    def save_to_csv(self, articles, filename):
        """Save articles to CSV file"""
        try:
            if articles:
                df = pd.DataFrame(articles)
                output_path = os.path.join(self.output_dir, filename)
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                logging.info(f"Saved {len(df)} articles to {output_path}")
            else:
                logging.warning("No articles to save")
        except Exception as e:
            logging.error(f"Error saving to CSV: {str(e)}")

class SCMPNewsCrawler(NewsCrawlerBase):
    """SCMP crawler implementation"""
    def __init__(self):
        super().__init__()
        # Define all SCMP RSS feed categories
        self.feed_categories = {
            'news': {
                'hong_kong': 'https://www.scmp.com/rss/91/feed',
                'china': 'https://www.scmp.com/rss/4/feed',
                'asia': 'https://www.scmp.com/rss/3/feed',
                'world': 'https://www.scmp.com/rss/2/feed',
            },
            'business': {
                'business': 'https://www.scmp.com/rss/92/feed',
                'companies': 'https://www.scmp.com/rss/95/feed',
                'property': 'https://www.scmp.com/rss/96/feed',
                'global_economy': 'https://www.scmp.com/rss/94/feed',
                'china_economy': 'https://www.scmp.com/rss/5/feed',
            },
            'tech': {
                'tech': 'https://www.scmp.com/rss/36/feed',
                'enterprises': 'https://www.scmp.com/rss/36396/feed',
                'social_gadgets': 'https://www.scmp.com/rss/36397/feed',
                'start_ups': 'https://www.scmp.com/rss/36398/feed',
            },
            'lifestyle': {
                'lifestyle': 'https://www.scmp.com/rss/94469/feed',
                'fashion': 'https://www.scmp.com/rss/94472/feed',
                'travel': 'https://www.scmp.com/rss/94473/feed',
            },
            'sport': {
                'sport': 'https://www.scmp.com/rss/95/feed',
                'hong_kong': 'https://www.scmp.com/rss/95056/feed',
                'china': 'https://www.scmp.com/rss/95057/feed',
                'golf': 'https://www.scmp.com/rss/95058/feed',
            }
        }

    def parse_feed(self):
        """Parse all SCMP RSS feeds"""
        all_articles = []
        
        # Iterate through all categories and their feeds
        for category, subcategories in self.feed_categories.items():
            for subcategory, feed_url in subcategories.items():
                try:
                    logging.info(f"Parsing SCMP {category}/{subcategory} feed")
                    
                    # Get the raw XML content
                    response = requests.get(feed_url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    # Parse XML directly
                    root = ET.fromstring(response.content)
                    channel = root.find('channel')
                    if channel is None:
                        continue
                        
                    # Process each item in the feed
                    for item in channel.findall('item'):
                        description = self._get_element_text(item, 'description')
                        
                        # Skip articles with missing or empty description
                        if not description or description.isspace():
                            continue
                            
                        # Clean description by removing newlines and multiple spaces
                        description = ' '.join(description.split())
                        
                        article = {
                            'source': 'SCMP',
                            'category': category,
                            'subcategory': subcategory,
                            'title': self._get_element_text(item, 'title'),
                            'link': self._get_element_text(item, 'link'),
                            'description': description,
                            'pub_date': self._get_element_text(item, 'pubDate'),
                            'author': self._get_element_text(item, 'author'),
                            'guid': self._get_element_text(item, 'guid'),
                            'full_content': description,  # Using description as content
                        }
                        
                        # Clean and format the published date
                        try:
                            if article['pub_date']:
                                parsed_date = datetime.strptime(
                                    article['pub_date'], 
                                    '%a, %d %b %Y %H:%M:%S %z'
                                )
                                article['pub_date_formatted'] = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            logging.warning(f"Date parsing error: {str(e)}")
                            article['pub_date_formatted'] = article['pub_date']
                        
                        # Extract media content if available
                        media_content = item.find('{http://search.yahoo.com/mrss/}content')
                        if media_content is not None:
                            article.update({
                                'media_url': media_content.get('url', ''),
                                'media_type': media_content.get('type', ''),
                                'media_width': media_content.get('width', ''),
                                'media_height': media_content.get('height', '')
                            })
                        
                        all_articles.append(article)
                    
                    time.sleep(2)  # Polite delay between feed requests
                        
                except Exception as e:
                    logging.error(f"Error parsing SCMP {category}/{subcategory} feed: {str(e)}")
                    continue
                
        return all_articles

    def _get_element_text(self, item, tag):
        """Helper method to safely get element text"""
        element = item.find(tag)
        return element.text if element is not None else ''

    def extract_article_content(self, url):
        """
        Minimal implementation to satisfy abstract base class.
        We're not using this since we get content directly from RSS feed.
        """
        return {'full_content': ''}

class HKFPCrawler(NewsCrawlerBase):
    """Hong Kong Free Press crawler"""
    def __init__(self):
        super().__init__()
        self.feed_url = 'https://hongkongfp.com/feed/'

    def parse_feed(self):
        try:
            feed = feedparser.parse(self.feed_url)
            articles = []
            
            for entry in feed.entries:
                article = {
                    'source': 'HKFP',
                    'category': 'news',  # Default category
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'description': entry.get('description', ''),
                    'pub_date': entry.get('published', ''),
                    'author': entry.get('author', '')
                }
                
                # Clean and format the published date
                try:
                    if article['pub_date']:
                        parsed_date = datetime.strptime(
                            article['pub_date'], 
                            '%a, %d %b %Y %H:%M:%S %z'
                        )
                        article['pub_date_formatted'] = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    logging.warning(f"Date parsing error: {str(e)}")
                    article['pub_date_formatted'] = article['pub_date']
                
                if article['link']:
                    content = self.extract_article_content(article['link'])
                    article.update(content)
                
                articles.append(article)
                time.sleep(1)
                
            return articles
        except Exception as e:
            logging.error(f"Error parsing HKFP feed: {str(e)}")
            return []

    def extract_article_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content = ''
            content_div = soup.find('div', class_='entry-content')
            if content_div:
                paragraphs = content_div.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs])
            
            return {'full_content': content}
        except Exception as e:
            logging.error(f"Error extracting HKFP content from {url}: {str(e)}")
            return {'full_content': ''}

class RTHKCrawler(NewsCrawlerBase):
    """RTHK English news crawler"""
    def __init__(self):
        super().__init__()
        self.feed_categories = {
            'local': 'https://rthk.hk/rthk/news/rss/e_expressnews_elocal.xml',
            'greater_china': 'https://rthk.hk/rthk/news/rss/e_expressnews_egreaterchina.xml',
            'international': 'https://rthk.hk/rthk/news/rss/e_expressnews_einternational.xml',
            'finance': 'https://rthk.hk/rthk/news/rss/e_expressnews_efinance.xml',
            'sport': 'https://rthk.hk/rthk/news/rss/e_expressnews_esport.xml'
        }

    def parse_feed(self):
        """Parse all RTHK English RSS feeds"""
        all_articles = []
        
        for category, feed_url in self.feed_categories.items():
            try:
                logging.info(f"Parsing RTHK {category} feed")
                
                # Get the raw XML content
                response = requests.get(feed_url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                # Parse XML directly
                root = ET.fromstring(response.content)
                channel = root.find('channel')
                if channel is None:
                    continue
                
                # Get all descriptions from the feed
                description_elem = channel.find('description')
                if description_elem is None or not description_elem.text:
                    continue
                    
                # Split the description into individual articles
                articles_text = description_elem.text.split('\n\n\n')
                
                for article_text in articles_text:
                    if not article_text.strip():
                        continue
                        
                    try:
                        # Split into title and content
                        parts = article_text.strip().split('\n\n', 2)
                        if len(parts) < 2:
                            continue
                            
                        title = parts[0].replace('(with hyperlink)', '').strip()
                        pub_date = parts[1].strip()
                        content = parts[2].strip() if len(parts) > 2 else ''
                        
                        # Clean text by removing newlines and multiple spaces
                        content = ' '.join(content.split())
                        
                        article = {
                            'source': 'RTHK',
                            'category': category,
                            'title': title,
                            'description': content,
                            'pub_date': pub_date,
                            'full_content': content,
                        }
                        
                        # Clean and format the published date
                        try:
                            if article['pub_date']:
                                parsed_date = datetime.strptime(
                                    article['pub_date'], 
                                    '%a, %d %b %Y %H:%M:%S %z'
                                )
                                article['pub_date_formatted'] = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            logging.warning(f"Date parsing error: {str(e)}")
                            article['pub_date_formatted'] = article['pub_date']
                        
                        all_articles.append(article)
                        
                    except Exception as e:
                        logging.error(f"Error parsing article text: {str(e)}")
                        continue
                
                time.sleep(2)  # Polite delay between feed requests
                    
            except Exception as e:
                logging.error(f"Error parsing RTHK {category} feed: {str(e)}")
                continue
            
        return all_articles

    def _get_element_text(self, item, tag):
        """Helper method to safely get element text"""
        element = item.find(tag)
        return element.text if element is not None else ''

    def extract_article_content(self, url):
        """
        Minimal implementation to satisfy abstract base class.
        We're not using this since we get content directly from RSS feed.
        """
        return {'full_content': ''}

def main():
    try:
        # Dictionary to store articles by source
        articles_by_source = {
            'SCMP': [],
            'HKFP': [],
            'RTHK': []
        }
        
        # Create output directory
        output_dir = os.path.abspath('hk_news')
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Created output directory at: {output_dir}")
        
        # Crawl SCMP
        scmp_crawler = SCMPNewsCrawler()
        scmp_articles = scmp_crawler.parse_feed()
        articles_by_source['SCMP'].extend(scmp_articles)
        
        # Crawl HKFP
        hkfp_crawler = HKFPCrawler()
        hkfp_articles = hkfp_crawler.parse_feed()
        articles_by_source['HKFP'].extend(hkfp_articles)
        
        # Crawl RTHK
        rthk_crawler = RTHKCrawler()
        rthk_articles = rthk_crawler.parse_feed()
        articles_by_source['RTHK'].extend(rthk_articles)
        
        # Process and save each source separately
        dataframes = {}
        for source, articles in articles_by_source.items():
            if articles:
                # Create DataFrame
                df = pd.DataFrame(articles)
                
                # Remove rows with missing values
                df = df.dropna(subset=['title', 'description', 'full_content'])
                
                # Clean all text columns by removing newlines and multiple spaces
                text_columns = ['title', 'description', 'full_content', 'author']
                for col in text_columns:
                    if col in df.columns:
                        df[col] = df[col].astype(str).str.split().str.join(' ')
                
                # Filter for English content
                def is_english(text):
                    if not text:
                        return False
                    return len([c for c in text if ord(c) < 128]) / len(text) > 0.7
                
                df = df[df['full_content'].apply(is_english)]
                
                # Save to source-specific file in hk_news directory
                filename = os.path.join(output_dir, f'{source.lower()}_news.csv')
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                logging.info(f"Saved {len(df)} articles to {filename}")
                
                # Store DataFrame in dictionary
                dataframes[source] = df
            else:
                logging.warning(f"No articles found for {source}")
                dataframes[source] = pd.DataFrame()
        
        return dataframes
            
    except Exception as e:
        logging.error(f"Main execution error: {str(e)}")
        return {}

if __name__ == "__main__":
    dataframes = main()
    
    # Print summary of results with safer column selection
    for source, df in dataframes.items():
        print(f"\n{source} articles found: {len(df)}")
        if not df.empty:
            print("\nFirst few articles:")
            # Only show columns that exist in the DataFrame
            display_columns = ['title']
            if 'category' in df.columns:
                display_columns.append('category')
            if 'pub_date_formatted' in df.columns:
                display_columns.append('pub_date_formatted')
            print(df[display_columns].head())
