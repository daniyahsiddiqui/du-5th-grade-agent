import os
import urllib.request
import re
from html.parser import HTMLParser
from datetime import datetime, date, timedelta


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
        filtered = [t for t in parser.text
                    if t not in nav_noise
                    and not t.startswith('DOCS_timing')
                    and 'globals.header' not in t
                    and 'function _DumpException' not in t
                    and not t.startswith('window.WIZ')
                    and not t.startswith('(function')
                    and not t.startswith('.rrJNTc')
                    and not t.startswith('@media')]
        return filtered, parser.links
    except Exception as e:
        print(f"[SCRAPE WARNING] Failed to fetch {url}: {e}")
        return [], []


# ============================================================
# DATE-AWARE CURRENT WEEK DETECTION
# ============================================================
MONTH_WORDS = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}


def get_reference_date(today=None):
    """The date the report is 'for'. On weekends (the agent runs Sunday) look ahead to the upcoming Monday."""
    today = today or date.today()
    if today.weekday() >= 5:  # Saturday / Sunday
        today = today + timedelta(days=7 - today.weekday())
    return today


def _school_year_for_month(month, ref):
    school_start_year = ref.year if ref.month >= 7 else ref.year - 1
    return school_start_year if month >= 7 else school_start_year + 1


def parse_week_range(text, ref=None):
    """
    Extract a (start_date, end_date) range from week labels / URL slugs such as:
      'W9 OCTOBER 5 - OCTOBER 9', 'q1-week-9-oct-05-09', 'oct-5th-9th',
      'week-of-10052026', 'Week of 10/05/2026', 'Week of Sept. 28- Oct. 2'
    Returns None if no date could be found.
    """
    ref = ref or get_reference_date()
    t = text.lower()
    dates = []

    # Numeric dates: 10/05/2026, 10-05-26
    for m in re.finditer(r'(?<!\d)(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})(?!\d)', t):
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = y + 2000 if y < 100 else y
        try:
            dates.append(date(y, mo, d))
        except ValueError:
            pass
    # Compact mmddyyyy (e.g. week-of-10052026)
    for m in re.finditer(r'(?<!\d)(\d{2})(\d{2})(20\d{2})(?!\d)', t):
        try:
            dates.append(date(int(m.group(3)), int(m.group(1)), int(m.group(2))))
        except ValueError:
            pass

    if not dates:
        # Month-name based: a month word followed by one or more day numbers
        cur_month = None
        for tok in re.findall(r'[a-z]+|\d+', t):
            if tok in MONTH_WORDS:
                cur_month = MONTH_WORDS[tok]
            elif tok.isdigit() and cur_month:
                day = int(tok)
                if 1 <= day <= 31:
                    try:
                        dates.append(date(_school_year_for_month(cur_month, ref), cur_month, day))
                    except ValueError:
                        pass
            elif tok in ('st', 'nd', 'rd', 'th', 'of', 'to'):
                continue

    if not dates:
        return None
    start, end = min(dates), max(dates)
    if start == end:
        end = start + timedelta(days=6)
    return (start, end)


def pick_current(candidates, ref=None):
    """
    candidates: list of (label_text, payload). Picks the candidate whose date range contains the
    reference date; otherwise the most recent week that started on/before it; otherwise the first.
    """
    ref = ref or get_reference_date()
    dated = []
    for label, payload in candidates:
        rng = parse_week_range(label, ref)
        if rng:
            dated.append((rng, label, payload))

    for (start, end), label, payload in dated:
        if start <= ref <= end:
            return payload, label
    past = [d for d in dated if d[0][0] <= ref]
    if past:
        best = max(past, key=lambda d: d[0][0])
        return best[2], best[1]
    if candidates:
        return candidates[0][1], candidates[0][0]
    return None, None


def find_subpage_link(links, grade_pattern='5th-grade'):
    """Pick the weekly sub-page link that matches the current date."""
    candidates = []
    seen = set()
    for link in links:
        link_lower = link.lower().split('?')[0]
        if grade_pattern not in link_lower or link_lower in seen:
            continue
        if link_lower.endswith('/' + grade_pattern) or link_lower.endswith('/' + grade_pattern + '/home'):
            continue
        slug = link_lower.split(grade_pattern, 1)[1]  # only the part after the grade folder
        if parse_week_range(slug):
            seen.add(link_lower)
            candidates.append((slug, link))
    link, _ = pick_current(candidates)
    return link


WEEK_HEADER_RE = re.compile(r'^(W\d+\b|Week\s*\d+|Q\d+[\s_-]*Week\s*\d+)', re.IGNORECASE)


def split_week_blocks(lines):
    """
    Split a page that lists many weeks (W9 ..., W8 ..., W7 ...) into blocks.
    Handles headers that Google Sites splits across lines, e.g. 'W', '9', 'OCTOBER 5', '-', 'OCTOBER 9', ':'.
    Returns list of (header_text, block_lines).
    """
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        is_split_header = line == 'W' and i + 1 < len(lines) and lines[i + 1].strip().isdigit()
        if WEEK_HEADER_RE.match(line) or is_split_header:
            header_parts = [line]
            j = i + 1
            # Absorb continuation fragments of the header (dates, dashes, colon)
            while j < len(lines) and j < i + 7 and not header_parts[-1].endswith(':'):
                nxt = lines[j].strip()
                if len(nxt) > 30 or WEEK_HEADER_RE.match(nxt):
                    break
                header_parts.append(nxt)
                j += 1
            blocks.append([' '.join(header_parts), []])
            i = j
            continue
        if blocks:
            blocks[-1][1].append(line)
        i += 1
    return [(h, b) for h, b in blocks]


def extract_current_week_block(lines):
    """Return (header, block_lines) for the week that matches today's date."""
    blocks = split_week_blocks(lines)
    if not blocks:
        return '', []
    block, header = pick_current([(h, (h, b)) for h, b in blocks])
    return block if block else blocks[0]


TEST_RE = re.compile(r'\b(test|quiz|checkpoint|exam)\b', re.IGNORECASE)


def find_tests(lines):
    return [l for l in lines if TEST_RE.search(l) and len(l) < 160]


def ayah_range_after(lines, idx, lookahead=5):
    """Ayah ranges are split like '(', '5', '-1)' or '(10-1)'. Join and normalise to '1–10'."""
    chunk = ''.join(lines[idx:idx + lookahead])
    m = re.search(r'\(?\s*(\d+)\s*-\s*(\d+)\s*\)?', chunk)
    if m:
        a, b = sorted([int(m.group(1)), int(m.group(2))])
        return f"{a}–{b}"
    return ''


# ============================================================
# MAIN SCRAPER
# ============================================================
def parse_all_subjects():
    ref = get_reference_date()
    print(f"[SCRAPER] Reference date for 'current week': {ref.isoformat()}")

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
        raw_data[key] = {'url': url, 'lines': text_lines, 'links': links}

    extracted = {
        'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'reference_date': ref.isoformat(),
        'upcoming_events': [],
        'subjects': {}
    }

    # ----------------------------------------------------
    # 1. Homeroom - Upcoming Events Only
    # ----------------------------------------------------
    hr_lines = raw_data['homeroom']['lines']
    in_upcoming = False
    raw_events = []
    for line in hr_lines:
        if 'Upcoming Events:' in line:
            in_upcoming = True
            continue
        if in_upcoming:
            if any(stop in line for stop in ['Language Arts', 'Science', 'Social Studies', 'Hello 5th Graders', 'Important Announcements', 'Contact Information']):
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
            next_line = raw_events[i + 1]
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
    ela_header, ela_block = extract_current_week_block(raw_data['ela']['lines'])
    print(f"[SCRAPER] ELA current week block: {ela_header}")
    ela_module_parts = []
    ela_focus = []
    ela_writing = []
    ela_ixl_due = ""
    ela_ixls = []
    after_ixl = False

    for j, item in enumerate(ela_block):
        low = item.lower()
        if 'ixl' in low and 'due' in low:
            ela_ixl_due = item
            after_ixl = True
            continue
        if after_ixl:
            if len(item) < 90 and 'due' not in low and '.pdf' not in low:
                ela_ixls.append(item)
            continue
        if 'module' in low:
            ela_module_parts.append(item)
        elif item.startswith('(') and ela_module_parts and len(ela_module_parts) == 1:
            ela_module_parts.append(item)
        elif any(kw in low for kw in ['due', 'draft', 'homework', 'project', 'assignment']):
            if item not in ela_writing:
                ela_writing.append(item)
        elif 'this week we will' in low:
            continue
        elif len(item) < 60 and not item.endswith('?') and not TEST_RE.search(item) and len(ela_focus) < 4 \
                and not low.startswith(('prompts', 'each paragraph', 'to write', 'what ', 'how ', 'where ', 'who ', 'when ', 'give ', 'identify the', 'at least', 'supporting')):
            ela_focus.append(item)

    ela_module = ' '.join(ela_module_parts) if ela_module_parts else "Language Arts"
    if ela_focus:
        ela_module += " — " + ", ".join(ela_focus)

    # Spelling: newest week's list is at the top of the page
    sp_lines = raw_data['spelling']['lines']
    spelling_words = []
    spelling_title = ""
    spelling_week_num = None
    started = False
    for line in sp_lines:
        m_sp = re.match(r'^Week\s*(\d+)\s*Spelling', line, re.IGNORECASE)
        if m_sp:
            if started:
                break
            started = True
            spelling_title = line
            spelling_week_num = int(m_sp.group(1))
            continue
        if started:
            if line.strip().lower() in ('review', 'challenge'):
                break
            match = re.match(r'^\d+\.\s*(.+)', line)
            if match:
                w = match.group(1).strip()
                if w and w not in spelling_words:
                    spelling_words.append(w)

    # Check if the spelling list is current with the active week
    curr_week_match = re.search(r'W(?:eek)?\s*(\d+)', ela_header, re.IGNORECASE)
    if curr_week_match and spelling_week_num:
        curr_week_num = int(curr_week_match.group(1))
        if spelling_week_num < curr_week_num:
            print(f"[SCRAPER] Hiding Spelling section: list is for Week {spelling_week_num}, active week is Week {curr_week_num}")
            spelling_words = []
            spelling_title = ""

    extracted['subjects']['Language Arts'] = {
        'template_type': 'ela',
        'teacher': 'Mrs. Tasneim Khalifa',
        'module': ela_module,
        'week_header': ela_header,
        'writing_tasks': ela_writing,
        'ixl_due': ela_ixl_due,
        'ixl_items': ela_ixls,
        'spelling_title': spelling_title,
        'spelling_words': spelling_words,
        'tests': find_tests(ela_block)
    }

    # ----------------------------------------------------
    # TEMPLATE 2: Science & Social Studies (Mrs. Tasneim)
    # ----------------------------------------------------
    def parse_science_ss(lines, subject):
        header, block = extract_current_week_block(lines)
        print(f"[SCRAPER] {subject} current week block: {header}")
        module_name = ""
        video_summary = ""
        ixl_due = ""
        ixl_items = []
        tasks = []
        after_ixl = False

        i = 0
        while i < len(block):
            item = block[i]
            low = item.lower()
            if item == 'NO' and i + 1 < len(block) and 'ixl' in block[i + 1].lower():
                ixl_due = "No IXL homework this week"
                # skip the split fragments: 'IXL Homework th', 'is week'
                i += 2
                if i < len(block) and len(block[i]) < 10:
                    i += 1
                continue
            if 'ixl' in low and 'due' in low:
                ixl_due = item
                after_ixl = True
            elif after_ixl and len(item) < 90 and not TEST_RE.search(item) and 'homework' not in low:
                ixl_items.append(item)
            elif ('module' in low or 'studying about' in low) and not TEST_RE.search(item):
                if not module_name:
                    module_name = item
            elif 'summarize' in low:
                video_summary = f"{item} {block[i + 1]}" if i + 1 < len(block) else item
                i += 1
            elif 'youtube' in low:
                video_summary = f"Watch video: {item}"
            elif low.startswith('homework') or 'project' in low or 'experiment' in low:
                tasks.append(item)
            i += 1

        return {
            'template_type': 'science_ss',
            'teacher': 'Mrs. Tasneim Khalifa',
            'module': module_name or subject,
            'week_header': header,
            'video_summary': video_summary,
            'ixl_due': ixl_due,
            'ixl_items': ixl_items,
            'tasks': tasks,
            'tests': find_tests(block)
        }

    extracted['subjects']['Science'] = parse_science_ss(raw_data['science']['lines'], 'Science')
    extracted['subjects']['Social Studies'] = parse_science_ss(raw_data['social_studies']['lines'], 'Social Studies')

    # ----------------------------------------------------
    # TEMPLATE 3: Mathematics (Mrs. Hiba Naffakh)
    # ----------------------------------------------------
    math_sublink = find_subpage_link(raw_data['math']['links'])
    math_lines = []
    if math_sublink:
        print(f"[SCRAPER] Found Math current week link: {math_sublink}")
        math_lines, _ = fetch_site_text(math_sublink)

    math_module = ""
    math_deltamath = False
    math_ixl_codes = []
    math_tests = []
    for idx, line in enumerate(math_lines):
        if re.match(r'^Module\s*\d+', line, re.IGNORECASE):
            math_module = line
            nxt = math_lines[idx + 1] if idx + 1 < len(math_lines) else ''
            if nxt and len(nxt) < 50 and not any(k in nxt for k in ['DeltaMath', 'IXL']):
                math_module = f"{line}: {nxt}"
        elif 'DeltaMath' in line:
            math_deltamath = True
        elif 'IXL' in line:
            code = line.replace('IXL/', '').replace('IXL', '').strip(' :-')
            if code and code not in math_ixl_codes:
                math_ixl_codes.append(code)
        elif TEST_RE.search(line):
            math_tests.append(line)

    extracted['subjects']['Mathematics'] = {
        'template_type': 'math',
        'teacher': 'Mrs. Hiba Naffakh',
        'module': math_module or "Mathematics",
        'has_deltamath': math_deltamath,
        'ixl_codes': math_ixl_codes,
        'tests': math_tests
    }

    # ----------------------------------------------------
    # TEMPLATE 4: Qur'an & Arabic (Mrs. Iman Luteify)
    # ----------------------------------------------------
    quran_sublink = find_subpage_link(raw_data['quran']['links'])
    q_lines = []
    q_links = []
    if quran_sublink:
        print(f"[SCRAPER] Found Qur'an current week link: {quran_sublink}")
        q_lines, q_links = fetch_site_text(quran_sublink)

    quran_week = ""
    for line in q_lines:
        m = re.search(r'(Q\d+\s*Week\s*\d+.*)$', line, re.IGNORECASE)
        if m:
            quran_week = m.group(1).strip()
            break

    def next_surah(idx, lookahead=4):
        for k in range(idx + 1, min(idx + 1 + lookahead, len(q_lines))):
            if re.match(r'^Sura[ht]\b', q_lines[k], re.IGNORECASE):
                name = q_lines[k].strip(' :')
                if '&' not in name and k + 1 < len(q_lines) and '&' in q_lines[k + 1]:
                    latin = re.findall(r'[A-Za-z][A-Za-z\'-]+', q_lines[k + 1].split('&', 1)[1])
                    if latin:
                        name = f"{name} & {' '.join(latin)}"
                return k, name
        return None, None

    main_hifz = ""
    review_surahs = []
    friday_recitation = ""
    quran_tests = []
    current_day = ""
    day_names = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday')

    for idx, line in enumerate(q_lines):
        low = line.lower().strip()
        if low in day_names:
            current_day = line.strip().title()
        if line.strip() == 'حِفظ':
            k, surah = next_surah(idx)
            if surah:
                rng = ayah_range_after(q_lines, k + 2)
                main_hifz = f"{surah} (Ayah {rng})" if rng else surah
        elif 'مراجعة' in line:
            k, surah = next_surah(idx)
            if surah and surah not in review_surahs:
                review_surahs.append(surah)
        elif line.strip() == 'TEST:':
            k, surah = next_surah(idx - 1)
            if surah:
                rng = ayah_range_after(q_lines, k + 2)
                day = f" on {current_day}" if current_day else ""
                quran_tests.append(f"{surah}{' (Ayah ' + rng + ')' if rng else ''} Hifz Test{day}")
        elif 'kahf' in low:
            rng = ayah_range_after(q_lines, idx, 2)
            friday_recitation = f"{line.strip()}{' (Ayah ' + rng + ')' if rng else ''}"

    hifz_name = main_hifz.split(' (')[0]
    review_surahs = [s for s in review_surahs if s != hifz_name]

    # Detect Arabic Activity Platforms (Blooket, Quizlet, Wordwall, Book/Worksheet, etc.)
    arabic_platforms = []
    for l in q_links:
        low_link = l.lower()
        if 'blooket' in low_link and 'Blooket Game' not in arabic_platforms:
            arabic_platforms.append('Blooket Game')
        elif 'quizlet' in low_link and 'Quizlet Flashcards' not in arabic_platforms:
            arabic_platforms.append('Quizlet Flashcards')
        elif 'wordwall' in low_link and 'Wordwall Activity' not in arabic_platforms:
            arabic_platforms.append('Wordwall Activity')
        elif 'liveworksheets' in low_link and 'Interactive Worksheet' not in arabic_platforms:
            arabic_platforms.append('Interactive Worksheet')

    arabic_unit = ""
    study_guide = ""
    flashcards_list = []
    for idx, line in enumerate(q_lines):
        low = line.lower()
        if 'blooket' in low and 'Blooket Game' not in arabic_platforms:
            arabic_platforms.append('Blooket Game')
        if 'quizlet' in low and 'Quizlet Flashcards' not in arabic_platforms:
            arabic_platforms.append('Quizlet Flashcards')
        if 'wordwall' in low and 'Wordwall Activity' not in arabic_platforms:
            arabic_platforms.append('Wordwall Activity')
        if ('notebook' in low or 'book page' in low) and 'Book/Notebook Practice' not in arabic_platforms:
            arabic_platforms.append('Book/Notebook Practice')

        if re.search(r'\bHW\b', line) and not arabic_unit:
            arabic_unit = line.replace('HW', '').strip()
        if 'due date' in low and not study_guide:
            parts = [line]
            for k in range(idx + 1, min(idx + 4, len(q_lines))):
                parts.append(q_lines[k])
                if 'inshallah' in q_lines[k].lower():
                    break
            study_guide = ' '.join(parts)
        if any(k in low for k in ['quizlet', 'wordwall', 'flashcard']) and len(line) < 100:
            if line not in flashcards_list:
                flashcards_list.append(line)

    if arabic_unit and study_guide:
        study_guide = f"{arabic_unit} homework — {study_guide}"

    week_title = ""
    match = re.search(r'Q(\d+)[\s_-]*Week\s*(\d+)', quran_week, re.IGNORECASE)
    if match:
        week_title = f"Quarter {match.group(1)} Week {int(match.group(2))}"
    extracted['week_title'] = week_title or (ela_header.strip(' :') if ela_header else "")

    extracted['subjects']['Qur\'an & Arabic'] = {
        'template_type': 'quran',
        'teacher': 'Mrs. Iman Luteify',
        'week': quran_week,
        'main_hifz': main_hifz,
        'review_surahs': review_surahs,
        'friday_recitation': friday_recitation,
        'arabic_unit': arabic_unit,
        'study_guide': study_guide,
        'arabic_platforms': arabic_platforms,
        'flashcards': flashcards_list,
        'tests': quran_tests
    }

    # ----------------------------------------------------
    # TEMPLATE 5: Islamic Studies (Mrs. Mubeen Fatima)
    # ----------------------------------------------------
    is_sublink = find_subpage_link(raw_data['is_home']['links'] + raw_data['is_5th']['links'])
    is_lines = []
    if is_sublink:
        print(f"[SCRAPER] Found Islamic Studies current week link: {is_sublink}")
        is_lines, _ = fetch_site_text(is_sublink)

    is_tests = []
    is_tasks = []
    is_topic = ""
    for line in is_lines:
        low = line.lower()
        if TEST_RE.search(line):
            is_tests.append(line)
        elif 'wordwall' in low or 'assignment' in low or 'homework' in low or 'project' in low or 'worksheet' in low:
            task = re.sub(r':?\s*click$', '', line).strip()
            if task not in is_tasks:
                is_tasks.append(task)
        elif re.match(r'^(Belief in|Chapter|Lesson|Unit|Topic)\b', line) and len(line) > 12 and 'presentation' not in low:
            is_topic = line.replace('continued.', '').replace('continued', '').strip(' .')
    # Prefer the detailed test announcements (with a date) over short agenda repeats
    dated = [t for t in is_tests if re.search(r'(monday|tuesday|wednesday|thursday|friday|\d)', t, re.IGNORECASE)]
    is_tests = dated or is_tests

    extracted['subjects']['Islamic Studies'] = {
        'template_type': 'is',
        'teacher': 'Mrs. Mubeen Fatima',
        'chapter_topic': is_topic,
        'subtopics': [],
        'workbook_task': '',
        'presentation_task': '',
        'tasks': is_tasks,
        'tests': is_tests
    }

    # ----------------------------------------------------
    # TEMPLATE 6: Computers (Mrs. Mubeen Fatima)
    # ----------------------------------------------------
    comp_sublink = find_subpage_link(raw_data['comp_home']['links'] + raw_data['comp_5th']['links'])
    comp_lines = []
    if comp_sublink:
        print(f"[SCRAPER] Found Computers current week link: {comp_sublink}")
        comp_lines, _ = fetch_site_text(comp_sublink)

    comp_topic = ""
    edclub_task = ""
    typing_task = ""
    comp_tests = []
    for idx, line in enumerate(comp_lines):
        low = line.lower()
        if low.startswith('lesson') and ':' in line:
            comp_topic = line.split(':', 1)[1].strip()
        elif low.startswith('complete lesson'):
            parts = [line] + [p for p in comp_lines[idx + 1: idx + 4] if len(p) < 10]
            area = next((l for l in comp_lines if 'digital citizenship' in l.lower()), '')
            edclub_task = ' '.join(parts)
            if area:
                edclub_task = f"Edclub: {edclub_task} ({area.replace('Click on start under', '').strip()})"
        elif 'typing' in low and not typing_task:
            typing_task = line
        elif TEST_RE.search(line):
            comp_tests.append(line)

    extracted['subjects']['Computers'] = {
        'template_type': 'computers',
        'teacher': 'Mrs. Mubeen Fatima',
        'tech_topic': comp_topic,
        'edclub_task': edclub_task,
        'typing_task': typing_task,
        'tests': comp_tests
    }

    return extracted


if __name__ == '__main__':
    import json
    print(json.dumps(parse_all_subjects(), indent=2, ensure_ascii=False))
