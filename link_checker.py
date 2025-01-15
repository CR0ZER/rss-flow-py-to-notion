from utils.utils import Tools, Notion
import sys
import feedparser


def check_link(link):
    try:
        feed = feedparser.parse(link)

        print(f"[INFO] Link checked: {link}")
        print(f"[INFO] Number of entries: {feed.entries.__len__()}")
        content_type = "Full article" if hasattr(feed.entries[0], "content") else "Only summary"
        print(f"[INFO] Content type: {content_type}")
        
        print(f"[INFO] First entry:")
        print(f"""
Title: {feed.entries[0].title}
Author: {feed.entries[0].author}
Date: {Tools.format_date(feed.entries[0].published)}
Link: {feed.entries[0].link}
Content: {feed.entries[0].content[0].value if hasattr(feed.entries[0], "content") else feed.entries[0].summary}
""")

    except Exception as e:
        print(f"[ERROR] Error while parsing the link {link}")
        print(f"[ERROR] {e}")
        print(feed.entries[0].keys())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python link_checker.py <link>")
        sys.exit(1)

    link = sys.argv[1]

    check_link(link)