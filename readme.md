<p><a target="_blank" href="https://app.eraser.io/workspace/ZokN063P0oiGNBlOXd2w" id="edit-in-eraser-github-link"><img alt="Edit in Eraser" src="https://firebasestorage.googleapis.com/v0/b/second-petal-295822.appspot.com/o/images%2Fgithub%2FOpen%20in%20Eraser.svg?alt=media&amp;token=968381c8-a7e7-472a-8ed6-4a6626da5501"></a></p>

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
- A `.env`  file with required environment variables
- PostgresQl database
## Installation
1. Clone the repository:git clone https://github.com/akshayanagaraj/Automating-Email-Workflow.git
cd Automating-Email-Workflow
2. Create a python virtual env and activate itpython -m venv env
source env/bin/activate
3. Install dependencies:pip install -r requirements.txt
4. Install all packages using poetrypoetry update
5. Follow the steps in [﻿https://www.geeksforgeeks.org/how-to-read-emails-from-gmail-using-gmail-api-in-python/](https://www.geeksforgeeks.org/how-to-read-emails-from-gmail-using-gmail-api-in-python/)  to create credentials.json file and store here
6. Create a new database and Set up the `.env`  file with the following variables:GMAIL_CREDENTIALS_PATH=path/to/credentials.json
GMAIL_TOKEN_PATH=path/to/token.json

DB_HOST=localhost
DB_PORT=5432
DB_NAME=db_name
DB_USER=user_name
DB_PASSWORD=password
## Usage
Run the application with the following command:

```bash
poetry run python -m gmail_rules_engine.main --env-file .env --rules-file rules.json --max-results 100 --interval 5
```
Run with this command to run only once

```bash
poetry run python -m gmail_rules_engine.main --run-once
```
### Command-Line Arguments
- `--env-file` : Path to the `.env`  file (default: `.env` ).
- `--rules-file` : Path to the rules JSON file (default: `rules.json` ).
- `--max-results` : Maximum number of emails to fetch (default: 100).
- `--interval` : Interval in minutes to run the job (default: 5).
- `--log-level` : Logging level (default: `INFO` ).
- `--run-once` : Run the job once and exit.




<!-- eraser-additional-content -->
## Diagrams
<!-- eraser-additional-files -->
<a href="/readme-Email Processing Flowchart-1.eraserdiagram" data-element-id="BYQOn-IcwTsJldERUmGA3"><img src="/.eraser/ZokN063P0oiGNBlOXd2w___8HMLcgJ8mxXYRBPHO4tqNtJVk042___---diagram----5707400014125a6de5ef8df58715295c-Email-Processing-Flowchart.png" alt="" data-element-id="BYQOn-IcwTsJldERUmGA3" /></a>
<!-- end-eraser-additional-files -->
<!-- end-eraser-additional-content -->
<!--- Eraser file: https://app.eraser.io/workspace/ZokN063P0oiGNBlOXd2w --->
