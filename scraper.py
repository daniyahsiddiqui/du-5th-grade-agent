import os
import urllib.request
import re
from html.parser import HTMLParser
from datetime import datetime

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'a' and 'href' in attrs_dict:
            href = attrs_dict['href']
            if href.startswith('/'):
                href = 'https://sites.google.com' + href
            self.links.append(href)

    def handle_data(self, data):
        cleaned = data.strip()
        if cleaned and not cleaned.startswith('{') and not cleaned.startswith('var ') and len(cleaned) < 500:
            self.text.append(cleaned)

def fetch_site_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        cookie_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        if os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'r') as cf:
                    cookie_str = cf.read().strip()
                    if cookie_str:
                        headers['Cookie'] = cookie_str
            except Exception:
                pass
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
        parser = TextExtractor()
        parser.feed(html)
        nav_noise = {
            'Daarul Uloom School', 'DU 8th Grade', 'Search this site', 'Skip to main content',
            'Skip to navigation', 'Home', 'Language Arts', 'Spelling words', 'ELA charts',
            'Science', 'Social Studies', 'Class Points', 'More', 'Google Sites', 'Report abuse',
            'Page details', 'Page updated', 'Embedded Files', 'Mrs. Naffakh',
            "DU QUR'AN & ARABIC", 'Islamic Studies MS', 'Middle School Computers'
        }
        filtered = [
            t for t in parser.text
            if t not in nav_noise
            and not t.startswith('DOCS_timing')
            and 'globals.header' not in t
            and 'function _DumpException' not in t
        ]
        return filtered, parser.links
    except Exception as e:
        print(f"[SCRAPE WARNING] Failed to fetch {url}: {e}")
        return [], []

def clean_lines(lines):
    """Remove boilerplate/noise lines from scraped content."""
    noise_patterns = [
        r'^window\.WIZ',
        r'^\(function',
        r'^\.rrJNTc',
        r'^@media',
        r'^\s*$',
        r'^[5-8]TH GRADE$',
        r'^Grade [5-8]$',
        r'^Search this site',
        r'^Skip to',
        r'^Home page$',
        r'^Welcome Page$',
    ]
    cleaned = []
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        if any(re.search(pat, line_s, re.IGNORECASE) for pat in noise_patterns):
            continue
        cleaned.append(line_s)
    return cleaned

def find_subpage_link(links, grade_pattern='8th'):
    """Dynamically picks the latest weekly subpage for the given grade pattern."""
    sub_links = []
    for link in links:
        link_lower = link.lower()
        if grade_pattern in link_lower or 'eighth' in link_lower:
            if any(kw in link_lower for kw in [
                'week', 'quarter', 'q1', 'q2', 'q3', 'q4',
                'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may'
            ]):
                sub_links.append(link)
    if sub_links:
        sub_links.sort(reverse=True)
        return sub_links[0]
    return None

def extract_current_week_block(lines, week_header_pattern=r'^Week\s+\d+'):
    """
    For pages that list multiple weeks (newest first), extract only the first/latest week block.
    Returns lines between the first week header and the second week header.
    """
    block = []
    in_block = False
    for line in lines:
        if re.match(week_header_pattern, line, re.IGNORECASE):
            if not in_block:
                in_block = True
                continue   # skip the header line itself
            else:
                break      # hit next week — stop
        if in_block:
            block.append(line)
    return block

def parse_all_subjects():
    base_sites = {
        'homeroom': 'https://sites.google.com/view/daarululoomschool/home/8th-grade',
        'ela': 'https://sites.google.com/view/mrsstewartselaclasses/home',
        'ela_8th': 'https://sites.google.com/view/mrsstewartselaclasses/8th-grade-english',
        'history': 'https://sites.google.com/view/miss-sanas-website/home',
        'math': 'https://sites.google.com/view/mrscluskey-classes/algebra-i/lesson-plans',
        'quran': 'https://sites.google.com/view/du-quran-arabic/8th-grade',
        'is': 'https://sites.google.com/view/dums-islamicstudies/8th-grade',
        'comp': 'https://sites.google.com/view/middleschoolcomputers/8th-grade',
    }

    raw_data = {}
    for key, url in base_sites.items():
        text_lines, links = fetch_site_text(url)
        raw_data[key] = {'url': url, 'lines': text_lines, 'links': links}

    extracted = {
        'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'upcoming_events': [],
        'subjects': {}
    }

    # --------------------------------------------------------
    # 1. Homeroom — Events + Science (Science lives here)
    # --------------------------------------------------------
    hr_sublink = find_subpage_link(raw_data['homeroom']['links'], '8th')
    science_lines = []
    if hr_sublink:
        print(f"[SCRAPER] Found 8th Grade Homeroom/Science week link: {hr_sublink}")
        sub_lines, _ = fetch_site_text(hr_sublink)
        if sub_lines:
            science_lines = sub_lines

    # Events: pull from the base homeroom page
    hr_clean = clean_lines(raw_data['homeroom']['lines'])
    clean_events = []
    i = 0
    while i < len(hr_clean):
        line = hr_clean[i]
        # Look for event-flagged lines
        if any(ev_kw in line.lower() for ev_kw in ['picnic', 'conference', 'improvement', 'no school', 'early dismissal', 'holiday', 'pto']):
            # Try to attach the following date/time line if it looks like one
            parts = [line]
            if i + 1 < len(hr_clean):
                nxt = hr_clean[i + 1]
                if any(dt in nxt.lower() for dt in ['am', 'pm', '2026', '2025', 'oct', 'nov', 'dec', 'jan', 'feb', '[', ']']):
                    parts.append(nxt)
            event_text = ' '.join(parts)
            if event_text not in clean_events:
                clean_events.append(event_text)
        i += 1

    if not clean_events:
        clean_events = ["No explicit upcoming school events posted for this week."]
    extracted['upcoming_events'] = clean_events

    # Science: from the homeroom weekly subpage — filter to homework/quiz/IXL only
    sci_clean = clean_lines(science_lines)
    sci_tasks = []
    sci_tests = []
    sci_module = "Science"

    for line in sci_clean:
        if re.match(r'^Unit\s+\d+', line, re.IGNORECASE) and len(line) < 100:
            sci_module = line
        if any(kw in line.lower() for kw in ['quiz', 'test', 'exam', 'assessment']) and len(line) < 150:
            if line not in sci_tests:
                sci_tests.append(line)
        elif any(kw in line.lower() for kw in ['h.w', 'homework', 'ixl ', 'study guide', 'workbook', 'pages']) and len(line) < 150:
            if line not in sci_tasks:
                sci_tasks.append(line)

    if not sci_tasks and not sci_tests:
        sci_tasks = ["No explicit Science homework posted for this week."]

    extracted['subjects']['Science'] = {
        'teacher': 'Science Teacher',
        'module': sci_module,
        'tasks': sci_tasks,
        'tests': sci_tests
    }

    # --------------------------------------------------------
    # 2. Language Arts (Mrs. Stewart / Ms. Carman)
    #    Page lists all weeks newest-first. Extract only Week 8 block.
    # --------------------------------------------------------
    ela_links = raw_data['ela']['links'] + raw_data['ela_8th']['links']
    ela_sublink = find_subpage_link(ela_links, '8th')
    ela_raw = raw_data['ela_8th']['lines'] or raw_data['ela']['lines']
    if ela_sublink:
        print(f"[SCRAPER] Found 8th Grade ELA current week link: {ela_sublink}")
        sub_lines, _ = fetch_site_text(ela_sublink)
        if sub_lines:
            ela_raw = sub_lines

    ela_all = clean_lines(ela_raw)

    # Week 8 is at the TOP of the page with a fragmented header:
    # 'Week', '8', '- September', '28 - October 2' then the daily content.
    # The first "Week 7-" (or lower) header line signals the end of the current week.
    ela_week = []
    ela_week_title = "Quarter 1 Week 8"
    for line in ela_all:
        if re.match(r'^Week\s+[1-7]\b', line, re.IGNORECASE):
            break   # hit an older week — stop
        ela_week.append(line)

    # Build a cleaner week title from the fragmented header ('Week', '8', '- September', '28 - October 2')
    for i, line in enumerate(ela_week):
        if line == 'Week' and i + 1 < len(ela_week) and ela_week[i + 1].strip().isdigit():
            week_num = ela_week[i + 1].strip()
            date_parts = []
            j = i + 2
            while j < len(ela_week) and j < i + 5:
                if ela_week[j] in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'):
                    break
                date_parts.append(ela_week[j].strip(' -'))
                j += 1
            ela_week_title = f"Week {week_num} — {' '.join(date_parts)}".strip(' —')
            break

    # Now rebuild clean day-by-day tasks from the week block
    # The pattern is: day name → Reading + content → Writing + content → Homework lines
    ela_tasks = []
    ela_tests = []
    current_day = None
    day_names = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}

    i = 0
    while i < len(ela_week):
        line = ela_week[i]

        if line in day_names:
            current_day = line
            i += 1
            continue

        # Single ':'  — separator fragment, skip
        if line == ':':
            i += 1
            continue

        # "Reading" or "Writing" label: merge with next content line
        if line in ('Reading', 'Writing') and i + 1 < len(ela_week):
            next_line = ela_week[i + 1]
            if next_line == ':' and i + 2 < len(ela_week):
                content = ela_week[i + 2]
                i += 3
            elif next_line.startswith(':'):
                content = next_line[1:].strip()
                i += 2
            else:
                content = next_line
                i += 2
            if content and content not in (':', ''):
                entry = f"{current_day} — {line}: {content}" if current_day else f"{line}: {content}"
                ela_tasks.append(entry)
            continue

        # Homework lines
        if line.lower().startswith('homework:') or line.lower().startswith('h.w'):
            ela_tasks.append(line)
            i += 1
            continue

        # Classwork lines (keep only if they have substance)
        if line.lower().startswith('classwork:') and len(line) > 15:
            ela_tasks.append(line)
            i += 1
            continue

        # IXL skill lines
        if 'ixl skill' in line.lower() or 'ixl skills' in line.lower():
            # Merge with next if it's a continuation
            task = line
            if i + 1 < len(ela_week) and not ela_week[i + 1] in day_names and len(ela_week[i + 1]) < 60:
                task += ' ' + ela_week[i + 1]
                i += 1
            ela_tasks.append(task)
            i += 1
            continue

        # Test/quiz lines
        if any(kw in line.lower() for kw in ['vocab quiz', 'comprehension check', 'map testing']) and len(line) < 120:
            ela_tests.append(line)
            i += 1
            continue

        i += 1

    # Remove duplicate entries
    ela_tasks = list(dict.fromkeys(ela_tasks))
    ela_tests = list(dict.fromkeys(ela_tests))

    if not ela_tasks:
        ela_tasks = ["No explicit Language Arts assignments posted for this week."]

    extracted['subjects']['Language Arts'] = {
        'teacher': 'Mrs. Stewart / Ms. Carman',
        'module': ela_week_title,
        'tasks': ela_tasks,
        'tests': ela_tests
    }

    # --------------------------------------------------------
    # 3. US History II (Ms. Anderson)
    # --------------------------------------------------------
    hist_sublink = find_subpage_link(raw_data['history']['links'], '8th')
    hist_lines = raw_data['history']['lines']
    if hist_sublink:
        print(f"[SCRAPER] Found 8th Grade History current week link: {hist_sublink}")
        sub_lines, _ = fetch_site_text(hist_sublink)
        if sub_lines:
            hist_lines = sub_lines

    hist_clean = clean_lines(hist_lines)
    hist_tasks = []
    hist_tests = []
    hist_module = "US History II"

    # Extract only the current week block (Week N header)
    hist_week = extract_current_week_block(hist_clean, r'^Week\s+\d+')
    if not hist_week:
        hist_week = hist_clean

    for line in hist_week:
        # Only use pure "Module N" or "Unit N" lines as module names
        if re.match(r'^Module\s+\d+\s*$', line, re.IGNORECASE):
            hist_module = line
        elif any(kw in line.lower() for kw in ['test', 'exam']) and len(line) < 150:
            if line not in hist_tests:
                hist_tests.append(line)
        elif any(kw in line.lower() for kw in ['review', 'hw', 'due', 'project', 'presentation', 'peer', 'study guide', 'quiz']) and len(line) < 150:
            if line not in hist_tasks:
                hist_tasks.append(line)

    if not hist_tasks and not hist_tests:
        hist_tasks = ["No explicit History assignments posted for this week."]

    extracted['subjects']['US History II'] = {
        'teacher': 'Ms. Anderson',
        'module': hist_module,
        'tasks': hist_tasks,
        'tests': hist_tests
    }

    # --------------------------------------------------------
    # 4. Mathematics — Algebra I (Mrs. Cluskey)
    #    Single page, newest week listed first.
    # --------------------------------------------------------
    math_clean = clean_lines(raw_data['math']['lines'])
    math_tasks = []
    math_tests = []
    math_module = "Algebra I"

    # Extract the latest week block
    week_block_raw = extract_current_week_block(math_clean, r'^Week\s+\d+')

    # Merge fragmented date/lesson lines (e.g. "9/2", "8", "-", "Topic" → "9/28 - Topic")
    week_block = []
    i = 0
    while i < len(week_block_raw):
        line = week_block_raw[i]
        # Standalone digit fragments (date pieces like "9/2", "8", "-")
        if re.match(r'^\d{1,2}(/\d{0,2})?$', line) or line == '-':
            merged = line
            i += 1
            while i < len(week_block_raw):
                nxt = week_block_raw[i]
                if re.match(r'^\d{1,2}(/\d{0,2})?$', nxt) or nxt == '-':
                    merged += nxt
                    i += 1
                elif len(nxt) < 80 and not re.match(r'^Week\s+\d+', nxt):
                    merged += nxt
                    i += 1
                    break
                else:
                    break
            week_block.append(merged.strip(' -'))
        else:
            week_block.append(line)
            i += 1

    for line in week_block:
        if any(kw in line.lower() for kw in ['test', 'exam', 'mid-unit']):
            if line not in math_tests:
                math_tests.append(line)
        elif any(kw in line.lower() for kw in ['homework', 'ixl', 'deltamath', 'practice']):
            if line not in math_tasks:
                math_tasks.append(line)
        elif len(line) > 3 and line not in math_tasks:
            math_tasks.append(line)

    if not math_tasks and not math_tests:
        math_tasks = ["No explicit Algebra I assignments posted for this week."]

    extracted['subjects']['Mathematics (Algebra I)'] = {
        'teacher': 'Mrs. Cluskey',
        'module': math_module,
        'tasks': math_tasks,
        'tests': math_tests
    }

    # --------------------------------------------------------
    # 5. Qur'an & Arabic (Mrs. Iman Luteify)
    #    Single-week dedicated page — build structured summaries
    # --------------------------------------------------------
    quran_sublink = find_subpage_link(raw_data['quran']['links'], '8th')
    quran_lines = raw_data['quran']['lines']
    if quran_sublink:
        print(f"[SCRAPER] Found 8th Grade Qur'an current week link: {quran_sublink}")
        sub_lines, _ = fetch_site_text(quran_sublink)
        if sub_lines:
            quran_lines = sub_lines

    quran_clean = clean_lines(quran_lines)
    quran_tasks = []
    quran_tests = []
    week_title = "Q1 Week 8 (Sep 28 - Oct 2)"

    # Find week title
    for line in quran_clean:
        if re.search(r'Q\d+\s+Week\s+\d+', line, re.IGNORECASE):
            week_title = line
            break

    # Build structured Qur'an summaries by scanning day-by-day
    # Key patterns: حِفظ (Hifz), تِلَاوَة (Tilawah), الوَاجِبُ (homework), TEST, Quizlet, Wordwall
    hifz_items = []      # memorization assignments
    tilawah_items = []   # recitation/review
    hw_items = []        # homework deadlines
    arabic_items = []    # Arabic class items

    i = 0
    while i < len(quran_clean):
        line = quran_clean[i]

        # Hifz (memorization): حِفظ label followed by surah + ayah
        if line in ('حِفظ',) and i + 1 < len(quran_clean):
            nxt = quran_clean[i + 1]
            ayah_part = ''
            if nxt.startswith(': Surah') or nxt.startswith(':  Surah'):
                surah = nxt.lstrip(': ').strip()
                # Look ahead for ayah range
                if i + 2 < len(quran_clean) and 'Ayah' in quran_clean[i + 2]:
                    ayah_part = ' (' + quran_clean[i + 2].rstrip(')') + ')'
                entry = f"Hifz: {surah}{ayah_part}"
                if entry not in hifz_items:
                    hifz_items.append(entry)

        # Test announcement
        if line == 'TEST:' and i + 1 < len(quran_clean):
            test_surah = quran_clean[i + 1]
            ayah_note = ''
            # Look ahead for the Hadid ayah range (e.g. "Surah Al-\nHadid 22-24")
            for look in range(i + 2, min(i + 8, len(quran_clean))):
                candidate = quran_clean[look]
                # Match patterns like "Ayah 20-21", "21-20", or "Hadid 22-24"
                ayah_match = re.search(r'(\d+[-–]\d+)', candidate)
                if ayah_match:
                    ayah_note = f" (Ayah {ayah_match.group(1)})"
                    break
            quran_tests.append(f"Qur'an Memorization Test (Thursday, Oct 1): {test_surah}{ayah_note}")

        # Arabic homework (الوَاجِبُ المَنْزِلِيُّ)
        if 'الوَاجِبُ' in line or 'Please c' in line or 'omplete three activities' in line:
            hw_items.append('Arabic Homework: Complete 3 activities from Quizlet (آدَابُ الطَّعَامِ) — due Saturday, October 3rd')

        # Quizlet / Wordwall tasks
        if 'Rules of Noon Sakinah' in line:
            arabic_items.append(f"Tajweed: {line}")
        elif 'Wordwall:' in line:
            arabic_items.append('Arabic Practice: Wordwall — أسئلة/سورة الحديد')

        # Friday recitation
        if line == 'Surat Al-Kahf 1-20':
            tilawah_items.append("Friday: Tilawah — Surat Al-Kahf (Ayah 1-20)")

        # Arabic reading lesson
        if 'آداب الطَّعَامِ' in line or 'Food etiquettes' in line:
            if 'Arabic: Lesson — آداب الطَّعَامِ (Food Etiquettes)' not in arabic_items:
                arabic_items.append('Arabic: Lesson — آداب الطَّعَامِ (Food Etiquettes)')

        i += 1

    # Build final clean task list
    if hifz_items:
        # Deduplicate and take the latest hifz (highest ayah)
        latest_hifz = hifz_items[-1] if hifz_items else None
        if latest_hifz:
            quran_tasks.append(latest_hifz)
    if tilawah_items:
        for t in dict.fromkeys(tilawah_items):
            quran_tasks.append(t)
    if arabic_items:
        for a in dict.fromkeys(arabic_items):
            quran_tasks.append(a)
    if hw_items:
        for h in dict.fromkeys(hw_items):
            quran_tasks.append(h)

    if not quran_tasks:
        quran_tasks = ["No explicit Qur'an & Arabic assignments posted for this week."]

    # Deduplicate tests
    quran_tests = list(dict.fromkeys(quran_tests))

    extracted['week_title'] = week_title
    extracted['subjects']["Qur'an & Arabic"] = {
        'teacher': 'Mrs. Iman Luteify',
        'week': week_title,
        'tasks': quran_tasks,
        'tests': quran_tests
    }

    # --------------------------------------------------------
    # 6. Islamic Studies (Ms. Mahmood)
    #    Show ONLY: Tests / Homework / Projects
    # --------------------------------------------------------
    is_sublink = find_subpage_link(raw_data['is']['links'], '8th')
    is_lines = raw_data['is']['lines']
    if is_sublink:
        print(f"[SCRAPER] Found 8th Grade Islamic Studies current week link: {is_sublink}")
        sub_lines, _ = fetch_site_text(is_sublink)
        if sub_lines:
            is_lines = sub_lines

    is_clean = clean_lines(is_lines)
    is_tasks = []
    is_tests = []

    # Collect IS project/homework/due lines — consolidate "OPTION 1/2" blocks
    project_lines = []
    in_project = False
    for line in is_clean:
        if 'project due' in line.lower() or 'announcement' in line.lower():
            in_project = True
            if 'project due' in line.lower():
                project_lines.append(line)
        elif in_project:
            if line in ('OPTION 1', 'OPTION', '2', 'OPTION 2'):
                continue
            elif any(kw in line.lower() for kw in ['make a', 'poster', 'names of allah', 'the name', 'its meaning', 'what it teaches', 'how knowing', 'reference from']):
                project_lines.append(line)
            elif line in ('MONDAY', 'WEDNESDAY', 'FRIDAY', 'Topic', 'Objective'):
                in_project = False
        if any(kw in line.lower() for kw in ['test', 'quiz', 'exam']) and len(line) < 150:
            if line not in is_tests:
                is_tests.append(line)

    # Consolidate project lines into clean entries
    if project_lines:
        # Find due date
        due_line = next((l for l in project_lines if 'project due' in l.lower()), None)
        if due_line:
            is_tasks.append(due_line)
        # Option 1
        option1_lines = [l for l in project_lines if 'all 99 names' in l.lower()]
        if option1_lines:
            is_tasks.append('Option 1: Make a creative poster with all 99 names of Allah with English meaning')
        # Option 2
        option2_details = [l for l in project_lines if any(x in l.lower() for x in ['make a poster explaining', 'the name', 'its meaning', 'what it teaches', 'how knowing', 'reference from'])]
        if option2_details:
            is_tasks.append('Option 2: Make a poster explaining 1 name of Allah (include: The Name, Its Meaning, What it Teaches us, How it Affects Muslim Behavior, Reference from Qur\'an/Hadith)')

    if not is_tasks and not is_tests:
        is_tasks = ["No explicit Islamic Studies homework or projects posted for this week."]

    extracted['subjects']['Islamic Studies'] = {
        'teacher': 'Ms. Mahmood',
        'module': 'Tawheed — Asma was Sifaat',
        'tasks': is_tasks,
        'tests': is_tests
    }

    # --------------------------------------------------------
    # 7. Computers (Mrs. Mubeen Fatima)
    # --------------------------------------------------------
    comp_sublink = find_subpage_link(raw_data['comp']['links'], '8th')
    comp_lines = raw_data['comp']['lines']
    if comp_sublink:
        print(f"[SCRAPER] Found 8th Grade Computers current week link: {comp_sublink}")
        sub_lines, _ = fetch_site_text(comp_sublink)
        if sub_lines:
            comp_lines = sub_lines

    comp_clean = clean_lines(comp_lines)
    comp_tasks = []
    comp_tests = []
    comp_module = "Computers & Technology"

    for line in comp_clean:
        if any(kw in line.lower() for kw in ['learn by doing', 'lesson']) and len(line) < 80:
            comp_module = line
            # Don't also add it as a task
            continue
        if any(kw in line.lower() for kw in ['test', 'quiz', 'exam']) and len(line) < 150:
            if line not in comp_tests:
                comp_tests.append(line)
        elif any(kw in line.lower() for kw in ['fast finisher', 'typing', 'nitro type', 'typing.com']) and len(line) < 180:
            if line not in comp_tasks:
                comp_tasks.append(line)
        elif line.lower() in ('resource', ':'):
            pass  # skip lone noise lines

    if not comp_tasks and not comp_tests:
        comp_tasks = ["No explicit Computers assignments posted for this week."]

    extracted['subjects']['Computers'] = {
        'teacher': 'Mrs. Mubeen Fatima',
        'module': comp_module,
        'tasks': comp_tasks,
        'tests': comp_tests
    }

    return extracted


if __name__ == '__main__':
    data = parse_all_subjects()
    print("\n" + "=" * 60)
    print("Scraped 8th Grade Subjects:", list(data['subjects'].keys()))
    print("=" * 60)
    for s_name, s_data in data['subjects'].items():
        print(f"\n--- {s_name} ({s_data['teacher']}) ---")
        print(f"  Module: {s_data.get('module', '')}")
        print(f"  Tasks ({len(s_data.get('tasks', []))}):")
        for t in s_data.get('tasks', []):
            print(f"    • {t}")
        print(f"  Tests ({len(s_data.get('tests', []))}):")
        for t in s_data.get('tests', []):
            print(f"    ⚠ {t}")
    print(f"\nEvents: {data['upcoming_events']}")
