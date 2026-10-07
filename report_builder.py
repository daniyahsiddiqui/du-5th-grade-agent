import os
import re
from datetime import datetime

def generate_markdown_report(data):
    date_str = data.get('scrape_date', datetime.now().strftime('%Y-%m-%d'))
    week_title = data.get('week_title') or data.get('subjects', {}).get("Qur'an & Arabic", {}).get('week') or "This Week"
    if week_title.startswith("Q1"):
        week_title = week_title.replace("Q1", "Quarter 1")
    elif week_title.startswith("Q2"):
        week_title = week_title.replace("Q2", "Quarter 2")
    
    md = []
    md.append(f"# 📋 DU 5th Grade Weekly Homework Digest & Student Checklist")
    md.append(f"## 🗓️ {week_title}")
    md.append(f"**Report Date:** {date_str} | **Grade:** 5th Grade\n")
    
    # 1. High Priority Tests & Deadlines
    md.append("## 🚨 Upcoming Tests & High Priority Deadlines")
    has_tests = False
    for subj_name, subj_data in data['subjects'].items():
        for test in subj_data.get('tests', []):
            if test:
                has_tests = True
                md.append(f"- **{subj_name}**: {test}")
    if not has_tests:
        md.append("- No explicit upcoming tests flagged for this week. Check subject details below.")
    md.append("")

    # 2. Printable Weekly Homework Checklist
    md.append("## 🔲 Weekly Student Homework Checklist")
    md.append("*Print this page and check off each item as you complete it throughout the week!*\n")

    subjects = data['subjects']

    # --- 1. ELA & SPELLING ---
    if 'Language Arts' in subjects:
        ela = subjects['Language Arts']
        md.append(f"### Language Arts *(Teacher: {ela['teacher']})*")
        md.append(f"**Current Unit/Module:** {ela['module']}")
        for task in ela.get('writing_tasks', []):
            md.append(f"- [ ] 📝 {task}")
        if ela.get('ixl_items'):
            due_str = f" ({ela['ixl_due']})" if ela.get('ixl_due') else ""
            md.append(f"- [ ] 🎯 **[IXL Homework - {len(ela['ixl_items'])} IXL(s) Assigned{due_str}]**")
            for ixl in ela['ixl_items']:
                md.append(f"  - [ ] 🎯 **[IXL]** {ixl}")
        elif ela.get('ixl_due'):
            md.append(f"- ℹ️ {ela['ixl_due']}")
        md.append("")

    # --- 2. SCIENCE & SOCIAL STUDIES ---
    for s_name in ['Science', 'Social Studies']:
        if s_name in subjects:
            s_data = subjects[s_name]
            md.append(f"### {s_name} *(Teacher: {s_data['teacher']})*")
            md.append(f"**Current Unit/Module:** {s_data['module']}")
            for task in s_data.get('tasks', []):
                md.append(f"- [ ] 📝 {task}")
            if s_data.get('video_summary'):
                md.append(f"- [ ] 🎬 {s_data['video_summary']}")
            if s_data.get('ixl_items'):
                due_str = f" ({s_data['ixl_due']})" if s_data.get('ixl_due') else ""
                md.append(f"- [ ] 🎯 **[IXL Homework - {len(s_data['ixl_items'])} IXL(s) Assigned{due_str}]**")
                for ixl in s_data['ixl_items']:
                    md.append(f"  - [ ] 🎯 **[IXL]** {ixl}")
            elif s_data.get('ixl_due'):
                md.append(f"- ℹ️ {s_data['ixl_due']}")
            md.append("")

    # --- 3. MATHEMATICS ---
    if 'Mathematics' in subjects:
        m_data = subjects['Mathematics']
        md.append(f"### Mathematics *(Teacher: {m_data['teacher']})*")
        md.append(f"**Current Unit/Module:** {m_data['module']}")
        if m_data.get('has_deltamath'):
            md.append("- [ ] 📐 **[DeltaMath Assignment]** Complete online DeltaMath module")
        if m_data.get('ixl_codes'):
            md.append(f"- [ ] 🎯 **[IXL Homework - {len(m_data['ixl_codes'])} Skill(s) Assigned]**")
            for code in m_data['ixl_codes']:
                md.append(f"  - [ ] 🎯 **[IXL Skill Code]** {code}")
        md.append("")

    # --- 4. QUR'AN & ARABIC ---
    if "Qur'an & Arabic" in subjects:
        q_data = subjects["Qur'an & Arabic"]
        md.append(f"### Qur'an & Arabic *(Teacher: {q_data['teacher']})*")
        if q_data.get('week'):
            md.append(f"**Active Week:** {q_data['week']}")
        md.append("**📖 Qur'an (Hifz & Recitation):**")
        if q_data.get('main_hifz'):
            md.append(f"- [ ] 🎯 **Main Hifz Assignment:** {q_data['main_hifz']}")
        if q_data.get('review_surahs'):
            md.append(f"- [ ] 📖 **Weekly Review Surahs:** {', '.join(q_data['review_surahs'])}")
        if q_data.get('friday_recitation'):
            md.append(f"- [ ] 🕌 **Friday Surah Practice:** {q_data['friday_recitation']}")
        
        if q_data.get('arabic_unit') or q_data.get('study_guide') or q_data.get('arabic_platforms') or q_data.get('flashcards'):
            md.append("**📝 Arabic Class:**")
            if q_data.get('arabic_unit'):
                md.append(f"- [ ] 📚 **Unit Title:** {q_data['arabic_unit']}")
            if q_data.get('arabic_platforms'):
                md.append(f"- [ ] 🎮 **Activity Platforms:** {', '.join(q_data['arabic_platforms'])}")
            if q_data.get('study_guide'):
                md.append(f"- [ ] 📝 **Homework:** {q_data['study_guide']}")
            if q_data.get('flashcards'):
                md.append(f"- [ ] 🎴 **Quizlet & Wordwall Flashcard Review:**")
                for fc in q_data['flashcards']:
                    md.append(f"  - [ ] {fc}")
        md.append("")

    # --- 5. ISLAMIC STUDIES ---
    if 'Islamic Studies' in subjects:
        is_data = subjects['Islamic Studies']
        md.append(f"### Islamic Studies *(Teacher: {is_data['teacher']})*")
        if is_data.get('chapter_topic'):
            md.append(f"**Chapter Topic:** {is_data['chapter_topic']}")
        if is_data.get('subtopics'):
            md.append(f"**Lesson Coverage:** {', '.join(is_data['subtopics'])}")
        for task in is_data.get('tasks', []):
            md.append(f"- [ ] 📝 {task}")
        if is_data.get('workbook_task'):
            md.append(f"- [ ] 📝 {is_data['workbook_task']}")
        if is_data.get('presentation_task'):
            md.append(f"- [ ] 💻 {is_data['presentation_task']}")
        md.append("")

    # --- 6. COMPUTERS ---
    if 'Computers' in subjects:
        c_data = subjects['Computers']
        md.append(f"### Computers *(Teacher: {c_data['teacher']})*")
        if c_data.get('tech_topic'):
            md.append(f"**Tech Unit:** {c_data['tech_topic']}")
        if c_data.get('edclub_task'):
            md.append(f"- [ ] 💻 {c_data['edclub_task']}")
        if c_data.get('typing_task'):
            md.append(f"- [ ] ⌨️ {c_data['typing_task']}")
        md.append("")

    # 3. Spelling Words Section
    spelling = subjects.get('Language Arts', {}).get('spelling_words', [])
    if spelling:
        md.append("## 📖 Weekly Spelling & Vocabulary Words")
        md.append(", ".join([f"**{i+1}.** {w}" for i, w in enumerate(spelling)]))
        md.append("\n")

    # 4. Announcements Section
    events = data.get('upcoming_events', [])
    if events:
        md.append("## 📢 School Announcements & Upcoming Events")
        for ev in events:
            md.append(f"- 🗓️ {ev}")
        md.append("")

    md.append("---\n*Generated automatically by DU 5th Grade Weekly Agent.*")
    return "\n".join(md)

def generate_html_report(data):
    date_str = data.get('scrape_date', datetime.now().strftime('%Y-%m-%d'))
    week_title = data.get('week_title') or data.get('subjects', {}).get("Qur'an & Arabic", {}).get('week') or "This Week"
    if week_title.startswith("Q1"):
        week_title = week_title.replace("Q1", "Quarter 1")
    elif week_title.startswith("Q2"):
        week_title = week_title.replace("Q2", "Quarter 2")

    subjects = data['subjects']
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DU 5th Grade Weekly Digest & Checklist</title>
    <style>
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #e2e8f0;
        }}
        .header {{
            border-bottom: 3px solid #0284c7;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .header h1 {{ margin: 0; color: #0f172a; font-size: 24px; }}
        .header .week-badge {{
            font-size: 16px; font-weight: 800; color: #1e3a8a; background: #e0f2fe;
            border-left: 4px solid #0284c7; padding: 4px 12px; border-radius: 4px;
            margin: 8px 0 6px 0; display: inline-block;
        }}
        .header .meta {{ color: #64748b; font-size: 14px; margin-top: 5px; }}
        .print-btn {{
            background-color: #0284c7;
            color: #ffffff;
            border: none;
            padding: 8px 14px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: background-color 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        .print-btn:hover {{
            background-color: #0369a1;
        }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{
            font-size: 18px; font-weight: 700; color: #0f172a;
            border-bottom: 1px solid #cbd5e1; padding-bottom: 6px; margin-bottom: 15px;
        }}
        .alert-box {{
            background-color: #fef2f2; border-left: 4px solid #ef4444;
            padding: 12px 16px; border-radius: 6px; margin-bottom: 20px;
        }}
        .alert-box h3 {{ margin: 0 0 6px 0; color: #991b1b; font-size: 16px; }}
        .subject-card {{
            background: #f8fafc; border: 1px solid #e2e8f0;
            border-radius: 8px; padding: 15px; margin-bottom: 15px;
            page-break-inside: avoid;
        }}
        .subject-header {{
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
        }}
        .subject-name {{ font-size: 16px; font-weight: 700; color: #0284c7; }}
        .teacher-name {{ font-size: 13px; color: #64748b; font-style: italic; }}
        .topic-tag {{
            display: inline-block; background: #e0f2fe; color: #0369a1;
            font-size: 12px; font-weight: 600; padding: 3px 8px; border-radius: 4px; margin-bottom: 10px;
        }}
        .ixl-badge {{
            background: #dbeafe; color: #1e40af; font-size: 11px; font-weight: 700;
            padding: 2px 6px; border-radius: 4px; text-transform: uppercase;
        }}
        .deltamath-badge {{
            background: #fef3c7; color: #92400e; font-size: 11px; font-weight: 700;
            padding: 2px 6px; border-radius: 4px; text-transform: uppercase;
        }}
        .task-list {{ list-style: none; padding: 0; margin: 0; }}
        .task-item {{
            display: flex; align-items: flex-start; gap: 10px;
            padding: 6px 0; font-size: 14px; border-bottom: 1px dashed #f1f5f9;
        }}
        .task-item input[type="checkbox"] {{
            width: 18px; height: 18px; margin-top: 2px; cursor: pointer; accent-color: #0284c7;
        }}
        .sub-task-list {{ padding-left: 28px; list-style: none; margin: 4px 0; }}
        .spelling-grid {{
            display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
            gap: 8px; background: #f1f5f9; padding: 12px; border-radius: 6px;
        }}
        .spelling-word {{ font-size: 13px; font-weight: 600; color: #334155; }}
        .footer {{
            text-align: center; font-size: 12px; color: #94a3b8;
            margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; border: none; padding: 0; max-width: 100%; }}
            .subject-card {{ border: 1px solid #cbd5e1; margin-bottom: 10px; padding: 10px; }}
            .no-print, .print-btn {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h1>📋 DU 5th Grade Weekly Digest & Student Checklist</h1>
                    <div class="week-badge">🗓️ {week_title}</div>
                    <div class="meta"><strong>Report Date:</strong> {date_str} | Weekly Homework & Test Tracker</div>
                </div>
                <button class="print-btn no-print" onclick="window.print()" title="Print Report">
                    🖨️ Print Report
                </button>
            </div>
        </div>

        <!-- High Priority Alerts -->
        <div class="alert-box">
            <h3>🚨 Upcoming Tests & Important Deadlines</h3>
            <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #7f1d1d;">
"""

    has_tests = False
    for subj_name, subj_data in subjects.items():
        for test in subj_data.get('tests', []):
            if test:
                has_tests = True
                html += f"<li><strong>{subj_name}:</strong> {test}</li>"
    if not has_tests:
        html += "<li>No explicit tests flagged for this week. Please review individual subject checklists below.</li>"

    html += """
            </ul>
        </div>

        <!-- Weekly Student Checklist -->
        <div class="section">
            <div class="section-title">🔲 Weekly Student Homework Checklist</div>
"""

    # --- 1. ELA & SPELLING ---
    if 'Language Arts' in subjects:
        ela = subjects['Language Arts']
        html += f"""
        <div class="subject-card">
            <div class="subject-header">
                <span class="subject-name">Language Arts</span>
                <span class="teacher-name">{ela['teacher']}</span>
            </div>
            <div class="topic-tag">Unit/Module: {ela['module']}</div>
            <ul class="task-list">
"""
        for task in ela.get('writing_tasks', []):
            html += f'<li class="task-item"><input type="checkbox"><div>📝 <strong>{task}</strong></div></li>'
        if ela.get('ixl_items'):
            due_str = f" ({ela['ixl_due']})" if ela.get('ixl_due') else ""
            html += f'''
                <li class="task-item">
                    <input type="checkbox">
                    <div><span class="ixl-badge">🎯 IXL Homework</span> <strong>{len(ela['ixl_items'])} IXL(s) Assigned{due_str}</strong></div>
                </li>
                <ul class="sub-task-list">
'''
            for ixl in ela['ixl_items']:
                html += f'<li class="task-item"><input type="checkbox"><div><span class="ixl-badge">IXL</span> {ixl}</div></li>'
            html += '</ul>'
        elif ela.get('ixl_due'):
            html += f'<li class="task-item"><div>ℹ️ {ela["ixl_due"]}</div></li>'
        html += "</ul></div>"

    # --- 2. SCIENCE & SOCIAL STUDIES ---
    for s_name in ['Science', 'Social Studies']:
        if s_name in subjects:
            s_data = subjects[s_name]
            html += f"""
            <div class="subject-card">
                <div class="subject-header">
                    <span class="subject-name">{s_name}</span>
                    <span class="teacher-name">{s_data['teacher']}</span>
                </div>
                <div class="topic-tag">Module: {s_data['module']}</div>
                <ul class="task-list">
"""
            for task in s_data.get('tasks', []):
                html += f'<li class="task-item"><input type="checkbox"><div>📝 {task}</div></li>'
            if s_data.get('video_summary'):
                html += f'<li class="task-item"><input type="checkbox"><div>🎬 {s_data["video_summary"]}</div></li>'
            if s_data.get('ixl_items'):
                due_str = f" ({s_data['ixl_due']})" if s_data.get('ixl_due') else ""
                html += f'''
                    <li class="task-item">
                        <input type="checkbox">
                        <div><span class="ixl-badge">🎯 IXL Homework</span> <strong>{len(s_data['ixl_items'])} IXL(s) Assigned{due_str}</strong></div>
                    </li>
                    <ul class="sub-task-list">
'''
                for ixl in s_data['ixl_items']:
                    html += f'<li class="task-item"><input type="checkbox"><div><span class="ixl-badge">IXL</span> {ixl}</div></li>'
                html += '</ul>'
            elif s_data.get('ixl_due'):
                html += f'<li class="task-item"><div>ℹ️ {s_data["ixl_due"]}</div></li>'
            html += "</ul></div>"

    # --- 3. MATHEMATICS ---
    if 'Mathematics' in subjects:
        m_data = subjects['Mathematics']
        html += f"""
        <div class="subject-card">
            <div class="subject-header">
                <span class="subject-name">Mathematics</span>
                <span class="teacher-name">{m_data['teacher']}</span>
            </div>
            <div class="topic-tag">Module: {m_data['module']}</div>
            <ul class="task-list">
"""
        if m_data.get('has_deltamath'):
            html += '<li class="task-item"><input type="checkbox"><div><span class="deltamath-badge">📐 DeltaMath</span> Complete online DeltaMath assignment</div></li>'
        if m_data.get('ixl_codes'):
            html += f'''
                <li class="task-item">
                    <input type="checkbox">
                    <div><span class="ixl-badge">🎯 IXL Homework</span> <strong>{len(m_data['ixl_codes'])} Skill(s) Assigned</strong></div>
                </li>
                <ul class="sub-task-list">
'''
            for code in m_data['ixl_codes']:
                html += f'<li class="task-item"><input type="checkbox"><div><span class="ixl-badge">IXL Skill</span> {code}</div></li>'
            html += '</ul>'
        html += "</ul></div>"

    # --- 4. QUR'AN & ARABIC ---
    if "Qur'an & Arabic" in subjects:
        q_data = subjects["Qur'an & Arabic"]
        html += f"""
        <div class="subject-card">
            <div class="subject-header">
                <span class="subject-name">Qur'an & Arabic</span>
                <span class="teacher-name">{q_data['teacher']}</span>
            </div>
"""
        if q_data.get('week'):
            html += f'<div class="topic-tag">Active Week: {q_data["week"]}</div>'
        html += """
            <div style="font-weight: 700; color: #0f172a; margin-top: 8px; margin-bottom: 4px;">📖 Qur'an (Hifz & Recitation):</div>
            <ul class="task-list">
"""
        if q_data.get('main_hifz'):
            html += f'<li class="task-item"><input type="checkbox"><div>🎯 <strong>Main Hifz Assignment:</strong> {q_data["main_hifz"]}</div></li>'
        if q_data.get('review_surahs'):
            html += f'<li class="task-item"><input type="checkbox"><div>📖 <strong>Weekly Review Surahs:</strong> {", ".join(q_data["review_surahs"])}</div></li>'
        if q_data.get('friday_recitation'):
            html += f'<li class="task-item"><input type="checkbox"><div>🕌 <strong>Friday Recitation:</strong> {q_data["friday_recitation"]}</div></li>'
        html += """
            </ul>
"""
        if q_data.get('arabic_unit') or q_data.get('study_guide') or q_data.get('arabic_platforms') or q_data.get('flashcards'):
            html += """
            <div style="font-weight: 700; color: #0f172a; margin-top: 12px; margin-bottom: 4px;">📝 Arabic Class:</div>
            <ul class="task-list">
"""
            if q_data.get('arabic_unit'):
                html += f'<li class="task-item"><input type="checkbox"><div>📚 <strong>Unit Title:</strong> {q_data["arabic_unit"]}</div></li>'
            if q_data.get('arabic_platforms'):
                html += f'<li class="task-item"><input type="checkbox"><div>🎮 <strong>Activity Platforms:</strong> {", ".join(q_data["arabic_platforms"])}</div></li>'
            if q_data.get('study_guide'):
                html += f'<li class="task-item"><input type="checkbox"><div>📝 <strong>Homework:</strong> {q_data["study_guide"]}</div></li>'
            if q_data.get('flashcards'):
                html += f'<li class="task-item"><input type="checkbox"><div>🎴 <strong>Quizlet & Wordwall Flashcards:</strong></div></li><ul class="sub-task-list">'
                for fc in q_data['flashcards']:
                    html += f'<li class="task-item"><input type="checkbox"><div>{fc}</div></li>'
                html += '</ul>'
            html += '</ul>'
        html += "</div>"

    # --- 5. ISLAMIC STUDIES ---
    if 'Islamic Studies' in subjects:
        is_data = subjects['Islamic Studies']
        html += f"""
        <div class="subject-card">
            <div class="subject-header">
                <span class="subject-name">Islamic Studies</span>
                <span class="teacher-name">{is_data['teacher']}</span>
            </div>
"""
        if is_data.get('chapter_topic'):
            html += f'<div class="topic-tag">Chapter: {is_data["chapter_topic"]}</div>'
        if is_data.get('subtopics'):
            html += f'<div style="font-size: 13px; color: #64748b; margin-bottom: 8px;">Coverage: {", ".join(is_data["subtopics"])}</div>'
        html += '<ul class="task-list">'
        for task in is_data.get('tasks', []):
            html += f'<li class="task-item"><input type="checkbox"><div>📝 {task}</div></li>'
        if is_data.get('workbook_task'):
            html += f'<li class="task-item"><input type="checkbox"><div>📝 {is_data["workbook_task"]}</div></li>'
        if is_data.get('presentation_task'):
            html += f'<li class="task-item"><input type="checkbox"><div>💻 {is_data["presentation_task"]}</div></li>'
        html += "</ul></div>"

    # --- 6. COMPUTERS ---
    if 'Computers' in subjects:
        c_data = subjects['Computers']
        html += f"""
        <div class="subject-card">
            <div class="subject-header">
                <span class="subject-name">Computers</span>
                <span class="teacher-name">{c_data['teacher']}</span>
            </div>
"""
        if c_data.get('tech_topic'):
            html += f'<div class="topic-tag">Tech Unit: {c_data["tech_topic"]}</div>'
        html += '<ul class="task-list">'
        if c_data.get('edclub_task'):
            html += f'<li class="task-item"><input type="checkbox"><div>💻 {c_data["edclub_task"]}</div></li>'
        if c_data.get('typing_task'):
            html += f'<li class="task-item"><input type="checkbox"><div>⌨️ {c_data["typing_task"]}</div></li>'
        html += """
            </ul>
        </div>
"""

    # Spelling Words Section
    spelling = subjects.get('Language Arts', {}).get('spelling_words', [])
    if spelling:
        html += """
        <div class="section">
            <div class="section-title">📖 Weekly Spelling & Vocabulary Words</div>
            <div class="spelling-grid">
"""
        for i, word in enumerate(spelling):
            html += f'<div class="spelling-word">{i+1}. {word}</div>'
        html += """
            </div>
        </div>
"""

    # Announcements Section
    events = data.get('upcoming_events', [])
    if events:
        html += """
        <div class="section">
            <div class="section-title">📢 School Announcements & Upcoming Events</div>
            <ul style="padding-left: 20px; font-size: 14px;">
"""
    html += """
        <div class="footer">
            Darul Uloom 5th Grade Automated Weekly Agent • Generated on demand
        </div>
    </div>
</body>
</html>
"""
    return html

def generate_dashboard_html_report(data, grade_name="5th Grade"):
    date_str = data.get('scrape_date', datetime.now().strftime('%Y-%m-%d'))
    week_title = data.get('week_title') or data.get('subjects', {}).get("Qur'an & Arabic", {}).get('week') or "This Week"
    if week_title.startswith("Q1"):
        week_title = week_title.replace("Q1", "Quarter 1")
    elif week_title.startswith("Q2"):
        week_title = week_title.replace("Q2", "Quarter 2")

    subjects = data.get('subjects', {})

    all_tests = []
    for subj_name, subj_data in subjects.items():
        for test in subj_data.get('tests', []):
            if test and len(test.strip()) > 3:
                all_tests.append((subj_name, test.strip()))

    left_subjects = []
    right_subjects = []
    right_keywords = ["qur'an", "quran", "arabic", "islamic", "computer", "tech"]

    for subj_name, subj_data in subjects.items():
        is_right = any(k in subj_name.lower() for k in right_keywords)
        if is_right:
            right_subjects.append((subj_name, subj_data))
        else:
            left_subjects.append((subj_name, subj_data))

    if not left_subjects and right_subjects:
        half = (len(right_subjects) + 1) // 2
        left_subjects = right_subjects[:half]
        right_subjects = right_subjects[half:]
    elif not right_subjects and left_subjects:
        half = (len(left_subjects) + 1) // 2
        right_subjects = left_subjects[half:]
        left_subjects = left_subjects[:half]

    def get_color_accent(subj_name):
        s = subj_name.lower()
        if "lang" in s or "ela" in s or "english" in s:
            return "#2563eb", "#dbeafe", "#1e40af"
        elif "math" in s or "algebra" in s or "geom" in s:
            return "#059669", "#d1fae5", "#065f46"
        elif "sci" in s or "phys" in s or "chem" in s or "bio" in s:
            return "#7c3aed", "#ede9fe", "#5b21b6"
        elif "soc" in s or "hist" in s or "geog" in s:
            return "#0284c7", "#e0f2fe", "#075985"
        elif "qur" in s or "arab" in s:
            return "#d97706", "#fef3c7", "#92400e"
        elif "islam" in s:
            return "#4f46e5", "#e0e7ff", "#3730a3"
        elif "comp" in s or "tech" in s:
            return "#06b6d4", "#cffaffe", "#155e75"
        else:
            return "#3b82f6", "#dbeafe", "#1e40af"

    def render_card(subj_name, subj_data):
        main_color, bg_light, text_dark = get_color_accent(subj_name)
        teacher = subj_data.get('teacher', 'Subject Teacher')
        module = subj_data.get('module') or subj_data.get('chapter_topic') or subj_data.get('arabic_unit') or subj_data.get('tech_topic') or subj_data.get('week') or ""
        
        card_html = f'''
        <div class="dash-card" style="border-top: 4px solid {main_color};">
            <div class="dash-card-header">
                <span class="dash-subj-name">{subj_name}</span>
                <span class="dash-teacher">{teacher}</span>
            </div>
        '''
        if module and module != subj_name:
            card_html += f'<div class="dash-module-pill" style="background: {bg_light}; color: {text_dark};">{module}</div>'

        card_html += '<ul class="dash-task-list">'

        writing = subj_data.get('writing_tasks', [])
        for w in writing:
            card_html += f'<li class="dash-task-item"><span class="check-box">📝</span> <span>{w}</span></li>'

        if subj_data.get('video_summary'):
            card_html += f'<li class="dash-task-item"><span class="check-box">🎬</span> <span>{subj_data["video_summary"]}</span></li>'

        ixl_items = subj_data.get('ixl_items', [])
        if ixl_items:
            due_str = f" ({subj_data['ixl_due']})" if subj_data.get('ixl_due') else ""
            card_html += f'<li class="dash-task-item"><span class="badge badge-ixl">IXL</span> <strong>{len(ixl_items)} IXL Skill(s) Assigned{due_str}</strong></li>'
            for ixl in ixl_items:
                card_html += f'<li class="dash-task-item dash-sub-item"><span class="check-box">☐</span> <span>{ixl}</span></li>'
        elif subj_data.get('ixl_due') and subj_data.get('ixl_due') != "No IXL homework this week":
            card_html += f'<li class="dash-task-item"><span class="badge badge-ixl">IXL</span> <span>{subj_data["ixl_due"]}</span></li>'

        if subj_data.get('has_deltamath'):
            card_html += '<li class="dash-task-item"><span class="badge badge-deltamath">DeltaMath</span> <strong>Online DeltaMath Module Assigned</strong></li>'
        if subj_data.get('ixl_codes'):
            card_html += f'<li class="dash-task-item"><span class="badge badge-ixl">IXL</span> <strong>Skill Codes: {", ".join(subj_data["ixl_codes"])}</strong></li>'

        if subj_data.get('main_hifz'):
            card_html += f'<li class="dash-task-item"><span class="badge badge-hifz">Hifz</span> <strong>{subj_data["main_hifz"]}</strong></li>'
        if subj_data.get('review_surahs'):
            card_html += f'<li class="dash-task-item"><span class="check-box">📖</span> <span><strong>Review:</strong> {", ".join(subj_data["review_surahs"])}</span></li>'
        if subj_data.get('friday_recitation'):
            card_html += f'<li class="dash-task-item"><span class="check-box">🕌</span> <span><strong>Friday:</strong> {subj_data["friday_recitation"]}</span></li>'
        if subj_data.get('arabic_unit'):
            card_html += f'<li class="dash-task-item"><span class="badge badge-arabic">Arabic</span> <span><strong>Unit:</strong> {subj_data["arabic_unit"]}</span></li>'
        if subj_data.get('study_guide'):
            card_html += f'<li class="dash-task-item"><span class="check-box">📝</span> <span>{subj_data["study_guide"]}</span></li>'
        if subj_data.get('arabic_platforms'):
            card_html += f'<li class="dash-task-item"><span class="check-box">🎮</span> <span><strong>Platforms:</strong> {", ".join(subj_data["arabic_platforms"])}</span></li>'

        tasks = subj_data.get('tasks', [])
        for t in tasks:
            t_clean = t.strip()
            if t_clean:
                if 'IXL' in t_clean:
                    card_html += f'<li class="dash-task-item"><span class="badge badge-ixl">IXL</span> <span>{t_clean}</span></li>'
                elif 'DeltaMath' in t_clean:
                    card_html += f'<li class="dash-task-item"><span class="badge badge-deltamath">DeltaMath</span> <span>{t_clean}</span></li>'
                else:
                    card_html += f'<li class="dash-task-item"><span class="check-box">📝</span> <span>{t_clean}</span></li>'

        if subj_data.get('workbook_task'):
            card_html += f'<li class="dash-task-item"><span class="check-box">📝</span> <span>{subj_data["workbook_task"]}</span></li>'
        if subj_data.get('presentation_task'):
            card_html += f'<li class="dash-task-item"><span class="check-box">💻</span> <span>{subj_data["presentation_task"]}</span></li>'
        if subj_data.get('edclub_task'):
            card_html += f'<li class="dash-task-item"><span class="check-box">💻</span> <span>{subj_data["edclub_task"]}</span></li>'
        if subj_data.get('typing_task'):
            card_html += f'<li class="dash-task-item"><span class="check-box">⌨️</span> <span>{subj_data["typing_task"]}</span></li>'

        if not (writing or ixl_items or subj_data.get('has_deltamath') or subj_data.get('ixl_codes') or subj_data.get('main_hifz') or tasks or subj_data.get('study_guide') or subj_data.get('workbook_task') or subj_data.get('edclub_task') or subj_data.get('video_summary')):
            card_html += '<li class="dash-task-item" style="color: #94a3b8; font-style: italic;">No explicit homework items listed for this week.</li>'

        card_html += '</ul></div>'
        return card_html

    left_html = "".join([render_card(name, sdata) for name, sdata in left_subjects])
    right_html = "".join([render_card(name, sdata) for name, sdata in right_subjects])

    spelling = subjects.get('Language Arts', {}).get('spelling_words', [])
    spelling_html = ""
    if spelling:
        words_rendered = "".join([f'<div class="spelling-word">{i+1}. {w}</div>' for i, w in enumerate(spelling)])
        spelling_html = f'''
        <div class="spelling-box">
            <div class="spelling-title">📖 Weekly Spelling & Vocabulary Words</div>
            <div class="spelling-grid">
                {words_rendered}
            </div>
        </div>
        '''

    events = data.get('upcoming_events', [])
    events_html = ""
    if events:
        events_list = "".join([f'<li style="margin-bottom: 4px;">🗓️ {ev.strip()}</li>' for ev in events])
        events_html = f'''
        <div class="events-box">
            <div class="spelling-title">📢 School Announcements & Upcoming Events</div>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #334155;">
                {events_list}
            </ul>
        </div>
        '''

    alert_box_html = ""
    if all_tests:
        test_items = "".join([f'<li><strong>{subj}:</strong> {t}</li>' for subj, t in all_tests])
        alert_box_html = f'''
        <div class="alert-card">
            <div class="alert-title">🚨 Upcoming Tests & High Priority Deadlines</div>
            <ul class="alert-list">
                {test_items}
            </ul>
        </div>
        '''
    else:
        alert_box_html = '''
        <div class="alert-card" style="background: #f0fdf4; border-color: #bbf7d0; border-left-color: #22c55e;">
            <div class="alert-title" style="color: #15803d;">✅ Upcoming Tests & High Priority Deadlines</div>
            <div style="font-size: 13px; color: #166534; font-weight: 500;">No high priority tests flagged for this week. Great job staying on top of your studies!</div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080">
    <title>DU {grade_name} Weekly Dashboard</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            margin: 0;
            padding: 24px;
            color: #1e293b;
            width: 1080px;
        }}
        .dashboard {{
            background: #f8fafc;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        }}
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
            color: #ffffff;
            border-radius: 12px;
            padding: 20px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .header-title h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #ffffff;
        }}
        .header-title p {{
            margin: 4px 0 0 0;
            font-size: 13px;
            color: #93c5fd;
            font-weight: 500;
        }}
        .header-badge {{
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.25);
            padding: 8px 16px;
            border-radius: 10px;
            text-align: right;
        }}
        .header-badge .grade {{
            font-size: 16px;
            font-weight: 800;
            color: #38bdf8;
        }}
        .header-badge .date {{
            font-size: 12px;
            color: #cbd5e1;
            margin-top: 2px;
        }}
        
        .alert-card {{
            background: #fff1f2;
            border: 1px solid #fecdd3;
            border-left: 6px solid #e11d48;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 20px;
        }}
        .alert-title {{
            color: #9f1239;
            font-weight: 800;
            font-size: 14px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .alert-list {{
            margin: 0;
            padding-left: 20px;
            color: #881337;
            font-size: 13px;
            font-weight: 600;
        }}
        .alert-list li {{
            margin-bottom: 4px;
        }}

        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
        }}

        .dash-card {{
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            break-inside: avoid;
            margin-bottom: 18px;
        }}
        .dash-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 6px;
        }}
        .dash-subj-name {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
        }}
        .dash-teacher {{
            font-size: 12px;
            color: #64748b;
            font-style: italic;
        }}
        .dash-module-pill {{
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            margin-bottom: 10px;
            display: inline-block;
            max-width: 100%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .dash-task-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .dash-task-item {{
            font-size: 13px;
            padding: 5px 0;
            display: flex;
            align-items: flex-start;
            gap: 8px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
            line-height: 1.4;
        }}
        .dash-task-item:last-child {{
            border-bottom: none;
        }}
        .dash-sub-item {{
            padding-left: 20px;
            color: #475569;
            font-size: 12px;
        }}
        .check-box {{
            color: #0284c7;
            font-weight: bold;
            font-size: 13px;
            flex-shrink: 0;
        }}

        .badge {{
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            flex-shrink: 0;
        }}
        .badge-ixl {{ background: #dbeafe; color: #1e40af; }}
        .badge-deltamath {{ background: #fef3c7; color: #92400e; }}
        .badge-hifz {{ background: #d1fae5; color: #065f46; }}
        .badge-arabic {{ background: #fee2e2; color: #991b1b; }}

        .spelling-box {{
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #6366f1;
            margin-top: 6px;
        }}
        .spelling-title {{
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 10px;
        }}
        .spelling-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
        }}
        .spelling-word {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            color: #334155;
        }}

        .events-box {{
            background: #ffffff;
            border-radius: 10px;
            padding: 16px;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #0ea5e9;
            margin-top: 18px;
        }}

        .footer {{
            text-align: center;
            font-size: 11px;
            color: #94a3b8;
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #e2e8f0;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <div class="header-title">
                <h1>📋 DU WEEKLY STUDENT DASHBOARD</h1>
                <p>Darul Uloom Academy • Weekly Digest & Homework Tracker</p>
            </div>
            <div class="header-badge">
                <div class="grade">{grade_name}</div>
                <div class="date">{week_title} | {date_str}</div>
            </div>
        </div>

        {alert_box_html}

        <div class="grid">
            <div class="column">
                {left_html}
            </div>
            <div class="column">
                {right_html}
                {spelling_html}
                {events_html}
            </div>
        </div>

        <div class="footer">
            Darul Uloom Automated Weekly Agent • 1-Page PNG Graphic Summary
        </div>
    </div>
</body>
</html>
'''
    return html

