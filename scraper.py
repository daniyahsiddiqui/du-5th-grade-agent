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
            'DU QUR\'AN & ARABIC', 'Islamic Studies MS', 'Middle School Computers'
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

def find_latest_link(links, path_fragment):
    """Find the latest subpage under a site that contains path_fragment."""
    matches = [l for l in links if path_fragment in l.lower()]
    if matches:
        matches.sort(reverse=True)
        return matches[0]
    return None

def parse_all_subjects():
    base_sites = {
        'homeroom': 'https://sites.google.com/view/daarululoomschool/home/8th-grade',
        'ela': 'https://sites.google.com/view/mrsstewartselaclasses/home',
        'ela_8th': 'https://sites.google.com/view/mrsstewartselaclasses/8th-grade-english',
        'history': 'https://sites.google.com/view/miss-sanas-website/home',
        # Math: Mrs. Cluskey's Algebra I lesson plans (single page, all weeks listed)
        'math': 'https://sites.google.com/view/mrscluskey-classes/algebra-i/lesson-plans',
        'quran': 'https://sites.google.com/view/du-quran-arabic/8th-grade',
        'is': 'https://sites.google.com/view/dums-islamicstudies/8th-grade',
        'comp': 'https://sites.google.com/view/middleschoolcomputers/8th-grade',
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

    # --------------------------------------------------------
    # 1. Homeroom — Events + Science (Science lives here)
    # --------------------------------------------------------
    hr_sublink = find_subpage_link(raw_data['homeroom']['links'], '8th')
    hr_lines = raw_data['homeroom']['lines']
    science_lines = []
    if hr_sublink:
        print(f"[SCRAPER] Found 8th Grade Homeroom/Science week link: {hr_sublink}")
        sub_lines, _ = fetch_site_text(hr_sublink)
        if sub_lines:
            science_lines = sub_lines
            hr_lines = hr_lines + sub_lines

    # Events from homeroom base page
    hr_clean = clean_lines(raw_data['homeroom']['lines'])
    clean_events = []
    for i, line in enumerate(hr_clean):
        if any(ev_kw in line.lower() for ev_kw in [
            'picnic', 'conference', 'improvement', 'no school',
            'early dismissal', 'holiday', 'pto', 'event'
        ]):
            event_text = line
            if i + 1 < len(hr_clean) and len(hr_clean[i + 1]) < 80:
                next_l = hr_clean[i + 1].lower()
                if any(dt in next_l for dt in ['am', 'pm', '2026', '2025', 'oct', 'nov', 'dec', 'jan', 'feb', 'mar', '[', 'pm']):
                    event_text += ' ' + hr_clean[i + 1]
            if event_text not in clean_events:
                clean_events.append(event_text)

    if not clean_events:
        clean_events = ["No explicit upcoming school events posted for this week."]
    extracted['upcoming_events'] = clean_events

    # Science from homeroom weekly subpage
    sci_clean = clean_lines(science_lines)
    sci_tasks = []
    sci_tests = []
    sci_module = "Science"

    for line in sci_clean:
        if re.match(r'^Unit', line, re.IGNORECASE) and len(line) < 100:
            sci_module = line
        # Only collect test/quiz/hw/IXL lines — skip nav/week headers
        if any(kw in line.lower() for kw in ['quiz', 'test', 'exam']) and len(line) < 150:
            if line not in sci_tests:
                sci_tests.append(line)
        elif any(kw in line.lower() for kw in ['h.w', 'homework', 'ixl', 'study guide', 'workbook']) and len(line) < 150:
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
    # --------------------------------------------------------
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
    ela_module = "Quarter 1 Reading & Writing Unit"

    for line in ela_clean:
        if any(kw in line for kw in ['Monster Calls', 'Reading', 'Writing', 'IXL', 'Vocabulary', 'Homework', 'Classwork', 'Narrative', 'HMH']):
            if line not in ela_tasks and len(line) < 200:
                ela_tasks.append(line)
        if any(kw in line.lower() for kw in ['quiz', 'test', 'checkpoint', 'exam', 'map testing']):
            if line not in ela_tests and len(line) < 150:
                ela_tests.append(line)

    if not ela_tasks:
        ela_tasks = ela_clean[:10] if ela_clean else ["No explicit Language Arts assignments posted for this week."]

    extracted['subjects']['Language Arts'] = {
        'teacher': 'Mrs. Stewart / Ms. Carman',
        'module': ela_module,
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

    for line in hist_clean:
        if re.match(r'^Module\s+\d+', line, re.IGNORECASE) and len(line) < 80:
            hist_module = line
        if any(kw in line.lower() for kw in ['test', 'quiz', 'exam']) and len(line) < 150:
            if line not in hist_tests:
                hist_tests.append(line)
        elif any(kw in line.lower() for kw in ['review', 'hw', 'due', 'project', 'presentation', 'peer', 'study guide']) and len(line) < 150:
            if line not in hist_tasks:
                hist_tasks.append(line)

    if not hist_tasks:
        hist_tasks = hist_clean[:8] if hist_clean else ["No explicit History assignments posted for this week."]

    extracted['subjects']['US History II'] = {
        'teacher': 'Ms. Anderson',
        'module': hist_module,
        'tasks': hist_tasks,
        'tests': hist_tests
    }

    # --------------------------------------------------------
    # 4. Mathematics — Algebra I (Mrs. Cluskey)
    #    Single page with all weeks listed; parse Week 8 block
    # --------------------------------------------------------
    math_clean = clean_lines(raw_data['math']['lines'])
    math_tasks = []
    math_tests = []
    math_module = "Algebra I"

    # Find the latest "Week N" block and merge fragmented date/lesson lines
    recording = False
    week_block_raw = []
    for line in math_clean:
        if re.match(r'^Week\s+\d+', line, re.IGNORECASE):
            if not recording:
                recording = True   # start capturing the first (latest) week block
                continue
            else:
                break              # hit the next older week — stop
        if recording:
            week_block_raw.append(line)

    # Join fragmented lines: date parts (e.g. "9/2", "8", "-", "Topic") merge into one line
    week_block = []
    i = 0
    while i < len(week_block_raw):
        line = week_block_raw[i]
        # A date fragment: starts with digits/slash or is a standalone digit or "-"
        if re.match(r'^\d{1,2}(/\d{0,2})?$', line) or line == '-':
            # Accumulate until we hit a real content line
            merged = line
            i += 1
            while i < len(week_block_raw):
                next_l = week_block_raw[i]
                if re.match(r'^\d{1,2}(/\d{0,2})?$', next_l) or next_l == '-':
                    merged += next_l
                    i += 1
                elif len(next_l) < 60 and not re.match(r'^Week\s+\d+', next_l):
                    merged += next_l
                    i += 1
                    break
                else:
                    break
            week_block.append(merged.strip(' -'))
        else:
            week_block.append(line)
            i += 1

    for line in week_block:
        if any(kw in line.lower() for kw in ['test', 'quiz', 'exam', 'mid-unit']):
            if line not in math_tests:
                math_tests.append(line)
        elif any(kw in line.lower() for kw in ['homework', 'ixl', 'deltamath', 'practice', 'worksheet']):
            if line not in math_tasks:
                math_tasks.append(line)
        elif len(line) > 3 and line not in math_tasks:
            math_tasks.append(line)

    if not math_tasks:
        math_tasks = ["No explicit Algebra I assignments posted for this week."]

    extracted['subjects']['Mathematics (Algebra I)'] = {
        'teacher': 'Mrs. Cluskey',
        'module': math_module,
        'tasks': math_tasks,
        'tests': math_tests
    }

    # --------------------------------------------------------
    # 5. Qur'an & Arabic (Mrs. Iman Luteify)
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
    week_title = "Quarter 1 Week 8"

    for line in quran_clean:
        if re.match(r'^(Q\d+|Quarter\s+\d+)\s+Week', line, re.IGNORECASE):
            week_title = line
        if any(kw in line.lower() for kw in [
            'surah', 'hifz', 'ayah', 'tilawat', 'arabic', 'آداب', 'quizlet',
            'wordwall', 'food etiquette', 'homework', 'الواجب'
        ]):
            if line not in quran_tasks and len(line) < 200:
                quran_tasks.append(line)
        if any(kw in line.lower() for kw in ['test', 'quiz', 'exam', 'memorization test', 'اختبار']):
            if line not in quran_tests and len(line) < 200:
                quran_tests.append(line)

    if not quran_tasks:
        quran_tasks = quran_clean[:10] if quran_clean else ["No explicit Qur'an & Arabic assignments posted for this week."]

    extracted['week_title'] = week_title
    extracted['subjects']["Qur'an & Arabic"] = {
        'teacher': 'Mrs. Iman Luteify',
        'week': week_title,
        'tasks': quran_tasks,
        'tests': quran_tests
    }

    # --------------------------------------------------------
    # 6. Islamic Studies (Ms. Mahmood)
    #    Only show: Tests / Homework / Projects — skip daily objectives
    # --------------------------------------------------------
    is_sublink = find_subpage_link(raw_data['is']['links'], '8th')
    is_lines = raw_data['is']['lines']
    if is_sublink:
        print(f"[SCRAPER] Found 8th Grade Islamic Studies current week link: {is_sublink}")
        sub_lines, _ = fetch_site_text(is_sublink)
        if sub_lines:
            is_lines = sub_lines

    is_clean = clean_lines(is_lines)
    is_tasks = []   # homework / projects only
    is_tests = []

    for line in is_clean:
        if any(kw in line.lower() for kw in ['test', 'quiz', 'exam']) and len(line) < 150:
            if line not in is_tests:
                is_tests.append(line)
        elif any(kw in line.lower() for kw in [
            'project', 'poster', 'homework', 'h.w', 'due', 'submit', 'assignment',
            'option', 'make a', 'names of allah', 'الواجب'
        ]) and len(line) < 200:
            if line not in is_tasks:
                is_tasks.append(line)

    if not is_tasks and not is_tests:
        is_tasks = ["No explicit Islamic Studies homework or projects posted for this week."]

    extracted['subjects']['Islamic Studies'] = {
        'teacher': 'Ms. Mahmood',
        'module': 'Tawheed & Asma was Sifaat',
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
        if any(kw in line.lower() for kw in ['learn by doing', 'sheets', 'lesson']) and len(line) < 80:
            comp_module = line
        if any(kw in line.lower() for kw in ['test', 'quiz', 'exam']) and len(line) < 150:
            if line not in comp_tests:
                comp_tests.append(line)
        elif any(kw in line.lower() for kw in ['resource', 'fast finisher', 'typing', 'nitro type', 'typing.com', 'skill']) and len(line) < 180:
            if line not in comp_tasks:
                comp_tasks.append(line)

    if not comp_tasks:
        comp_tasks = comp_clean[:6] if comp_clean else ["No explicit Computers assignments posted for this week."]

    extracted['subjects']['Computers'] = {
        'teacher': 'Mrs. Mubeen Fatima',
        'module': comp_module,
        'tasks': comp_tasks,
        'tests': comp_tests
    }

    return extracted


if __name__ == '__main__':
    data = parse_all_subjects()
    print("Scraped 8th Grade Subjects:", list(data['subjects'].keys()))
    for s_name, s_data in data['subjects'].items():
        print(f"\n--- {s_name} ({s_data['teacher']}) ---")
        print("  Module:", s_data.get('module', ''))
        print("  Tasks:", s_data.get('tasks', [])[:5])
        print("  Tests:", s_data.get('tests', []))
