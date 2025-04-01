# Gmail Rules Engine

The Gmail Rules Engine is a Python-based application that automates the process of fetching emails from Gmail, storing them in a database, and applying user-defined rules to perform actions on those emails.

## Features

- Fetch emails from Gmail using the Gmail API.
- Store emails in a database for processing.
- Apply rules defined in a JSON file to automate actions on emails.
- Schedule the job to run at regular intervals or execute it once.

## Prerequisites

- Python 3.8 or higher
- Gmail API credentials
- A `.env` file with required environment variables
- PostgresQl database

## Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:akshayanagaraj/Automating-Email-Workflows.git
   cd gmail_rules_engine
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the `.env` file with the following variables:
   ```
   GMAIL_CREDENTIALS_PATH=path/to/credentials.json
   GMAIL_TOKEN_PATH=path/to/token.json
   DATABASE_URL=sqlite:///emails.db
   ```

4. Create a `rules.json` file to define your email processing rules.

## Usage

Run the application with the following command:
```bash
python main.py --env-file .env --rules-file rules.json --max-results 100 --interval 5
```

### Command-Line Arguments

- `--env-file`: Path to the `.env` file (default: `.env`).
- `--rules-file`: Path to the rules JSON file (default: `rules.json`).
- `--max-results`: Maximum number of emails to fetch (default: 100).
- `--interval`: Interval in minutes to run the job (default: 5).
- `--log-level`: Logging level (default: `INFO`).
- `--run-once`: Run the job once and exit.

