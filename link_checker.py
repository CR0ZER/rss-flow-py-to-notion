import sys
from datetime import datetime, timedelta
import feedparser


def is_date_younger_than_week(date_str):
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return parsed_date > datetime.now() - timedelta(weeks=1)


def format_date(date_str,  output_format="%Y-%m-%d %H:%M:%S"):
    rss_format = "%a, %d %b %Y %H:%M:%S %z"
    try:
        parsed_date = datetime.strptime(date_str, rss_format)
        return parsed_date.strftime(output_format)
    except ValueError as e:
        return f"Error parsing date: {e}"


def check_link(link):
    try:
        feed = feedparser.parse(link)
        print(f"Number of entries (all): {feed.entries.__len__()}")
        i = 0
        for entry in feed.entries:
            if is_date_younger_than_week(format_date(entry.published)):
                i += 1
                print(f"""
Title: {entry.title}
Author: {entry.author}
Link: {entry.link}
Published: {entry.published}
Content: {entry.content[0].value if hasattr(entry, "content") else entry.summary}
                """)
        print(f"Number of entries (younger than a week): {i}")

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