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

def clean_lines(lines):
    noise_patterns = [
        r'^window\.WIZ',
        r'^\(function',
        r'^\.rrJNTc',
        r'^@media',
        r'^\s*$',
        r'^[5678]TH GRADE',
        r'^Grade [5678]',
        r'^Search this site',
        r'^Skip to',
        r'^Home page',
        r'^Welcome Page'
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
    sub_links = []
    for link in links:
        link_lower = link.lower()
        if grade_pattern in link_lower or 'eighth' in link_lower:
            if any(kw in link_lower for kw in ['week', 'quarter', 'q1', 'q2', 'q3', 'q4', 'sep', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may']):
                sub_links.append(link)
    if sub_links:
        # Sort so that latest week URLs come first
        sub_links.sort(reverse=True)
        return sub_links[0]
    return None

def parse_all_subjects():
    base_sites = {
        'homeroom': 'https://sites.google.com/view/daarululoomschool/home/8th-grade',
        'ela': 'https://sites.google.com/view/mrsstewartselaclasses/home',
        'ela_8th': 'https://sites.google.com/view/mrsstewartselaclasses/8th-grade-english',
        'history': 'https://sites.google.com/view/miss-sanas-website/home',
        'math': 'https://sites.google.com/view/du-ms-math6-7/8th-grade',
        'quran': 'https://sites.google.com/view/du-quran-arabic/8th-grade',
        'is': 'https://sites.google.com/view/dums-islamicstudies/8th-grade',
        'comp': 'https://sites.google.com/view/middleschoolcomputers/8th-grade'
    }

    raw_data = {}
    for key, url in base_sites.items():
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

    # 1. Homeroom - Announcements & Events
    hr_sublink = find_subpage_link(raw_data['homeroom']['links'], '8th')
    hr_lines = raw_data['homeroom']['lines']
    if hr_sublink:
        print(f"[SCRAPER] Found 8th Grade Homeroom current week link: {hr_sublink}")
        sub_lines, _ = fetch_site_text(hr_sublink)
        if sub_lines:
            hr_lines += sub_lines

    hr_lines_clean = clean_lines(hr_lines)
    clean_events = []
    for i, line in enumerate(hr_lines_clean):
        if any(ev_kw in line.lower() for ev_kw in ['picnic', 'conference', 'improvement', 'no school', 'early dismissal', 'holiday', 'pto', 'event']):
            event_text = line
            # Check if next line contains date/time detail
            if i + 1 < len(hr_lines_clean) and len(hr_lines_clean[i+1]) < 80:
                if any(dt in hr_lines_clean[i+1].lower() for dt in ['am', 'pm', '2026', '2025', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may', '[']):
                    event_text += " " + hr_lines_clean[i+1]
            if event_text not in clean_events:
                clean_events.append(event_text)

    if not clean_events:
        clean_events = ["No explicit upcoming school events posted for this week."]

    extracted['upcoming_events'] = clean_events

    # ----------------------------------------------------
    # 2. Language Arts (Mrs. Stewart / Ms. Carman)
    # ----------------------------------------------------
    ela_links = raw_data['ela']['links'] + raw_data['ela_8th']['links']
    ela_sublink = find_subpage_link(ela_links, '8th')
    ela_lines = raw_data['ela_8th']['lines'] or raw_data['ela']['lines']
    if ela_sublink:
        print(f"[SCRAPER] Found 8th Grade ELA current week link: {ela_sublink}")
        sub_lines, _ = fetch_site_text(ela_sublink)
        if sub_lines:
            ela_lines = sub_lines

    ela_clean = clean_lines(ela_lines)
    ela_tasks = []
    ela_tests = []
    ela_module = "Active Quarter 1 / Week 8 Reading & Writing Unit"

    for i, line in enumerate(ela_clean):
        if 'Monster Calls' in line or 'Reading' in line or 'Writing' in line or 'IXL' in line or 'Vocabulary' in line:
            if line not in ela_tasks and len(line) < 200:
                ela_tasks.append(line)
        if any(t_kw in line.lower() for t_kw in ['quiz', 'test', 'checkpoint', 'exam']):
            if line not in ela_tests and len(line) < 150:
                ela_tests.append(line)

    if not ela_tasks:
        ela_tasks = ela_clean[:10] if ela_clean else ["No explicit Language Arts assignments posted for this week."]

    extracted['subjects']['Language Arts'] = {
        'teacher': 'Mrs. Stewart / Ms. Carman',
        'module': ela_module,
        'lines': ela_clean,
        'tasks': ela_tasks,
        'tests': ela_tests
    }

    # ----------------------------------------------------
    # 3. US History II (Ms. Anderson)
    # ----------------------------------------------------
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

    for line in hist_clean:
        if any(m_kw in line.lower() for m_kw in ['module', 'unit', 'chapter']) and len(line) < 80:
            hist_module = line
        if any(t_kw in line.lower() for t_kw in ['test', 'quiz', 'exam']) and len(line) < 150:
            if line not in hist_tests:
                hist_tests.append(line)
        elif any(hw_kw in line.lower() for hw_kw in ['review', 'hw', 'due', 'project', 'presentation', 'study guide', 'peer']) and len(line) < 150:
            if line not in hist_tasks:
                hist_tasks.append(line)

    if not hist_tasks:
        hist_tasks = hist_clean[:8] if hist_clean else ["No explicit History assignments posted for this week."]

    extracted['subjects']['US History II'] = {
        'teacher': 'Ms. Anderson',
        'module': hist_module,
        'lines': hist_clean,
        'tasks': hist_tasks,
        'tests': hist_tests
    }

    # ----------------------------------------------------
    # 4. Mathematics (Mrs. Hiba Naffakh)
    # ----------------------------------------------------
    math_sublink = find_subpage_link(raw_data['math']['links'], '8th')
    math_lines = raw_data['math']['lines']
    if math_sublink:
        print(f"[SCRAPER] Found 8th Grade Math current week link: {math_sublink}")
        sub_lines, _ = fetch_site_text(math_sublink)
        if sub_lines:
            math_lines = sub_lines

    math_clean = clean_lines(math_lines)
    math_tasks = []
    math_tests = []
    math_module = "Mathematics"

    for line in math_clean:
        if 'Module' in line or 'Unit' in line or 'Angle' in line:
            math_module = line
        if 'IXL' in line or 'DeltaMath' in line or 'Worksheet' in line or 'Homework' in line:
            if line not in math_tasks:
                math_tasks.append(line)
        if any(t_kw in line.lower() for t_kw in ['quiz', 'test', 'checkpoint', 'exam']) and len(line) < 150:
            if line not in math_tests:
                math_tests.append(line)

    if not math_tasks:
        math_tasks = math_clean if math_clean else ["No explicit Math assignments posted for this week."]

    extracted['subjects']['Mathematics'] = {
        'teacher': 'Mrs. Hiba Naffakh',
        'module': math_module,
        'lines': math_clean,
        'tasks': math_tasks,
        'tests': math_tests
    }

    # ----------------------------------------------------
    # 5. Qur'an & Arabic (Mrs. Iman Luteify)
    # ----------------------------------------------------
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
    week_title = "Quarter 1 Week 8"

    for i, line in enumerate(quran_clean):
        if 'Week' in line or 'Q1' in line or 'Q2' in line:
            week_title = line
        if any(q_kw in line.lower() for q_kw in ['surah', 'hifz', 'ay', 'tilawat', 'arabic', 'آداب', 'quizlet', 'wordwall', 'food etiquettes', 'homework']):
            if line not in quran_tasks and len(line) < 200:
                quran_tasks.append(line)
        if any(t_kw in line.lower() for t_kw in ['test', 'quiz', 'exam', 'memorization test']):
            if line not in quran_tests and len(line) < 150:
                quran_tests.append(line)

    if not quran_tasks:
        quran_tasks = quran_clean[:10] if quran_clean else ["No explicit Qur'an & Arabic assignments posted for this week."]

    extracted['week_title'] = week_title
    extracted['subjects']["Qur'an & Arabic"] = {
        'teacher': 'Mrs. Iman Luteify',
        'week': week_title,
        'lines': quran_clean,
        'tasks': quran_tasks,
        'tests': quran_tests
    }

    # ----------------------------------------------------
    # 6. Islamic Studies (Mrs. Mubeen Fatima)
    # ----------------------------------------------------
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
    is_module = "Islamic Studies"

    for line in is_clean:
        if 'Tawheed' in line or 'Topic' in line or 'Asma' in line or 'AWS' in line:
            is_module = line
        if any(k in line.lower() for k in ['project', 'poster', 'names of allah', 'objective', 'notes', 'classwork', 'homework', 'due']) and len(line) < 200:
            if line not in is_tasks:
                is_tasks.append(line)
        if any(t_kw in line.lower() for t_kw in ['test', 'quiz', 'exam']) and len(line) < 150:
            if line not in is_tests:
                is_tests.append(line)

    if not is_tasks:
        is_tasks = is_clean[:8] if is_clean else ["No explicit Islamic Studies assignments posted for this week."]

    extracted['subjects']['Islamic Studies'] = {
        'teacher': 'Mrs. Mubeen Fatima',
        'module': is_module,
        'lines': is_clean,
        'tasks': is_tasks,
        'tests': is_tests
    }

    # ----------------------------------------------------
    # 7. Computers (Mrs. Mubeen Fatima)
    # ----------------------------------------------------
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
        if 'Learn By Doing' in line or 'Sheets' in line or 'Python' in line:
            comp_module = line
        if any(c_kw in line.lower() for c_kw in ['test', 'skill', 'lesson', 'resource', 'fast finisher', 'typing', 'nitro type']) and len(line) < 180:
            if any(t_kw in line.lower() for t_kw in ['test', 'quiz', 'exam']):
                if line not in comp_tests:
                    comp_tests.append(line)
            elif line not in comp_tasks:
                comp_tasks.append(line)

    if not comp_tasks:
        comp_tasks = comp_clean[:6] if comp_clean else ["No explicit Computers assignments posted for this week."]

    extracted['subjects']['Computers'] = {
        'teacher': 'Mrs. Mubeen Fatima',
        'module': comp_module,
        'lines': comp_clean,
        'tasks': comp_tasks,
        'tests': comp_tests
    }

    return extracted

if __name__ == '__main__':
    data = parse_all_subjects()
    print("Scraped 8th Grade Subjects:", list(data['subjects'].keys()))
    for s_name, s_data in data['subjects'].items():
        print(f"\n--- {s_name} ({s_data['teacher']}) ---")
        print("Tasks:", s_data['tasks'][:5])
        print("Tests:", s_data['tests'])
