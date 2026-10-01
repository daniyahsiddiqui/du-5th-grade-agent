# 🤖 DU 5th Grade Weekly Agent & Parent WhatsApp Bot

Automated weekly homework scraper, 1-page printable checklist generator (HTML, Markdown, PDF), email dispatcher, and parent WhatsApp group Q&A bot for DU 5th Grade.

---

## 📋 Features

- 🌐 **Multi-Subject Live Scraper (`scraper.py`)**: Scrapes live Google Sites pages across all subjects (Homeroom, ELA, Math, Science, Social Studies, Qur'an & Arabic, Islamic Studies, Computers) and dynamically follows current week sub-pages.
- 🔲 **Printable 1-Page Digest & PDF (`report_builder.py`)**: Generates an 8.5"x11" printable 1-page HTML report (`latest_report.html`), Markdown digest, and PDF document with checkboxes for student tracking.
- 📧 **Automated Email Dispatcher (`email_sender.py`)**: Sends rich HTML email digests directly to parents every Sunday morning with `latest_report.pdf` attached.
- 💬 **WhatsApp Parent Q&A Bot (`whatsapp_engine.py` & `whatsapp_bridge/index.js`)**: Connects to your parent WhatsApp group (`Test_1`) to answer parent queries instantly (`!due`, `!tests`, `!quran`, `!ixl`, `!spelling`, `!all`, `@bot`).
- ⚡ **GitHub Actions Automated Sunday Runner (`.github/workflows/weekly_agent.yml`)**: 100% free automated Sunday morning scraper & email dispatcher.

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/<your-username>/du-5th-grade-agent.git
cd du-5th-grade-agent
```

### 2. Configure Email & WhatsApp Group Settings
Copy `config.example.json` to `config.json` and fill in your email details:
```json
{
  "sender_email": "your_email@gmail.com",
  "sender_password": "your_16_char_app_password",
  "recipient_email": "parent1@gmail.com, parent2@gmail.com",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "whatsapp_group_name": "Test_1"
}
```

### 3. Run Manually Anytime
```bash
python3 agent.py --run-now
```

### 4. Start WhatsApp Personal Account Bot
```bash
./start_whatsapp_bot.sh
```
Scan the terminal QR code with your WhatsApp phone under **Linked Devices**.

---

## 📅 Supported WhatsApp Bot Commands

| Command | Description |
| :--- | :--- |
| `!due` | Shows assignments and tests due tomorrow |
| `!tests` | Lists upcoming tests and quizzes across all subjects |
| `!quran` | Shows main Hifz assignment, review surahs, and Friday recitation |
| `!ixl` | Lists assigned IXL skill codes and due dates |
| `!spelling` | Displays current weekly spelling list |
| `!all` / `!report` | Delivers complete weekly overview digest |
# du-5th-grade-agent
