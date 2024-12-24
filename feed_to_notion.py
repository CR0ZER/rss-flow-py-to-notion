import json
from datetime import datetime, timedelta
import feedparser
from notion_client import Client
from notion_client.errors import APIResponseError
from bs4 import BeautifulSoup


def get_rss_links_with_tags(file_path):
    with open(file_path, "r") as file:
        rss_feeds = json.load(file).get("rss_feeds", {})
    return [(link, tag) for tag, links in rss_feeds.items() for link in links]


def make_notion_connection():
    with open("config.json", "r") as file:
        config = json.load(file)

    try:
        notion = Client(auth=config["api"])
        return notion, get_database_id_by_name(notion, config["name"])

    except APIResponseError as e:
        print(f"[ERROR] Error while connecting to Notion: {e}")
        return None


def get_database_id_by_name(notion, database_name):
    try:
        search_results = notion.search(
            query=database_name,
            filter={
                "property": "object",
                "value": "database"
            }
        )
        return search_results['results'][0]['id']
    
    except APIResponseError as e:
        print(f"[ERROR] Error while searching for database: {e}")
        return None


def format_date(date_str,  output_format="%Y-%m-%d %H:%M:%S"):
    rss_format = "%a, %d %b %Y %H:%M:%S %z"
    try:
        parsed_date = datetime.strptime(date_str, rss_format)
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

    def create_notion_image(url):
        return {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {
                    "url": url
                }
            }
        }

    blocks = []

    for element in soup.contents:
        if element.name == "p":
            blocks.append(create_notion_paragraph(element.get_text()))
        elif element.name in ["h1", "h2", "h3"]:
            level = int(element.name[1])
            blocks.append(create_notion_heading(element.get_text(), level))
        elif element.name == "a":
            blocks.append(create_notion_link(element.get_text(), element.get("href")))
        elif element.name == "img" and element.get("src"):
            blocks.append(create_notion_image(element.get("src")))
        else:
            if element.string:
                blocks.append(create_notion_paragraph(element.string))

    return blocks


def create_notion_page(notion, database_id, title, author, tag, article_date, link, content):
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
        },
        "Category": {
            "select": {
                "name": tag
            }
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


def does_page_exist(notion, database_id, page_title):
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


def archive_old_pages(notion, database_id):
    one_week_date = datetime.now() - timedelta(weeks=1)

    try:
        query_result = notion.databases.query(
            **{
                "database_id": database_id,
                "filter": {
                    "property": "Article Date",
                    "date": {
                        "before": one_week_date.isoformat()
                    }
                }
            }
        ).get("results", [])
    except APIResponseError as e:
        print(f"[ERROR] Error while querying for pages: {e}")
        return None

    for page in query_result:
        page_id = page["id"]
        try:
            notion.pages.update(
                **{
                    "page_id": page_id,
                    "archived": True
                }
            )
            print(f"[INFO] Page archived: {page['id']}")
        except APIResponseError as e:
            print(f"[ERROR] Error while archiving a page: {e}")
            continue


def is_date_younger_than_week(date_str):
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return parsed_date > datetime.now() - timedelta(weeks=1)


if __name__ == "__main__":
    links_with_tags = get_rss_links_with_tags("rss_links.json")

    notion, database_id = make_notion_connection()

    feedparser.USER_AGENT = "feedparser/6.0.11 +https://github.com/kurtmckee/feedparser/"

    if notion and database_id:
        for link_, tag_ in links_with_tags:
            try:
                feed = feedparser.parse(link_)
                if feed.entries.__len__() == 0:
                    print(f"[ERROR] No entries found for link: {link_}")
                    continue
            
                for entry in feed.entries:
                    title = entry.title
                    author = entry.author
                    tag = tag_
                    date = format_date(entry.published)
                    link = entry.link
                    content = entry.content[0].value if hasattr(entry, "content") else entry.summary
                
                    if not does_page_exist(notion, database_id, title) and is_date_younger_than_week(date):
                        create_notion_page(
                            notion=notion,
                            database_id=database_id,
                            title=title,
                            author=author,
                            tag=tag,
                            article_date=date,
                            link=link,
                            content=content
                        )

            except:
                print("[ERROR] Error while parsing for link: ", link)
                continue

        archive_old_pages(notion, database_id)