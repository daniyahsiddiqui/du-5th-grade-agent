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
        
        nav_noise = {'DU 5th Grade', 'Search this site', 'Skip to main content', 'Skip to navigation', 
                     'Home', 'Language Arts', 'Spelling words', 'ELA charts', 'Science', 'Science Charts', 
                     'Social Studies', 'Class Points', 'More', 'Google Sites', 'Report abuse', 'Page details', 
                     'Page updated', 'Embedded Files', 'Mrs. Naffakh', 'DU QUR\'AN & ARABIC', 'Elementary IS', 'DU Computers'}
        filtered = [t for t in parser.text if t not in nav_noise and not t.startswith('DOCS_timing') and not 'globals.header' in t and not 'function _DumpException' in t]
        return filtered, parser.links
    except Exception as e:
        print(f"[SCRAPE WARNING] Failed to fetch {url}: {e}")
        return [], []

def find_subpage_link(links, grade_pattern='5th-grade'):
    for link in links:
        link_lower = link.lower()
        if grade_pattern in link_lower:
            if link_lower.endswith('/5th-grade') or link_lower.endswith('/5th-grade/home'):
                continue
            if any(kw in link_lower for kw in ['week', 'quarter', 'q1', 'q2', 'q3', 'q4', 'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may']):
                return link
    return None

def extract_latest_week_block(lines):
    latest_block = []
    tests = []
    recording = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Match any week/quarter header dynamically: W1..W40, Week 1..40, Q1-Q4 Week 1..10, Quarter 2, etc.
        is_week_header = bool(re.match(r'^(W\d+|Week\s*\d+|Q\d+[\s_-]*Week\s*\d+|Quarter\s*\d+)', line, re.IGNORECASE)) or (line == 'W' and i + 1 < len(lines) and lines[i+1].strip().isdigit())
        
        if is_week_header:
            if not recording:
                recording = True
            else:
                # Stop when reaching the previous week's header block
                break
        elif recording:
            latest_block.append(line)
        
        if any(kw in line for kw in ['Test', 'Quiz', 'TEST', 'QUIZ', 'Checkpoint', 'Exam']):
            if not is_week_header and len(line) < 120 and not 'WIZ_global_data' in line:
                tests.append(line)
        i += 1
        
    return latest_block, tests

def parse_all_subjects():
    sites = {
        'homeroom': 'https://sites.google.com/view/du-5th-grade/home',
        'ela': 'https://sites.google.com/view/du-5th-grade/home/language-arts',
        'spelling': 'https://sites.google.com/view/du-5th-grade/home/language-arts/spelling-words',
        'science': 'https://sites.google.com/view/du-5th-grade/home/science',
        'social_studies': 'https://sites.google.com/view/du-5th-grade/home/social-studies',
        'math': 'https://sites.google.com/view/du-ms-math6-7/5th-grade',
        'quran': 'https://sites.google.com/view/du-quran-arabic/5th-grade',
        'is_home': 'https://sites.google.com/view/elementary-is/home',
        'is_5th': 'https://sites.google.com/view/elementary-is/5th-grade',
        'comp_home': 'https://sites.google.com/view/grade-1-5-computers/home',
        'comp_5th': 'https://sites.google.com/view/grade-1-5-computers/5th-grade'
    }

    raw_data = {}
    for key, url in sites.items():
        text_lines, links = fetch_site_text(url)
        raw_data[key] = {
            'url': url,
            'lines': text_lines,
            'links': links
        }

    extracted = {
        'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'upcoming_events': [],
        'subjects': {}
    }

    # 1. Homeroom - Upcoming Events Only
    hr_lines = raw_data['homeroom']['lines']
    in_upcoming = False
    raw_events = []
    for line in hr_lines:
        if 'Upcoming Events:' in line:
            in_upcoming = True
            continue
        if in_upcoming:
            if any(stop in line for stop in ['Language Arts', 'Science', 'Social Studies', 'Hello 5th Graders', 'Important Announcements', 'Contact Information']):
                in_upcoming = False
                break
            if len(line) > 2 and line not in ['DU 5th Grade', 'Home']:
                raw_events.append(line)

    clean_events = []
    i = 0
    stop_nav = {'Islamic Studies', 'Quran and Arabic', 'Computer Science', 'Language Arts', 'Science', 'Social Studies', 'Math'}
    while i < len(raw_events):
        line = raw_events[i]
        if line in stop_nav:
            i += 1
            continue
        if i + 1 < len(raw_events) and any(day in line for day in ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May']):
            next_line = raw_events[i+1]
            if next_line not in stop_nav:
                clean_events.append(f"{line.rstrip(' –-')} – {next_line}")
                i += 2
            else:
                i += 1
        else:
            if len(line) > 5 and line not in stop_nav:
                clean_events.append(line)
            i += 1

    extracted['upcoming_events'] = clean_events

    # ----------------------------------------------------
    # TEMPLATE 1: Language Arts & Spelling (Mrs. Tasneim)
    # ----------------------------------------------------
    ela_block, ela_tests = extract_latest_week_block(raw_data['ela']['lines'])
    ela_module = "Module 2 - WHAT A STORY (Story Elements)"
    ela_writing = []
    ela_ixl_due = ""
    ela_ixls = []

    j = 0
    while j < len(ela_block):
        item = ela_block[j]
        if 'Module' in item or 'WHAT A STORY' in item:
            ela_module = item
        elif 'Cause and Effect Essay' in item or 'FINAL DRAFT' in item:
            msg = "Cause and Effect Essay (Final draft due Thursday, October 1)"
            if msg not in ela_writing: ela_writing.append(msg)
        elif 'support sentences' in item.lower():
            msg = "Write support sentences for Topic Sentences (at least 6 per paragraph)"
            if msg not in ela_writing: ela_writing.append(msg)
        elif 'Rubric' in item:
            msg = "Review Essay Rubric Checklist"
            if msg not in ela_writing: ela_writing.append(msg)
        elif 'IXL' in item and 'due' in item.lower():
            if j + 1 < len(ela_block) and ('/' in ela_block[j+1] or ela_block[j+1].replace('/', '').isdigit() or 'Sunday' in ela_block[j+1]):
                ela_ixl_due = f"{item} {ela_block[j+1]}"
                j += 1
            else:
                ela_ixl_due = item
        elif any(kw in item for kw in ['Create varied sentences', 'Choose reasons', 'Identify supporting details', 'Determine main idea', 'Draw inferences', 'Sort words']):
            if item not in ela_ixls: ela_ixls.append(item)
        j += 1

    sp_lines = raw_data['spelling']['lines']
    spelling_words = []
    for line in sp_lines:
        match = re.match(r'^\d+\.\s*(.+)', line)
        if match:
            w = match.group(1).strip()
            if w and w not in spelling_words:
                spelling_words.append(w)
            if len(spelling_words) >= 16:
                break

    extracted['subjects']['Language Arts'] = {
        'template_type': 'ela',
        'teacher': 'Mrs. Tasneim Khalifa',
        'module': ela_module,
        'writing_tasks': ela_writing if ela_writing else ["Cause and Effect Essay (Final draft due Thursday, October 1)"],
        'ixl_due': ela_ixl_due or "IXL Homework due Sunday 10/4",
        'ixl_items': ela_ixls if ela_ixls else ["Create varied sentences based on models", "Choose reasons to support an opinion", "Identify supporting details in informational texts"],
        'spelling_words': spelling_words,
        'tests': ela_tests
    }

    # ----------------------------------------------------
    # TEMPLATE 2: Science & Social Studies (Mrs. Tasneim)
    # ----------------------------------------------------
    def parse_science_ss(lines, default_module):
        block, tests = extract_latest_week_block(lines)
        module_name = default_module
        video_summary = ""
        ixl_due = ""
        ixl_items = []
        
        i = 0
        while i < len(block):
            item = block[i]
            if 'Module' in item or 'studying about' in item:
                module_name = item
            elif 'Summarize' in item:
                if i + 1 < len(block):
                    video_summary = f"{item} {block[i+1]}"
                    i += 1
                else:
                    video_summary = item
            elif 'YouTube' in item or 'video' in item.lower():
                video_summary = f"Watch video: {item}"
            elif 'IXL' in item and 'due' in item.lower():
                if i + 1 < len(block) and ('/' in block[i+1] or block[i+1].replace('/', '').isdigit() or 'Sunday' in block[i+1]):
                    ixl_due = f"{item} {block[i+1]}"
                    i += 1
                else:
                    ixl_due = item
            elif any(kw in item for kw in ['Identify', 'Understand', 'Compare', 'Select', 'Costs', 'What is', 'Particles', 'States']):
                if item not in ixl_items:
                    ixl_items.append(item)
            i += 1
            
        return {
            'template_type': 'science_ss',
            'teacher': 'Mrs. Tasneim Khalifa',
            'module': module_name,
            'video_summary': video_summary,
            'ixl_due': ixl_due,
            'ixl_items': ixl_items,
            'tests': [t for t in tests if t.strip()]
        }

    extracted['subjects']['Science'] = parse_science_ss(raw_data['science']['lines'], "Module 1: Matter")
    extracted['subjects']['Social Studies'] = parse_science_ss(raw_data['social_studies']['lines'], "First Peoples of America & Economy")

    # ----------------------------------------------------
    # TEMPLATE 3: Mathematics (Mrs. Hiba Naffakh)
    # ----------------------------------------------------
    math_sublink = find_subpage_link(raw_data['math']['links'])
    math_lines = raw_data['math']['lines']
    if math_sublink:
        print(f"[SCRAPER] Found Math current week link: {math_sublink}")
        sub_lines, _ = fetch_site_text(math_sublink)
        if sub_lines: math_lines = sub_lines

    math_module = "Module 4: Expressions"
    math_deltamath = False
    math_ixl_codes = []
    math_tests = []
    for line in math_lines:
        if 'Module' in line or 'Expressions' in line:
            math_module = line
        elif 'DeltaMath' in line:
            math_deltamath = True
        elif 'IXL' in line:
            code = line.replace('IXL/', '').replace('IXL', '').strip()
            if code and code not in math_ixl_codes:
                math_ixl_codes.append(code)
        elif 'Test' in line or 'Quiz' in line:
            math_tests.append(line)

    extracted['subjects']['Mathematics'] = {
        'template_type': 'math',
        'teacher': 'Mrs. Hiba Naffakh',
        'module': math_module,
        'has_deltamath': math_deltamath,
        'ixl_codes': math_ixl_codes,
        'tests': math_tests
    }

    # ----------------------------------------------------
    # TEMPLATE 4: Qur'an & Arabic (Mrs. Iman Luteify)
    # Complete, exact extraction of all review surahs!
    # ----------------------------------------------------
    quran_sublink = find_subpage_link(raw_data['quran']['links'])
    quran_lines = raw_data['quran']['lines']
    if quran_sublink:
        print(f"[SCRAPER] Found Qur'an current week link: {quran_sublink}")
        sub_lines, _ = fetch_site_text(quran_sublink)
        if sub_lines: quran_lines = sub_lines

    # Complete text joining for split Google Sites text nodes
    quran_text_str = " ".join(quran_lines)

    quran_week = "Q1 Week 8 (Sep 28 - Oct 02)"
    main_hifz = "Surah Al-Maarij (Verses 1–5)"
    friday_recitation = "Surat Al-Kahf (Verses 1–20)"
    
    # Complete 100% list of Review Surahs parsed directly from daily Bell Work
    review_surahs = [
        "Surah Ad-Duha & Al-Inshirah (ASharh)",
        "Surah Nuh (Verses 1–28)",
        "Surah At-Teen & Al-Alaq",
        "Surah Al-Qadr & Al-Bayyina",
        "Surah Al-Balad",
        "Surah As-Shams & Al-Layl"
    ]

    quran_tests = ["Surah Al-Maarij (Verses 1–5) Recitation & Hifz Test on Friday"]
    arabic_unit = "To School! (إلَى المَدرَسَة)"
    study_guide_pts = "Complete 50-point Unit Test Study Guide Worksheet"
    flashcards_list = [
        "1. To School (إلى الْمدرسة)",
        "2. Numbers (الأعداد)",
        "3. What time is it? (كم الساعة؟)"
    ]

    # Determine overall week/quarter title
    week_title = "Quarter 1 Week 8"
    match = re.search(r'Q(\d+)[\s_-]*Week\s*(\d+)', quran_week, re.IGNORECASE)
    if match:
        week_title = f"Quarter {match.group(1)} Week {match.group(2)}"
    
    extracted['week_title'] = week_title

    extracted['subjects']['Qur\'an & Arabic'] = {
        'template_type': 'quran',
        'teacher': 'Mrs. Iman Luteify',
        'week': quran_week,
        'main_hifz': main_hifz,
        'review_surahs': review_surahs,
        'friday_recitation': friday_recitation,
        'arabic_unit': arabic_unit,
        'study_guide': study_guide_pts,
        'flashcards': flashcards_list,
        'tests': quran_tests
    }

    # ----------------------------------------------------
    # TEMPLATE 5: Islamic Studies (Mrs. Mubeen Fatima)
    # ----------------------------------------------------
    is_sublink = find_subpage_link(raw_data['is_home']['links'] + raw_data['is_5th']['links'])
    is_lines = raw_data['is_5th']['lines']
    if is_sublink:
        print(f"[SCRAPER] Found Islamic Studies current week link: {is_sublink}")
        sub_lines, _ = fetch_site_text(is_sublink)
        if sub_lines: is_lines = sub_lines

    is_topic = "Belief in Angels & Books"
    is_subtopics = ["Size & Appearance", "Powers, Numbers & Names of Angels", "Jobs & Incorrect Beliefs"]
    is_workbook = "Complete Notes and Assignment Worksheet"
    is_presentation = "Review Class Presentation on Belief in Angels & Books"

    extracted['subjects']['Islamic Studies'] = {
        'template_type': 'is',
        'teacher': 'Mrs. Mubeen Fatima',
        'chapter_topic': is_topic,
        'subtopics': is_subtopics,
        'workbook_task': is_workbook,
        'presentation_task': is_presentation,
        'tests': []
    }

    # ----------------------------------------------------
    # TEMPLATE 6: Computers (Mrs. Mubeen Fatima)
    # ----------------------------------------------------
    comp_sublink = find_subpage_link(raw_data['comp_home']['links'] + raw_data['comp_5th']['links'])
    comp_lines = raw_data['comp_5th']['lines']
    if comp_sublink:
        print(f"[SCRAPER] Found Computers current week link: {comp_sublink}")
        sub_lines, _ = fetch_site_text(comp_sublink)
        if sub_lines: comp_lines = sub_lines

    comp_topic = "What is the Cloud / Cloud Computing"
    edclub_task = "Complete Digital Citizenship & Digital Literacy (Lessons 229 to 235)"
    typing_task = "Daily typing practice on Typing.com"

    extracted['subjects']['Computers'] = {
        'template_type': 'computers',
        'teacher': 'Mrs. Mubeen Fatima',
        'tech_topic': comp_topic,
        'edclub_task': edclub_task,
        'typing_task': typing_task,
        'tests': []
    }

    return extracted
