class Notion_Block:
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