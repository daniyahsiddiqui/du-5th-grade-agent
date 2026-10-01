import os
import json
import re
from datetime import datetime, timedelta

DEFAULT_JSON_PATH = os.path.join(os.path.dirname(__file__), 'reports', 'latest_data.json')

def load_latest_data(json_path=None):
    target_path = json_path or DEFAULT_JSON_PATH
    
    # Auto re-scrape if dataset missing or older than 12 hours
    should_rescrape = not os.path.exists(target_path)
    if os.path.exists(target_path):
        mtime = os.path.getmtime(target_path)
        if (datetime.now().timestamp() - mtime) > (12 * 3600):
            should_rescrape = True

    if should_rescrape:
        try:
            print("[WHATSAPP ENGINE] Dataset is stale or missing. Auto-refreshing from Google Sites...")
            from scraper import parse_all_subjects
            scraped_data = parse_all_subjects()
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(scraped_data, f, indent=2, ensure_ascii=False)
            return scraped_data
        except Exception as e:
            print(f"[WHATSAPP ENGINE WARNING] Auto re-scrape failed: {e}")

    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WHATSAPP ENGINE ERROR] Could not read dataset: {e}")
        return None

def format_due_tomorrow(data):
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    tomorrow_day_name = tomorrow.strftime("%A")
    tomorrow_str = tomorrow.strftime("%m/%d")

    res = [f"📅 *DU 5th Grade - What's Due Tomorrow ({tomorrow_day_name}, {tomorrow_str})*:\n"]
    
    subjects = data.get('subjects', {})
    found_any = False

    # Check tests scheduled
    tests_for_tomorrow = []
    for subj_name, subj_data in subjects.items():
        for test in subj_data.get('tests', []):
            if test:
                if tomorrow_day_name.lower() in test.lower() or "tomorrow" in test.lower():
                    tests_for_tomorrow.append(f"🚨 *{subj_name}*: {test}")
    
    if tests_for_tomorrow:
        found_any = True
        res.append("⚠️ *TESTS / QUIZZES TOMORROW*:")
        res.extend(tests_for_tomorrow)
        res.append("")

    # Check IXL due dates
    ixls_due = []
    for subj_name, subj_data in subjects.items():
        due_info = subj_data.get('ixl_due', '')
        items = subj_data.get('ixl_items', []) or subj_data.get('ixl_codes', [])
        if items:
            if tomorrow_day_name.lower() in due_info.lower() or tomorrow_str in due_info:
                ixls_due.append(f"🎯 *{subj_name} IXL*: {len(items)} IXL(s) due ({due_info})")
    
    if ixls_due:
        found_any = True
        res.append("🎯 *IXL HOMEWORK DUE TOMORROW*:")
        res.extend(ixls_due)
        res.append("")

    # Specific Friday Recitation check if tomorrow is Friday
    if tomorrow_day_name.lower() == "friday" and "Qur'an & Arabic" in subjects:
        q_data = subjects["Qur'an & Arabic"]
        found_any = True
        res.append("🕌 *FRIDAY QUR'AN PRACTICE & TEST*:")
        res.append(f"  • Main Hifz: {q_data.get('main_hifz')}")
        res.append(f"  • Friday Recitation: {q_data.get('friday_recitation')}")
        res.append("")

    if not found_any:
        res.append("✅ No immediate specific deadlines or tests explicitly flagged for tomorrow.")
        res.append("📌 Reply with `!due` or `!all` to see full weekly checklist & due dates!")

    return "\n".join(res)

def format_upcoming_tests(data):
    subjects = data.get('subjects', {})
    res = ["🚨 *DU 5th Grade - Upcoming Tests & Quizzes*:\n"]
    has_tests = False
    
    for subj_name, subj_data in subjects.items():
        tests = subj_data.get('tests', [])
        for test in tests:
            if test:
                has_tests = True
                res.append(f"• *{subj_name}*: {test}")
    
    if not has_tests:
        res.append("✅ No upcoming tests or quizzes flagged for this week.")
        
    return "\n".join(res)

def format_ixl_summary(data):
    subjects = data.get('subjects', {})
    res = ["🎯 *DU 5th Grade - Weekly IXL & Math Assignments*:\n"]
    has_ixl = False

    # Language Arts
    ela = subjects.get('Language Arts', {})
    if ela.get('ixl_items'):
        has_ixl = True
        due = f" (Due: {ela.get('ixl_due')})" if ela.get('ixl_due') else ""
        res.append(f"📝 *Language Arts*{due}:")
        for item in ela['ixl_items']:
            res.append(f"  • {item}")
        res.append("")

    # Science / Social Studies
    for s_name in ['Science', 'Social Studies']:
        s_data = subjects.get(s_name, {})
        if s_data.get('ixl_items'):
            has_ixl = True
            due = f" (Due: {s_data.get('ixl_due')})" if s_data.get('ixl_due') else ""
            res.append(f"🔬 *{s_name}*{due}:")
            for item in s_data['ixl_items']:
                res.append(f"  • {item}")
            res.append("")

    # Math
    m_data = subjects.get('Mathematics', {})
    if m_data.get('has_deltamath') or m_data.get('ixl_codes'):
        has_ixl = True
        res.append("📐 *Mathematics*:")
        if m_data.get('has_deltamath'):
            res.append("  • 📐 [DeltaMath] Complete online DeltaMath assignment")
        if m_data.get('ixl_codes'):
            res.append(f"  • 🎯 [IXL Codes]: {', '.join(m_data['ixl_codes'])}")
        res.append("")

    if not has_ixl:
        res.append("✅ No IXL assignments flagged for this week.")

    return "\n".join(res)

def format_quran_summary(data):
    q_data = data.get('subjects', {}).get("Qur'an & Arabic", {})
    if not q_data:
        return "ℹ️ Qur'an & Arabic details not available for this week."

    res = [
        f"📖 *DU 5th Grade - Qur'an & Arabic ({q_data.get('week', 'Current Week')})*:\n",
        f"🎯 *Main Hifz*: {q_data.get('main_hifz')}",
    ]
    
    reviews = q_data.get('review_surahs', [])
    if reviews:
        res.append(f"📖 *Review Surahs*: {', '.join(reviews)}")
        
    res.append(f"🕌 *Friday Practice*: {q_data.get('friday_recitation')}")
    
    tests = q_data.get('tests', [])
    if tests:
        res.append(f"🚨 *Test Alert*: {', '.join(tests)}")

    res.append(f"\n📝 *Arabic Class*: {q_data.get('arabic_unit')}")
    res.append(f"📄 *Study Guide*: {q_data.get('study_guide')}")
    
    flashcards = q_data.get('flashcards', [])
    if flashcards:
        res.append("🎴 *Flashcards*: " + ", ".join(flashcards))

    return "\n".join(res)

def format_spelling_summary(data):
    spelling = data.get('subjects', {}).get('Language Arts', {}).get('spelling_words', [])
    if not spelling:
        return "ℹ️ Spelling word list not available for this week."
    
    res = [f"📖 *DU 5th Grade - Weekly Spelling Words ({len(spelling)} words)*:\n"]
    for i, word in enumerate(spelling, 1):
        res.append(f"{i}. {word}")
    
    return "\n".join(res)

def format_all_summary(data):
    date_str = data.get('scrape_date', datetime.now().strftime('%Y-%m-%d'))
    week_title = data.get('week_title') or "Quarter 1 Week 8"
    res = [f"📋 *DU 5th Grade Weekly Overview — {week_title} ({date_str})*\n"]

    # Quick tests
    res.append(format_upcoming_tests(data))
    res.append("\n" + "="*30 + "\n")
    # Quick IXL
    res.append(format_ixl_summary(data))
    res.append("\n" + "="*30 + "\n")
    # Quran
    res.append(format_quran_summary(data))
    
    return "\n".join(res)

BOT_HEADER = "🤖 *DU 5th Grade WhatsApp Bot*"

def process_whatsapp_query(user_query, json_path=None):
    data = load_latest_data(json_path)
    if not data:
        return f"{BOT_HEADER}\n\n⚠️ Sorry, the latest weekly report dataset is not loaded yet. Please run the weekly scraper."

    clean_q = re.sub(r'@bot:?', '', user_query, flags=re.IGNORECASE).strip()
    q = clean_q.lower()

    if any(k in q for k in ['tomorrow', 'due', 'deadline', 'submit', '!due', '!tomorrow']):
        raw_res = format_due_tomorrow(data)
    elif any(k in q for k in ['test', 'quiz', 'exam', 'assessment', 'testing', '!test', '!tests']):
        raw_res = format_upcoming_tests(data)
    elif any(k in q for k in ['ixl', 'deltamath', 'math hw', 'homework', 'assignment', '!ixl', '!hw']):
        raw_res = format_ixl_summary(data)
    elif any(k in q for k in ['quran', 'qur\'an', 'surah', 'surahs', 'hifz', 'memorize', 'recitation', 'arabic', '!quran', '!arabic']):
        raw_res = format_quran_summary(data)
    elif any(k in q for k in ['spelling', 'vocab', 'vocabulary', 'word', 'words', '!spelling', '!words']):
        raw_res = format_spelling_summary(data)
    elif any(k in q for k in ['event', 'events', 'announcement', 'picnic', 'conference', 'calendar', '!events']):
        events = data.get('upcoming_events', [])
        if not events:
            raw_res = "🗓️ No special upcoming school events flagged for this week."
        else:
            res_lines = ["📢 *Upcoming School Events*:\n"]
            for ev in events:
                res_lines.append(f"• 🗓️ {ev}")
            raw_res = "\n".join(res_lines)
    elif any(k in q for k in ['all', 'overview', 'summary', 'full', 'everything', '!all', '!help', 'help']):
        raw_res = format_all_summary(data)
    else:
        # Keyword matching fallback
        matching_subjects = []
        subjects = data.get('subjects', {})
        for subj_name, subj_data in subjects.items():
            if subj_name.lower() in q or any(word in q for word in subj_name.lower().split()):
                matching_subjects.append(subj_name)
        
        if matching_subjects:
            res_lines = [f"📚 *Details for {', '.join(matching_subjects)}*:\n"]
            for s in matching_subjects:
                sd = subjects[s]
                res_lines.append(f"• *{s}* (Teacher: {sd.get('teacher', 'N/A')})")
                res_lines.append(f"  Topic/Module: {sd.get('module') or sd.get('chapter_topic') or sd.get('tech_topic') or sd.get('arabic_unit')}")
                if sd.get('tests'):
                    res_lines.append(f"  🚨 Tests: {', '.join(sd['tests'])}")
                if sd.get('ixl_items'):
                    res_lines.append(f"  🎯 IXLs: {', '.join(sd['ixl_items'])}")
                if sd.get('ixl_codes'):
                    res_lines.append(f"  🎯 IXLs: {', '.join(sd['ixl_codes'])}")
            raw_res = "\n".join(res_lines)
        else:
            # General help response
            raw_res = (
                "Ask me anything about weekly homework! Commands:\n"
                "• `@bot !due` or `@bot What is due tomorrow?`\n"
                "• `@bot !tests` or `@bot What tests are coming up?`\n"
                "• `@bot !ixl` or `@bot What IXLs are assigned?`\n"
                "• `@bot !quran` or `@bot What surahs are for review?`\n"
                "• `@bot !spelling` or `@bot Spelling list`\n"
                "• `@bot !all` for full summary."
            )

    return f"{BOT_HEADER}\n\n{raw_res}"

if __name__ == '__main__':
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "!help"
    print(process_whatsapp_query(query))
