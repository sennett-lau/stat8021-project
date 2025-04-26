import os
import json
from openai import OpenAI
import httpx
from dotenv import load_dotenv
import psycopg2
from pgvector.psycopg2 import register_vector
from app import get_db_connection
from data_loader import create_simple_embedding

# Load environment variables
load_dotenv()

# Create a custom HTTP client to handle the proxies parameter
class CustomHTTPClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        # Remove 'proxies' argument if present
        kwargs.pop('proxies', None)  
        super().__init__(*args, **kwargs)

# Initialize OpenAI client with custom HTTP client
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=CustomHTTPClient()
)

def format_articles_for_prompt(news_articles):
    """Format articles for the prompt"""
    articles_json = []
    for article in news_articles:
        articles_json.append({
            "id": article['id'],
            "title": article['title'],
            "content": article['content']
        })
    return json.dumps(articles_json, indent=2)

def generate_summary_with_openai(news_articles):
    """Generate a summary of news articles using OpenAI API"""
    if not news_articles:
        return None
    
    # Format articles for the prompt
    formatted_articles = format_articles_for_prompt(news_articles)
    
    # Prepare the prompt
    prompt = """You are an AI assistant tasked with summarizing a set of news content provided by the user. The set may contain some irrelevant articles or content that does not align with the majority theme. Your job is to:

1. Identify and use only the news content that represents the majority and is thematically similar, ignoring irrelevant or outlier content.
2. Generate a concise summary based on the relevant content.
3. Provide a title for the summary.
4. List 4 TL;DR points highlighting the key takeaways.
5. Identify specific sentences in the summary that can be directly referenced to the provided news articles and include their IDs.
6. Return the results in the exact JSON format specified below.

### Input Format
The news content will be provided as an array of objects in the following format:

[
  {
    "id": "<Unique identifier for the article>",
    "title": "<Title of the news article>",
    "content": "<Full text content of the news article>"
  },
  ...
]

### Output Data Template
Return the output in the following JSON format:

{
  "title": "<A concise and descriptive title for the summarized news>",
  "tldr": [
    "<First key takeaway>",
    "<Second key takeaway>",
    "<Third key takeaway>",
    "<Fourth key takeaway>"
  ],
  "summary": "<A concise summary of the relevant news content, written in 3-5 sentences>",
  "refs": [
    {
      "sentence": "<A specific sentence from the summary>",
      "id": "<The ID of the news article from which the information in the sentence is derived>"
    },
    ...
  ]
}

### Instructions
- Analyze the provided news content, given in the input format [{id, title, content}, ...], to determine the dominant theme or topic.
- Exclude any content that is unrelated or significantly deviates from the majority theme.
- Create a title that captures the essence of the relevant news.
- List 4 TL;DR points that succinctly cover the main points of the relevant content.
- Write a summary in 3-5 sentences that provides an overview of the relevant news, ensuring clarity and brevity.
- For the `refs` field, identify at least 1-3 sentences in the summary that can be directly tied to specific news articles. For each referenced sentence, provide the sentence itself and the `id` of the article from which the information is derived. Ensure the sentence is an exact match from the summary.
- Ensure the output strictly follows the JSON format provided above, with no deviations.
- If the news content is insufficient or unclear, include a note in the summary field indicating the issue, but still adhere to the JSON format.
- If no references can be confidently tied to specific articles, include an empty `refs` array and note the issue in the summary.

Please process the provided news content, given in the specified input format, and return the summarized output in the specified JSON format.

Here are the news articles to summarize:

"""
    prompt += formatted_articles
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Use an appropriate model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}  # Ensure JSON response
        )
        
        # Parse response
        response_content = response.choices[0].message.content
        result = json.loads(response_content)
        
        return result
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

def save_summary_to_db(summary_data, article_ids):
    """Save summary data to the database"""
    if not summary_data:
        return None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Convert tldr list to array format for PostgreSQL
        tldr_array = "{" + ",".join(f'"{item}"' for item in summary_data["tldr"]) + "}"
        
        # Convert article IDs to array format
        article_ids_array = "{" + ",".join(str(id) for id in article_ids) + "}"
        
        # Create embedding for the summary text
        summary_text = summary_data["title"] + " " + summary_data["summary"]
        embedding = create_simple_embedding(summary_text)
        
        # Insert into database
        cur.execute("""
            INSERT INTO summaries (title, tldr, summary, news_articles_ids, embedding)
            VALUES (%s, %s, %s, %s, %s::vector)
            RETURNING id
        """, (
            summary_data["title"],
            tldr_array,
            summary_data["summary"],
            article_ids_array,
            embedding
        ))
        
        summary_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return summary_id
    except Exception as e:
        print(f"Error saving summary to database: {str(e)}")
        return None

def summarize_news_articles(article_ids):
    """
    Generate and save a summary for the provided news articles
    
    Parameters:
    - article_ids: List of news article IDs to summarize
    
    Returns:
    - Dict containing the summary data and the ID of the saved summary
    """
    if not article_ids:
        return {"error": "No article IDs provided"}
    
    try:
        # Get the articles from the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Convert article IDs to string format for SQL IN clause
        ids_str = ",".join(str(id) for id in article_ids)
        
        # Get articles
        cur.execute(f"""
            SELECT id, title, content
            FROM news_articles
            WHERE id IN ({ids_str})
        """)
        
        articles = []
        for row in cur.fetchall():
            articles.append({
                "id": row[0],
                "title": row[1],
                "content": row[2]
            })
        
        cur.close()
        conn.close()
        
        if not articles:
            return {"error": "No articles found with the provided IDs"}
        
        # Generate summary
        summary_data = generate_summary_with_openai(articles)
        
        if not summary_data:
            return {"error": "Failed to generate summary"}
        
        # Save summary to database
        summary_id = save_summary_to_db(summary_data, article_ids)
        
        if not summary_id:
            return {"error": "Failed to save summary to database"}
        
        return {
            "summary_id": summary_id,
            "summary_data": summary_data
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Example usage
    # summary_result = summarize_news_articles([1, 2, 3])
    # print(summary_result)
    pass 