# Domain Watchdog

This repository contains a Python-based tool and GitHub Action to monitor domain expiry dates.<br>
The tool reads a list of domains, retrieves domain information (such as creation, expiry, and last updated dates), and sends a daily email report listing the details.<br>
This tool is designed to help track domain health and avoid unexpected expirations.

## Features

- **Daily Domain Expiry Check**: Checks a list of domains for expiry information.
- **Email Notification**: Sends a detailed report via email with:
  - Domain Name
  - Creation Date
  - Expiry Date
  - Last Updated Date
  - Registrar Info
  - Days to Expiry
- **Error Logging**: Logs any errors encountered while fetching domain data.
- **Multiple Recipients**: Allows specifying multiple email recipients.
- **Parallel Processing**: Uses concurrent processing to improve performance and avoid timeouts.

## Repository Structure
```bash
domain-expiry-check/
├── .github/
│   └── workflows/
│       └── domain-checks.yml   # GitHub Action workflow file
├── check_domains.py           # Python script for domain checks
├── .gitignore                 # Ignores sensitive files
├── requirements.txt            # Github Action requirements needed to be installed
└── domains.json       # Placeholder file for domain list
```

## Setup Instructions

### Step 1: Add Domain List

1. Create a file named `domains.json` (in the root of the repository, excluded by `.gitignore`) containing the domains you want to monitor, with each domain on a new line:

`example.com mywebsite.net anotherdomain.org`

2. Alternatively, refer to the placeholder file `domains.json` to see the expected format.

### Step 2: Configure GitHub Secrets

To keep sensitive information private, store email credentials and SMTP settings as GitHub Secrets.<br>
Go to your repository’s **Settings > Secrets and variables > Actions > New repository secret** and add the following secrets:

| Secret Name         | Description                                       |
|---------------------|---------------------------------------------------|
| `EMAIL_SENDER`      | The email address used to send reports.           |
| `EMAIL_PASSWORD`    | The password for the sender email account. Use an app-specific password if necessary. |
| `SMTP_SERVER`       | The SMTP server address (e.g., `smtp.example.com`). |
| `SMTP_PORT`         | The SMTP server port (default is 587 for TLS).    |
| `RECIPIENT_EMAILS`  | Comma-separated list of email addresses to receive the report (e.g., `email1@example.com,email2@example.com`). |

### Step 3: Customize the GitHub Action (Optional)

The GitHub Action is set to run daily at midnight UTC.<br> 
You can adjust this by modifying the cron schedule in `.github/workflows/domain-check.yml`:

```yaml
on:
schedule:
 - cron: "0 0 * * *"  # Runs every day at midnight UTC
workflow_dispatch:      # Allows manual trigger
```

### Usage
Once configured, the GitHub Action will automatically:

- Check the domains listed in domains.txt.
- Generate a report summarizing domain details.
- Send the report to specified recipients via email.

Manual Run
You can manually trigger the workflow by going to the Actions tab in GitHub, selecting the Domain Expiry Check workflow, and clicking Run workflow.<br>
The Github Action have to be enabled to work (manually or as scpecified in cron settings).

Sample Email Report
The report email will look something like this:

```
Subject: Daily Domain Expiry Check

Domain Expiry Report

Domain: example.com
Creation Date: Monday, 01 January 2018
Expiry Date: Tuesday, 01 January 2025
Last Updated: Monday, 01 January 2023
Registrar: Example Registrar
Days to Expire: 365

Domain: mywebsite.net
Creation Date: Thursday, 12 March 2015
Expiry Date: Saturday, 12 March 2023
Last Updated: Friday, 10 March 2021
Registrar: Another Registrar
Days to Expire: 10

...
```

### Limitations
- GitHub Secrets: Ensure secrets are correctly configured, as they won’t show in the logs for security reasons. Misconfigurations might cause email errors without detailed output.
- Domain Availability: If a domain is unavailable or its information cannot be retrieved, an error will be logged, and the domain will be skipped in the report.
- Rate Limits: Some WHOIS servers may rate-limit requests. The tool uses ThreadPoolExecutor to parallelize domain checks, which may help avoid timeouts but could still be affected by server limitations.

### Troubleshooting
- Email Sending Issues. Ensure that the:
  - EMAIL_SENDER,
  - EMAIL_PASSWORD,
  - SMTP_SERVER,
  - and SMTP_PORT
  secrets are correctly configured. Some email providers may require app-specific passwords or additional security settings.
- Domain Check Failures: Check domain_check.log for error messages if a domain fails to load. WHOIS rate-limiting or network issues can sometimes prevent successful domain data retrieval.
- Environment-Specific Variables: Be cautious when printing environment variables in logs to avoid accidental exposure of sensitive data.
