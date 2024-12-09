import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import whois
import os
import logging
import pytz
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, filename='domain_check.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
SENDER_EMAIL = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
RECIPIENT_EMAILS = os.getenv('RECIPIENT_EMAILS', '').split(',')

ALERT_THRESHOLDS = [30, 7, 3, 1]  # Set alert thresholds in days

# Load domain list from file
def load_domains(file_path='domains.json'):
    try:
        file_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                domains = json.load(f)
                # Check if domains is a list, if so return it directly. Otherwise try to access the 'domains' key
                if isinstance(domains, list):
                    logging.info(f"Loaded domains from {file_path}")
                    return domains
                elif isinstance(domains, dict) and 'domains' in domains:
                    logging.info(f"Loaded domains from {file_path}")
                    return domains['domains']
                else:
                    logging.error(f"Invalid JSON format in {file_path}")
                    return []
        else:
            logging.error(f"domains.json not found at {file_path}")
            return []
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {file_path}: {e}")
        return []
    except Exception as e:
        logging.error(f"Failed to load domain list: {e}")
        return []

# Function to fetch domain details using whois
def get_domain_info(domain):
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
        expiry_date = w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date
        last_updated = w.updated_date[0] if isinstance(w.updated_date, list) else w.updated_date
        registrar_info = w.registrar

        # Calculate days to expiry
        if expiry_date:
            days_to_expiry = (expiry_date - datetime.now()).days
            days_to_expiry = days_to_expiry if days_to_expiry >= 0 else "Expired"
        else:
            days_to_expiry = "N/A"

        return {
            "domain": domain,
            "creation_date": creation_date.strftime("%A, %d %B %Y") if creation_date else "N/A",
            "expiry_date": expiry_date.strftime("%A, %d %B %Y") if expiry_date else "N/A",
            "last_updated": last_updated.strftime("%A, %d %B %Y") if last_updated else "N/A",
            "registrar_info": registrar_info,
            "days_to_expiry": days_to_expiry
        }
    except Exception as e:
        logging.error(f"Failed to fetch details for {domain}: {e}")
        return {
            "domain": domain,
            "creation_date": "N/A",
            "expiry_date": "N/A",
            "last_updated": "N/A",
            "registrar_info": "N/A",
            "days_to_expiry": "N/A"
        }

# Function to create and send summary email with domain information in a table format
def send_summary_email(domain_info_list):
    html_content = """
    <html>
        <body>
            <h2>Domain Expiration Summary</h2>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <thead>
                    <tr>
                        <th>Domain</th>
                        <th>Creation Date</th>
                        <th>Last Updated</th>
                        <th>Expiry Date</th>
                        <th>Registrar</th>
                        <th>Days to Expiry</th>
                    </tr>
                </thead>
                <tbody>
    """
    for info in domain_info_list:
        days_display = (
            "Expired" if info['days_to_expiry'] == "Expired" else 
            info['days_to_expiry'] if info['days_to_expiry'] != "N/A" else "N/A"
        )
        html_content += f"""
        <tr>
            <td>{info['domain']}</td>
            <td>{info['creation_date']}</td>
            <td>{info['last_updated']}</td>
            <td>{info['expiry_date']}</td>
            <td>{info['registrar_info']}</td>
            <td>{days_display}</td>
        </tr>
        """
    html_content += """
                </tbody>
            </table>
        </body>
    </html>
    """

    # Set up email message
    msg = MIMEMultipart("alternative")
    msg['Subject'] = "Domain Expiration Summary"
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECIPIENT_EMAILS)
    part1 = MIMEText(html_content, "html")
    msg.attach(part1)

    # Send email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS, msg.as_string())
    logging.info("Summary email sent successfully.")

# Main function to handle domain checks and email alerts
def main(all_domains=False, single_domains=None):
    # Load domains from file if checking all domains or use the specified list
    if all_domains:
        domains = load_domains()
    else:
        domains = single_domains
    if not domains:
        logging.warning("No domains to process.")
        return

    # Collect info for all domains
    domain_info_list = [get_domain_info(domain) for domain in domains]

    # Check if any domain meets the alert thresholds
    send_email = any(
        isinstance(info['days_to_expiry'], int) and info['days_to_expiry'] in ALERT_THRESHOLDS
        for info in domain_info_list
    ) or single_domains

    if send_email:
        send_summary_email(domain_info_list)

if __name__ == "__main__":
    # Parse arguments for manual or full check
    parser = argparse.ArgumentParser()
    parser.add_argument('--all_domains', action='store_true', help="Check all domains from the file")
    parser.add_argument('--domains', type=str, help="Comma-separated list of domains to check")
    args = parser.parse_args()

    # Parse domains argument if provided
    domains_to_check = args.domains.split(',') if args.domains else None
    main(all_domains=args.all_domains, single_domains=domains_to_check)
