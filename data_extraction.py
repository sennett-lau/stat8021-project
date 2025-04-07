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
        self.base_url = 'https://hongkongfp.com'

    def parse_feed(self):
        """Parse HKFP main page and individual articles"""
        all_articles = []
        
        try:
            # Get the main page
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Print first part of response to debug
            print("Response text sample:", response.text[:1000])
            
            # Find all article links
            # Pattern matches URLs like: /2025/04/06/article-title
            link_pattern = r'href="(https://hongkongfp\.com/\d{4}/\d{2}/\d{2}/[^"]+)"[^>]*>([^<]+)</a>'
            article_links = re.findall(link_pattern, response.text)
            
            print(f"Found {len(article_links)} article links")
            
            for url, title in article_links:
                try:
                    print(f"Processing URL: {url}")
                    print(f"Title: {title}")
                    
                    # Get article content
                    article_content = self.extract_article_content(url)
                    
                    if article_content:
                        article = {
                            'source': 'HKFP',
                            'title': title.strip(),
                            'link': url,
                            'pub_date': article_content.get('pub_date', ''),
                            'full_content': article_content.get('full_content', ''),
                            'author': article_content.get('author', '')
                        }
                        
                        # Format the date if available
                        if article['pub_date']:
                            try:
                                # HKFP date format: "08:48, 6 April 2025"
                                date_str = article['pub_date'].split(', ')[1]
                                parsed_date = datetime.strptime(date_str, '%d %B %Y')
                                article['pub_date_formatted'] = parsed_date.strftime('%Y-%m-%d')
                            except Exception as e:
                                logging.warning(f"Date parsing error: {str(e)}")
                                article['pub_date_formatted'] = article['pub_date']
                        
                        all_articles.append(article)
                        logging.info(f"Processed article: {title}")
                        
                        time.sleep(2)  # Polite delay between requests
                        
                except Exception as e:
                    logging.error(f"Error processing article {url}: {str(e)}")
                    continue
                
        except Exception as e:
            logging.error(f"Error parsing HKFP feed: {str(e)}")
            
        return all_articles

    def extract_article_content(self, url):
        """Extract content from HKFP article pages"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Clean the HTML content
            cleaned_text = re.sub(r'<script.*?</script>', '', response.text, flags=re.DOTALL)
            cleaned_text = re.sub(r'<style.*?</style>', '', cleaned_text, flags=re.DOTALL)
            
            # Extract author
            author_pattern = r'by\s+([^<]+)<'
            author_match = re.search(author_pattern, cleaned_text)
            author = author_match.group(1).strip() if author_match else ''
            
            # Extract date
            date_pattern = r'(\d{2}:\d{2},\s+\d+\s+[A-Za-z]+\s+\d{4})'
            date_match = re.search(date_pattern, cleaned_text)
            pub_date = date_match.group(1) if date_match else ''
            
            # Extract article content
            # Find the main article content div
            content_pattern = r'<div class="entry-content[^"]*">(.*?)</div>'
            content_match = re.search(content_pattern, cleaned_text, re.DOTALL)
            
            if content_match:
                content_html = content_match.group(1)
                # Extract paragraphs
                paragraphs = re.findall(r'<p>(.*?)</p>', content_html)
                # Clean and join paragraphs
                content = ' '.join(p.strip() for p in paragraphs if p.strip())
                
                return {
                    'full_content': content,
                    'pub_date': pub_date,
                    'author': author
                }
            
            return {'full_content': '', 'pub_date': '', 'author': ''}
            
        except Exception as e:
            logging.error(f"Error extracting content from {url}: {str(e)}")
            return {'full_content': '', 'pub_date': '', 'author': ''}

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
                
                # Process each item in the feed
                for item in channel.findall('item'):
                    try:
                        # Get title without hyperlink
                        title = self._get_element_text(item, 'title')
                        if '(with hyperlink)' in title:
                            title = title.replace('(with hyperlink)', '').strip()
                        
                        # Get description and parse its content
                        description = self._get_element_text(item, 'description')
                        if not description or description.isspace():
                            continue
                            
                        # Split description into lines and clean them
                        lines = [line.strip() for line in description.split('\n') if line.strip()]
                        if not lines:
                            continue
                            
                        # Join all lines with spaces to create single-line content
                        content = ' '.join(lines)
                        
                        article = {
                            'source': 'RTHK',
                            'category': category,
                            'title': title,
                            'link': self._get_element_text(item, 'link'),
                            'description': content,
                            'pub_date': self._get_element_text(item, 'pubDate'),
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
                        logging.error(f"Error parsing article: {str(e)}")
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
        # Create output directory
        output_dir = os.path.abspath('hk_news')
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Created output directory at: {output_dir}")
        
        # Dictionary to store existing articles by source
        existing_articles = {
            'SCMP': set(),
            'HKFP': set(),
            'RTHK': set(),
        }
        
        # Load existing articles from CSV files
        for source in existing_articles.keys():
            filename = os.path.join(output_dir, f'{source.lower()}_news.csv')
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                # Store URLs of existing articles
                existing_articles[source] = set(df['link'].tolist())
                logging.info(f"Loaded {len(existing_articles[source])} existing {source} articles")
        
        # Dictionary to store new articles
        new_articles_by_source = {
            'SCMP': [],
            'HKFP': [],
            'RTHK': [],
        }
        
        # Crawl SCMP
        scmp_crawler = SCMPNewsCrawler()
        scmp_articles = scmp_crawler.parse_feed()
        for article in scmp_articles:
            if article['link'] not in existing_articles['SCMP']:
                new_articles_by_source['SCMP'].append(article)
        
        # Crawl HKFP
        hkfp_crawler = HKFPCrawler()
        hkfp_articles = hkfp_crawler.parse_feed()
        for article in hkfp_articles:
            if article['link'] not in existing_articles['HKFP']:
                new_articles_by_source['HKFP'].append(article)
        
        # Crawl RTHK
        rthk_crawler = RTHKCrawler()
        rthk_articles = rthk_crawler.parse_feed()
        for article in rthk_articles:
            if article['link'] not in existing_articles['RTHK']:
                new_articles_by_source['RTHK'].append(article)
        
        # Process and update each source separately
        dataframes = {}
        for source, new_articles in new_articles_by_source.items():
            filename = os.path.join(output_dir, f'{source.lower()}_news.csv')
            
            if new_articles:
                logging.info(f"Found {len(new_articles)} new {source} articles")
                
                # Create DataFrame for new articles
                new_df = pd.DataFrame(new_articles)
                
                # Clean text columns
                text_columns = ['title', 'description', 'full_content', 'author']
                for col in text_columns:
                    if col in new_df.columns:
                        new_df[col] = new_df[col].astype(str).str.split().str.join(' ')
                
                # Filter for English content
                def is_english(text):
                    if not text:
                        return False
                    return len([c for c in text if ord(c) < 128]) / len(text) > 0.7
                
                new_df = new_df[new_df['full_content'].apply(is_english)]
                
                # Add a category column for HKFP if not present
                if source == 'HKFP':
                    new_df['category'] = 'HKFP'  # Set a default category for HKFP articles
                
                # Sort by publication date and then by category
                if 'pub_date_formatted' in new_df.columns:
                    new_df['pub_date_formatted'] = pd.to_datetime(new_df['pub_date_formatted'], errors='coerce')
                    new_df = new_df.sort_values(by=['pub_date_formatted', 'category'], ascending=[False, True])
                
                # If file exists, append new articles
                if os.path.exists(filename):
                    existing_df = pd.read_csv(filename)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    # Remove duplicates based on link
                    combined_df = combined_df.drop_duplicates(subset='link', keep='first')
                    combined_df.to_csv(filename, index=False, encoding='utf-8-sig')
                    dataframes[source] = combined_df
                    logging.info(f"Updated {filename} with {len(new_df)} new articles")
                else:
                    # Create new file if it doesn't exist
                    new_df.to_csv(filename, index=False, encoding='utf-8-sig')
                    dataframes[source] = new_df
                    logging.info(f"Created {filename} with {len(new_df)} articles")
            else:
                logging.info(f"No new articles found for {source}")
                if os.path.exists(filename):
                    dataframes[source] = pd.read_csv(filename)
                else:
                    dataframes[source] = pd.DataFrame()
        
        return dataframes
            
    except Exception as e:
        logging.error(f"Main execution error: {str(e)}")
        return {}

if __name__ == "__main__":
    dataframes = main()
    
    # Print summary of results
    for source, df in dataframes.items():
        print(f"\n{source} articles:")
        print(f"Total articles: {len(df)}")
        if not df.empty:
            print("\nMost recent articles:")
            if 'pub_date_formatted' in df.columns:
                df_sorted = df.sort_values('pub_date_formatted', ascending=False)
                display_columns = ['title', 'pub_date_formatted']
                print(df_sorted[display_columns].head())
            else:
                display_columns = ['title']
                print(df[display_columns].head())
