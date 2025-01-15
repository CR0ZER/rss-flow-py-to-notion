# Imports
from utils.notion_blocks import Notion_Block as NB

import json
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from notion_client import Client
from notion_client.errors import APIResponseError


# Tools functions
class Tools:
    def get_rss_links_with_tags(file_path):
        with open(file_path, "r") as file:
            rss_feeds = json.load(file).get("rss_feeds", {})
        return [(link, tag) for tag, links in rss_feeds.items() for link in links]


    def format_date(date_str,  output_format="%Y-%m-%d %H:%M:%S"):
        rss_format = "%a, %d %b %Y %H:%M:%S %z"
        try:
            parsed_date = datetime.strptime(date_str, rss_format)
            return parsed_date.strftime(output_format)
        except ValueError as e:
            return f"Error parsing date: {e}"


    def convert_html_to_blocks(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        blocks = []

        for element in soup.contents:
            if element.name == "p":
                blocks.append(NB.create_notion_paragraph(element.get_text()))
            elif element.name in ["h1", "h2", "h3"]:
                level = int(element.name[1])
                blocks.append(NB.create_notion_heading(element.get_text(), level))
            elif element.name == "a":
                blocks.append(NB.create_notion_link(element.get_text(), element.get("href")))
            elif element.name == "img" and element.get("src"):
                blocks.append(NB.create_notion_image(element.get("src")))
            else:
                if element.string:
                    blocks.append(NB.create_notion_paragraph(element.string))

        return blocks


    def is_date_younger_than_week(date_str):
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return parsed_date > datetime.now() - timedelta(weeks=1)


# Notion functions to interact with the Notion API
class Notion:
    def make_notion_connection():
        with open("config.json", "r") as file:
            config = json.load(file)

        try:
            notion = Client(auth=config["api"])
            return notion, Notion.get_database_id_by_name(notion, config["name"])

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


    def create_notion_page(notion, database_id, title, author, tag, article_date, link, content, content_type):
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
            },
            "Content Type": {
                "select": {
                    "name": content_type
                }
            }
        }

        try:
            notion_content = Tools.convert_html_to_blocks(content)

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