import os
import sys
import argparse
from datetime import datetime

# Local imports
from scraper import parse_all_subjects
from report_builder import generate_markdown_report, generate_html_report
from email_sender import send_weekly_email, load_config

import subprocess
import shutil

REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')

def ensure_reports_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_pdf_from_html(html_path, pdf_path):
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome_path):
        try:
            user_data_dir = "/tmp/chrome_pdf_user_data"
            os.makedirs(user_data_dir, exist_ok=True)
            cmd = [
                chrome_path,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                f"--user-data-dir={user_data_dir}",
                f"--print-to-pdf={pdf_path}",
                f"file://{os.path.abspath(html_path)}"
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            print(f" Saved Printable PDF Report: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"[PDF GENERATION WARNING] Headless Chrome PDF generation error: {e}")
    return None

def generate_png_from_html(html_path, png_path):
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome_path):
        try:
            user_data_dir = "/tmp/chrome_png_user_data"
            os.makedirs(user_data_dir, exist_ok=True)
            cmd = [
                chrome_path,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--window-size=1200,1600",
                f"--user-data-dir={user_data_dir}",
                f"--screenshot={png_path}",
                f"file://{os.path.abspath(html_path)}"
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            print(f" Saved Concise 1-Page PNG Report Graphic: {png_path}")
            return png_path
        except Exception as e:
            print(f"[PNG GENERATION WARNING] Headless Chrome PNG generation error: {e}")
    return None

def run_agent(send_email=False, print_to_stdout=False):
    print("=" * 60)
    print("🤖 Starting DU Weekly Agent Run...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Scrape Live Site
    print("[1/3] Scraping DU Google Sites network...")
    scraped_data = parse_all_subjects()

    # 2. Build Reports
    print("[2/3] Generating printable 1-page HTML, Markdown, PDF & PNG checklist reports...")
    md_report = generate_markdown_report(scraped_data)
    html_report = generate_html_report(scraped_data)

    ensure_reports_dir()
    date_stamp = datetime.now().strftime('%Y_%m_%d')
    md_path = os.path.join(REPORTS_DIR, f"report_{date_stamp}.md")
    html_path = os.path.join(REPORTS_DIR, f"report_{date_stamp}.html")
    pdf_path = os.path.join(REPORTS_DIR, f"report_{date_stamp}.pdf")
    png_path = os.path.join(REPORTS_DIR, f"report_{date_stamp}.png")
    latest_html_path = os.path.join(REPORTS_DIR, "latest_report.html")
    latest_pdf_path = os.path.join(REPORTS_DIR, "latest_report.pdf")
    latest_png_path = os.path.join(REPORTS_DIR, "latest_report.png")
    latest_json_path = os.path.join(REPORTS_DIR, "latest_data.json")

    import json
    with open(latest_json_path, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)

    with open(latest_html_path, 'w', encoding='utf-8') as f:
        f.write(html_report)

    print(f" Saved Markdown Report: {md_path}")
    print(f" Saved Printable HTML Report: {html_path}")
    print(f" Saved Structured JSON Dataset: {latest_json_path}")

    # Generate 1-page PDF document
    generated_pdf = generate_pdf_from_html(latest_html_path, latest_pdf_path)
    if generated_pdf and os.path.exists(latest_pdf_path):
        shutil.copyfile(latest_pdf_path, pdf_path)

    # Generate concise 1-page PNG image graphic (Option 1 Dashboard format)
    generated_png = generate_png_from_html(latest_html_path, latest_png_path)
    if generated_png and os.path.exists(latest_png_path):
        shutil.copyfile(latest_png_path, png_path)

    if print_to_stdout:
        print("\n" + "=" * 60)
        print("REPORT PREVIEW:")
        print("=" * 60)
        print(md_report)
        print("=" * 60 + "\n")

    # 3. Email Delivery
    attachments_to_send = []
    if os.path.exists(latest_pdf_path):
        attachments_to_send.append(latest_pdf_path)
    if os.path.exists(latest_png_path):
        attachments_to_send.append(latest_png_path)
    if not attachments_to_send:
        attachments_to_send = [latest_html_path]

    print(f"[3/3] Handling email delivery (attaching {[os.path.basename(a) for a in attachments_to_send]})...")
    if send_email:
        subject = f"📋 DU Weekly Digest & Checklist ({scraped_data.get('scrape_date', date_stamp)})"
        success, msg = send_weekly_email(subject, html_report, md_report, attachment_path=attachments_to_send)
        print(f"Email Dispatch Result: {msg}")
    else:
        cfg = load_config()
        if cfg.get("sender_email") and cfg.get("recipient_email"):
            subject = f"📋 DU Weekly Digest & Checklist ({scraped_data.get('scrape_date', date_stamp)})"
            success, msg = send_weekly_email(subject, html_report, md_report, attachment_path=attachments_to_send)
        else:
            print("[INFO] Email credentials not configured in config.json. Report saved locally.")

    print("\n Agent run complete!")
    return html_path, md_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="DU 5th Grade Weekly Agent")
    parser.add_argument('--run-now', action='store_true', help="Run scraper and generate reports now")
    parser.add_argument('--send-email', action='store_true', help="Force sending email digest")
    parser.add_argument('--print-report', action='store_true', help="Print markdown report to terminal")
    
    args = parser.parse_args()

    # Default to running now if no flags specified
    run_agent(send_email=args.send_email, print_to_stdout=args.print_report or not sys.argv[1:])
