###########################################
# This project have been created by @CR0ZER
# https://github.com/CR0ZER/
###########################################


from utils.utils import Tools, Notion
import feedparser


if __name__ == "__main__":
    links_with_tags = Tools.get_rss_links_with_tags("rss_links.json")

    notion, database_id = Notion.make_notion_connection()

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
                    date = Tools.format_date(entry.published)
                    link = entry.link
                    content = entry.content[0].value if hasattr(entry, "content") else entry.summary
                
                    if not Notion.does_page_exist(notion, database_id, title) and Tools.is_date_younger_than_week(date):
                        Notion.create_notion_page(
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

        Notion.archive_old_pages(notion, database_id)