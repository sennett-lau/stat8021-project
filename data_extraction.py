import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import re
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SCMPNewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Create output directory
        self.output_dir = os.path.abspath('scmp_news')
        os.makedirs(self.output_dir, exist_ok=True)
        logging.info(f"Created output directory at: {self.output_dir}")

    def parse_rss_feed(self, rss_file):
        """Parse RSS feed from file"""
        try:
            # Parse the RSS feed
            tree = ET.parse(rss_file)
            root = tree.getroot()
            channel = root.find('channel')
            
            # Get channel information
            feed_info = {
                'title': channel.find('title').text if channel.find('title') is not None else '',
                'link': channel.find('link').text if channel.find('link') is not None else '',
                'description': channel.find('description').text if channel.find('description') is not None else '',
                'language': channel.find('language').text if channel.find('language') is not None else ''
            }
            
            articles = []
            # Process each item in the feed
            for item in channel.findall('item'):
                article = {
                    'feed_title': feed_info['title'],
                    'feed_link': feed_info['link'],
                    'feed_description': feed_info['description'],
                    'feed_language': feed_info['language'],
                    
                    # Item specific information
                    'title': item.find('title').text if item.find('title') is not None else '',
                    'link': item.find('link').text if item.find('link') is not None else '',
                    'description': item.find('description').text if item.find('description') is not None else '',
                    'pub_date': item.find('pubDate').text if item.find('pubDate') is not None else '',
                    'guid': item.find('guid').text if item.find('guid') is not None else '',
                    'dc_creator': item.find('{http://purl.org/dc/elements/1.1/}creator').text 
                        if item.find('{http://purl.org/dc/elements/1.1/}creator') is not None else '',
                    'author': item.find('author').text if item.find('author') is not None else ''
                }
                
                # Extract media content
                media_content = item.find('{http://www.rssboard.org/media-rss}content')
                if media_content is not None:
                    article['media_url'] = media_content.get('url', '')
                    article['media_type'] = media_content.get('type', '')
                    article['media_width'] = media_content.get('width', '')
                    article['media_height'] = media_content.get('height', '')
                
                # Extract enclosure
                enclosure = item.find('enclosure')
                if enclosure is not None:
                    article['enclosure_url'] = enclosure.get('url', '')
                    article['enclosure_type'] = enclosure.get('type', '')
                    article['enclosure_length'] = enclosure.get('length', '')
                
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
                
                # Extract detailed content if link is available
                if article['link']:
                    logging.info(f"Extracting content from {article['link']}")
                    detailed_content = self.extract_article_content(article['link'])
                    article.update(detailed_content)
                
                articles.append(article)
                logging.info(f"Processed article: {article['title']}")
            
            return articles
            
        except Exception as e:
            logging.error(f"Error parsing RSS feed: {str(e)}")
            return []

    def extract_article_content(self, url):
        """Extract detailed content from article URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content = ''
            content_div = soup.find('div', class_='article-body')
            if content_div:
                paragraphs = content_div.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs])
            
            return {
                'full_content': content
            }
            
        except Exception as e:
            logging.error(f"Error extracting content from {url}: {str(e)}")
            return {'full_content': ''}

    def save_to_csv(self, articles, filename='scmp_articles.csv'):
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

def main():
    try:
        crawler = SCMPNewsCrawler()
        articles = crawler.parse_rss_feed('feed.rss')
        
        if articles:
            # Create DataFrame
            df = pd.DataFrame(articles)
            
            # Save to CSV in the current directory
            df.to_csv('hk_news.csv', index=False, encoding='utf-8-sig')
            logging.info(f"Successfully saved {len(df)} articles to hk_news.csv")
            
            # Display first few rows to verify
            print("\nFirst few rows of the saved data:")
            print(df.head())
        else:
            logging.warning("No articles were found to save")
            
    except Exception as e:
        logging.error(f"Main execution error: {str(e)}")

if __name__ == "__main__":
    main()
