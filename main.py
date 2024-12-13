import json
from datetime import datetime
import feedparser
from notion_client import Client
from notion_client.errors import APIResponseError
from bs4 import BeautifulSoup


def get_rss_flow_links():
    rss_links = []
    with open("rss_links.txt", "r") as file:
        for line in file:
            rss_links.append(line.strip())
    return rss_links


def make_notion_connection():
    with open("config.json", "r") as file:
        config = json.load(file)

    try:
        notion = Client(auth=config["api"])
        
        return notion, get_database_id(notion)

    except APIResponseError as e:
        print(f"[ERROR] Error while connecting to Notion: {e}")
        return None


def get_database_id(notion):
    try:
        search_results = notion.search(
            filter={
                "property": "object",
                "value": "database"
            }
        )
        
        if not search_results['results']:
            print("No databases found.")
            exit()
        
        databases = []
        for db in search_results['results']:
            db_title = db['title'][0]['plain_text'] if db['title'] else 'Untitled Database'
            db_id = db['id']
            
            databases.append({
                'title': db_title,
                'id': db_id
            })
        
        return databases[0]["id"]
    
    except Exception as e:
        print(f"An error occurred: {e}")
        exit()


def format_date(date_str,  output_format="%Y-%m-%d %H:%M:%S"):
    rss_format = "%a, %d %b %Y %H:%M:%S %z"
    try:
        parsed_date = datetime.strptime(date_str, rss_format)
        # Format the date into the desired format
        return parsed_date.strftime(output_format)
    except ValueError as e:
        return f"Error parsing date: {e}"
    

def convert_html_to_notion_blocks(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    def create_notion_paragraph(text):
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": text.strip()
                    }
                }]
            }
        }

    def create_notion_heading(text, level):
        return {
            "object": "block",
            "type": f"heading_{level}",
            f"heading_{level}": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": text.strip()
                    }
                }]
            }
        }

    def create_notion_link(text, url):
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": text,
                        "link": {"url": url}
                    }
                }]
            }
        }

    blocks = []

    for element in soup.contents:
        if element.name == "p":
            blocks.append(create_notion_paragraph(element.get_text()))
        elif element.name in ["h1", "h2", "h3"]:
            level = int(element.name[1])  # Extract heading level
            blocks.append(create_notion_heading(element.get_text(), level))
        elif element.name == "a":
            blocks.append(create_notion_link(element.get_text(), element.get("href")))
        else:
            if element.string:
                blocks.append(create_notion_paragraph(element.string))

    return blocks


def create_notion_page(notion, database_id, title, author, article_date, link, content):
    parsed_article_date = datetime.strptime(article_date, "%Y-%m-%d %H:%M:%S")

    page_properties = {
        "title": {
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": title
                    }
                }
            ]
        },
        "Author": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": author
                    }
                }
            ]
        },
        "Article Date": {
            "date": {
                "start": parsed_article_date.isoformat()
            }
        },
        "Link": {
            "url": link
        }
    }

    try:
        notion_content = convert_html_to_notion_blocks(content)

        notion.pages.create(
            parent={"database_id": database_id},
            properties=page_properties,
            children=notion_content
        )
        print(f"[INFO] New page created: {title}")

    except APIResponseError as e:
        print(f"[ERROR] Error while creating a new page: {e}")
        return None


def does_page_exist(notion, database_id, page_title) -> bool:
    query = notion.databases.query(
        **{
            "database_id": database_id,
            "filter": {
                "property": "title",
                "rich_text": {
                    "equals": page_title
                }
            }
        }
    )
    return True if query["results"] else False


if __name__ == "__main__":
    links = get_rss_flow_links()

    notion, database_id = make_notion_connection()

    feedparser.USER_AGENT = "feedparser/6.0.11 +https://github.com/kurtmckee/feedparser/"

    for link in links:
        try:
            feed = feedparser.parse(link)
            if feed.entries.__len__() == 0:
                continue
        
            for entry in feed.entries:
                title = entry.title
                author = entry.author
                date = format_date(entry.published)
                link = entry.link
                content = entry.content[0].value
            
            if not does_page_exist(notion, database_id, title):
                create_notion_page(
                    notion=notion,
                    database_id=database_id,
                    title=title,
                    author=author,
                    article_date=date,
                    link=link,
                    content=content
                )

        except:
            print("[ERROR] Error while parsing for link: ", link)
            continue