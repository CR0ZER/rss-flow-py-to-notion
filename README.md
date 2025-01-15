**Summary**

This script parses articles chosen by the user from various categories (e.g., AI, ML, Tech, Sports, etc.) and creates a Notion page in a database for each article. The workflow is automated using GitHub Actions, allowing users to fetch and store RSS feed data in Notion effortlessly. If the article is one week old, the script will automatically delete the page.

**Table of Contents**

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Run Locally](#run-locally)
  - [Using GitHub Actions](#using-github-actions)
  - [Configuration](#configuration)
  - [Validate Links](#validate-links)
- [GitHub Actions Workflow](#github-actions-workflow)
  - [Workflow Used/Example](#workflow-usedexample)
- [Contributing](#contributing)

## Features

- **Category-Based Parsing**: Organize articles by tags like `AI`, `ML`, `Tech`, and more.
- **Notion Integration**: Automatically create Notion pages for parsed articles.
- **Automated Workflow**: Runs daily using GitHub Actions or can be triggered manually.
- **Article Deletion**: Automatically delete articles older than one week.
- **Link Validation**: Ensure that only valid RSS links are processed using `link_checker.py`.

## Prerequisites

1. **Python 3.12.1 or Later**: Ensure Python is installed on your local machine.
2. **Notion Integration**: Create an integration and save the token from [Notion](https://www.notion.so/my-integrations) ([Create Integration](https://youtu.be/Hk7Vk_v4yfo?si=cffkvCVtfW77ItVr&t=18)). Then add your integration to your Notion database ([Add Integration to databse](https://youtu.be/Hk7Vk_v4yfo?si=cwD8YTzW2e3FlFWf&t=107) + first comment).
3. **GitHub Secrets Setup**:
   - Add a secret called `CONFIG_JSON` containing the following:
     ```json
     {
       "api": "your-notion-api-key",
       "name": "your-notion-database-name"
     }
     ```

## Installation

To set up the repository locally:

1. Clone the repository:

```bash
git clone https://github.com/CR0ZER/rss-flow-py-to-notion
cd rss-flow-py-to-notion
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

To use the script, you will have to manually add these properties in your database:
- Change the `Name` property to `Title`.
- `Category` - Property type: *Select* - Options: `tech news`, `data science`, `machine learning`, `ai`.
- `Content Type` - Property type: *Select* - Options: `Full article`, `Summary`.
- `Author` - Property type: *Text*.
- `Article Date` - Property type: *Date*.
- `Created Time` - Property type: *Created Time* (automatic property for page creation date).
- `Link` - Property type: *URL*.

*Do not change property's names.*

*You can also add more properties in your Notion database, but the script will not fill them.*

### Run Locally

1. [Add your RSS feed links](#configuration) to the `rss_links.json` file.
2. Run the script:

```bash
python feed_to_notion.py
```

### Using GitHub Actions

1. Ensure the workflow file (`.github/workflows/rss_feed_to_notion.yml`) is in place.
2. Push the repository to GitHub.
3. The script will:
   - Run daily at 1 AM UTC (configurable in the workflow file).
   - Fetch articles and create Notion pages.

### Configuration

To update your RSS feed links, modify your `rss_links.json` structure as follows:
```json
{
    "rss_feeds": {
        "subject 1": [
            "link 1",
            "link 2"...
        ],
        "subject 2": [
            "link 1",
            "link 2"...
        ]...
    }
}
```

*Do not forget to add or change subjects in the `Category` property in your Notion database.*

### Validate Links

You can use by yourself the script `link_checker.py` to check if the RSS feed link is valid:

```bash
python link_checker.py <link>
```

If the program don't return an error, the link is valid.

## GitHub Actions Workflow

The included GitHub Actions workflow file (`feed_to_notion_workflow.yml`) is set up to:

- Install Python and dependencies.
- Create a config.json file from the CONFIG_JSON GitHub secret.
- Run the feed_to_notion.py script daily or on manual triggers.

### Workflow Used/Example

```yaml
name: RSS Feed to Notion

on:
  # Run daily at 1 AM UTC
  schedule:
    - cron: '0 0 * * *'
  
  # Manually trigger the workflow
  workflow_dispatch:

jobs:
  sync-rss-to-notion:
    runs-on: ubuntu-latest

    steps:
      # Checkout the repository
      - uses: actions/checkout@v4

      # Set up Python 3.12.1
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12.1'

      # Install dependencies
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      # Create config.json from secrets
      - name: Create config.json
        env:
          CONFIG_JSON: ${{ secrets.CONFIG_JSON }}
        run: echo $CONFIG_JSON > config.json

      # Run the script
      - name: Run the script
        run: |
          python feed_to_notion.py
```

## Contributing

Feel free to fork this repository and submit pull requests. Ensure you follow these steps:

1. Fork the repository.
2. Make your changes.
3. Test thoroughly.
4. Submit a pull request with a clear description.

If you have any questions or suggestions, feel free to open an issue.