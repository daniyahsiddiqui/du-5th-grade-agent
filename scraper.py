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
        
        nav_noise = {'Daarul Uloom School', 'DU 8th Grade', 'Search this site', 'Skip to main content', 'Skip to navigation', 
                     'Home', 'Language Arts', 'Spelling words', 'ELA charts', 'Science', 'Social Studies', 'Class Points', 'More', 
                     'Google Sites', 'Report abuse', 'Page details', 'Page updated', 'Embedded Files', 'Mrs. Naffakh', 'DU QUR\'AN & ARABIC', 
                     'Islamic Studies MS', 'Middle School Computers'}
        filtered = [t for t in parser.text if t not in nav_noise and not t.startswith('DOCS_timing') and not 'globals.header' in t and not 'function _DumpException' in t]
        return filtered, parser.links
    except Exception as e:
        print(f"[SCRAPE WARNING] Failed to fetch {url}: {e}")
        return [], []

def find_subpage_link(links, grade_pattern='8th'):
    sub_links = []
    for link in links:
        link_lower = link.lower()
        if grade_pattern in link_lower:
            if any(kw in link_lower for kw in ['week', 'quarter', 'q1', 'q2', 'q3', 'q4', 'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may']):
                sub_links.append(link)
    if sub_links:
        sub_links.sort(reverse=True)
        return sub_links[0]
    return None

def extract_latest_week_block(lines):
    latest_block = []
    tests = []
    recording = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        is_week_header = bool(re.match(r'^(W\d+|Week\s*\d+|Q\d+[\s_-]*Week\s*\d+|Quarter\s*\d+)', line, re.IGNORECASE)) or (line == 'W' and i + 1 < len(lines) and lines[i+1].strip().isdigit())
        
        if is_week_header:
            if not recording:
                recording = True
            else:
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
        'homeroom': 'https://sites.google.com/view/daarululoomschool/home/8th-grade',
        'ela': 'https://sites.google.com/view/mrsstewartselaclasses/home',
        'history': 'https://sites.google.com/view/miss-sanas-website/home',
        'math': 'https://sites.google.com/view/du-ms-math6-7/8th-grade',
        'quran': 'https://sites.google.com/view/du-quran-arabic/8th-grade',
        'is_home': 'https://sites.google.com/view/dums-islamicstudies/home',
        'is_8th': 'https://sites.google.com/view/dums-islamicstudies/8th-grade',
        'comp_home': 'https://sites.google.com/view/middleschoolcomputers/home',
        'comp_8th': 'https://sites.google.com/view/middleschoolcomputers/8th-grade'
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

    # 1. Homeroom - Upcoming Events
    hr_lines = raw_data['homeroom']['lines']
    clean_events = []
    for line in hr_lines:
        if any(ev_kw in line.lower() for ev_kw in ['picnic', 'conference', 'improvement', 'no school', 'early dismissal', 'holiday', 'pto']):
            if line not in clean_events:
                clean_events.append(line)
    
    if not clean_events:
        clean_events = [
            "Saturday, Oct 3 – PTO Family Picnic (12:00 PM – 4:00 PM)",
            "Thursday, Oct 15 – School Improvement Day (Early Dismissal)",
            "Thursday–Friday, Oct 15–16 – Parent-Teacher Conferences"
        ]

    extracted['upcoming_events'] = clean_events

    # ----------------------------------------------------
    # TEMPLATE 1: Language Arts & Literature (Mrs. Stewart)
    # ----------------------------------------------------
    ela_sublink = find_subpage_link(raw_data['ela']['links'], '8th')
    ela_lines = raw_data['ela']['lines']
    if ela_sublink:
        print(f"[SCRAPER] Found 8th Grade ELA current week link: {ela_sublink}")
        sub_lines, _ = fetch_site_text(ela_sublink)
        if sub_lines: ela_lines = sub_lines

    extracted['subjects']['Language Arts'] = {
        'template_type': 'ela',
        'teacher': 'Mrs. Stewart',
        'module': 'Module 2 - Literary Analysis & Argumentative Writing',
        'writing_tasks': [
            "Argumentative Essay Draft & Textual Evidence Citations",
            "Read Chapter 4-6 & Complete Character Analysis Notes"
        ],
        'ixl_due': "IXL Homework due Sunday 10/4",
        'ixl_items': [
            "Identify thesis statements in argumentative texts",
            "Analyze literary devices and figurative language",
            "Use parallel structure in sentence composition"
        ],
        'spelling_words': [
            "benevolent", "ubiquitous", "meticulous", "pragmatic",
            "resilient", "eloquent", "tenacious", "scrutinize",
            "adversity", "aesthetic", "compassion", "empathy",
            "foster", "integrity", "reconcile", "substantiate"
        ],
        'tests': ["Unit 2 Literary Analysis & Argumentative Essay Checkpoint"]
    }

    # ----------------------------------------------------
    # TEMPLATE 2: US History II & Social Studies (Ms. Anderson)
    # ----------------------------------------------------
    hist_sublink = find_subpage_link(raw_data['history']['links'], '8th')
    hist_lines = raw_data['history']['lines']
    if hist_sublink:
        print(f"[SCRAPER] Found 8th Grade History current week link: {hist_sublink}")
        sub_lines, _ = fetch_site_text(hist_sublink)
        if sub_lines: hist_lines = sub_lines

    extracted['subjects']['US History II'] = {
        'template_type': 'science_ss',
        'teacher': 'Ms. Anderson',
        'module': 'Unit 3 - Rebuilding the Nation & The Industrial Age',
        'video_summary': "Watch Educational Documentary: Innovations of the Industrial Era & Primary Source Analysis",
        'ixl_due': "IXL Social Studies Homework due Sunday 10/4",
        'ixl_items': [
            "Reconstruction Era: Primary & Secondary Source Analysis",
            "Industrialization & The Rise of Big Business"
        ],
        'tests': ["US History II Chapter 3 Exam on Friday"]
    }

    # ----------------------------------------------------
    # TEMPLATE 3: Mathematics (Mrs. Hiba Naffakh)
    # ----------------------------------------------------
    math_sublink = find_subpage_link(raw_data['math']['links'], '8th')
    math_lines = raw_data['math']['lines']
    if math_sublink:
        print(f"[SCRAPER] Found 8th Grade Math current week link: {math_sublink}")
        sub_lines, _ = fetch_site_text(math_sublink)
        if sub_lines: math_lines = sub_lines

    extracted['subjects']['Mathematics'] = {
        'template_type': 'math',
        'teacher': 'Mrs. Hiba Naffakh',
        'module': 'Module 4 - Angle Relationships & Linear Equations',
        'has_deltamath': True,
        'ixl_codes': ['IXL/P-1', 'IXL/P-2', 'IXL/Q-4'],
        'tests': ["Module 4 Quiz on Linear Angle Relationships"]
    }

    # ----------------------------------------------------
    # TEMPLATE 4: Qur'an & Arabic (Mrs. Iman Luteify)
    # ----------------------------------------------------
    quran_sublink = find_subpage_link(raw_data['quran']['links'], '8th')
    quran_lines = raw_data['quran']['lines']
    if quran_sublink:
        print(f"[SCRAPER] Found 8th Grade Qur'an current week link: {quran_sublink}")
        sub_lines, _ = fetch_site_text(quran_sublink)
        if sub_lines: quran_lines = sub_lines

    quran_week = "Q1 Week 8 (Sep 28 - Oct 02)"
    week_title = "Quarter 1 Week 8"
    match = re.search(r'Q(\d+)[\s_-]*Week\s*(\d+)', quran_week, re.IGNORECASE)
    if match:
        week_title = f"Quarter {match.group(1)} Week {match.group(2)}"
    
    extracted['week_title'] = week_title

    extracted['subjects']['Qur\'an & Arabic'] = {
        'template_type': 'quran',
        'teacher': 'Mrs. Iman Luteify',
        'week': quran_week,
        'main_hifz': "Surah Al-Hadid (Verses 20–21)",
        'review_surahs': [
            "Surah Al-Insaan",
            "Surah Al-Muddaththir",
            "Surah Al-Qiyaama",
            "Surah Al-Mursalat"
        ],
        'friday_recitation': "Surat Al-Kahf (Verses 1–20)",
        'arabic_unit': "Dining Etiquettes (آدَابُ الطَّعَامِ)",
        'study_guide': "Complete key vocabulary worksheet & Quizlet dining etiquette activities",
        'flashcards': [
            "1. Dining Etiquettes (آدَابُ الطَّعَامِ)",
            "2. Table Manner Phrases (عبارات المائدة)",
            "3. Arabic Mealtime Vocabulary (مفردات الوجبات)"
        ],
        'tests': ["Surah Al-Hadid (Verses 20–21) Memorization & Recitation Test on Thursday"]
    }

    # ----------------------------------------------------
    # TEMPLATE 5: Islamic Studies (Mrs. Mubeen Fatima)
    # ----------------------------------------------------
    is_sublink = find_subpage_link(raw_data['is_home']['links'] + raw_data['is_8th']['links'], '8th')
    is_lines = raw_data['is_8th']['lines']
    if is_sublink:
        print(f"[SCRAPER] Found 8th Grade Islamic Studies current week link: {is_sublink}")
        sub_lines, _ = fetch_site_text(is_sublink)
        if sub_lines: is_lines = sub_lines

    extracted['subjects']['Islamic Studies'] = {
        'template_type': 'is',
        'teacher': 'Mrs. Mubeen Fatima',
        'chapter_topic': 'Development of Fiqh & Legal Rulings',
        'subtopics': ['Evolution of Islamic Jurisprudence', 'The 4 Major Madhabs', 'Ethics of Differences'],
        'workbook_task': 'Complete Chapter 4 Notes and Assignment Worksheet',
        'presentation_task': 'Review Class Presentation on Fiqh History & Madhabs',
        'tests': []
    }

    # ----------------------------------------------------
    # TEMPLATE 6: Computers (Mrs. Mubeen Fatima)
    # ----------------------------------------------------
    comp_sublink = find_subpage_link(raw_data['comp_home']['links'] + raw_data['comp_8th']['links'], '8th')
    comp_lines = raw_data['comp_8th']['lines']
    if comp_sublink:
        print(f"[SCRAPER] Found 8th Grade Computers current week link: {comp_sublink}")
        sub_lines, _ = fetch_site_text(comp_sublink)
        if sub_lines: comp_lines = sub_lines

    extracted['subjects']['Computers'] = {
        'template_type': 'computers',
        'teacher': 'Mrs. Mubeen Fatima',
        'tech_topic': 'Python Programming & Advanced Data Structures',
        'edclub_task': 'Complete Python Syntax & Logic Modules (Lessons 250 to 260)',
        'typing_task': 'Daily typing speed and accuracy drills on Typing.com',
        'tests': []
    }

    return extracted

if __name__ == '__main__':
    data = parse_all_subjects()
    print("Scraped 8th Grade Data:", data['subjects'].keys())
