import os
import re
from datetime import datetime

def generate_markdown_report(data):
    date_str = data.get('scrape_date', datetime.now().strftime('%Y-%m-%d'))
    week_title = data.get('week_title') or data.get('subjects', {}).get("Qur'an & Arabic", {}).get('week') or "Quarter 1 Week 8"
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
        for task in ela['writing_tasks']:
            md.append(f"- [ ] 📝 {task}")
        if ela.get('ixl_items'):
            due_str = f" ({ela['ixl_due']})" if ela.get('ixl_due') else ""
            md.append(f"- [ ] 🎯 **[IXL Homework - {len(ela['ixl_items'])} IXL(s) Assigned{due_str}]**")
            for ixl in ela['ixl_items']:
                md.append(f"  - [ ] 🎯 **[IXL]** {ixl}")
        md.append("")

    # --- 2. SCIENCE & SOCIAL STUDIES ---
    for s_name in ['Science', 'Social Studies']:
        if s_name in subjects:
            s_data = subjects[s_name]
            md.append(f"### {s_name} *(Teacher: {s_data['teacher']})*")
            md.append(f"**Current Unit/Module:** {s_data['module']}")
            if s_data['video_summary']:
                md.append(f"- [ ] 🎬 {s_data['video_summary']}")
            if s_data['ixl_items']:
                due_str = f" ({s_data['ixl_due']})" if s_data['ixl_due'] else ""
                md.append(f"- [ ] 🎯 **[IXL Homework - {len(s_data['ixl_items'])} IXL(s) Assigned{due_str}]**")
                for ixl in s_data['ixl_items']:
                    md.append(f"  - [ ] 🎯 **[IXL]** {ixl}")
            md.append("")

    # --- 3. MATHEMATICS ---
    if 'Mathematics' in subjects:
        m_data = subjects['Mathematics']
        md.append(f"### Mathematics *(Teacher: {m_data['teacher']})*")
        md.append(f"**Current Unit/Module:** {m_data['module']}")
        if m_data['has_deltamath']:
            md.append("- [ ] 📐 **[DeltaMath Assignment]** Complete online DeltaMath module")
        if m_data['ixl_codes']:
            md.append(f"- [ ] 🎯 **[IXL Homework - {len(m_data['ixl_codes'])} Skill(s) Assigned]**")
            for code in m_data['ixl_codes']:
                md.append(f"  - [ ] 🎯 **[IXL Skill Code]** {code}")
        md.append("")

    # --- 4. QUR'AN & ARABIC ---
    if "Qur'an & Arabic" in subjects:
        q_data = subjects["Qur'an & Arabic"]
        md.append(f"### Qur'an & Arabic *(Teacher: {q_data['teacher']})*")
        md.append(f"**Active Week:** {q_data['week']}")
        md.append("**📖 Qur'an (Hifz & Recitation):**")
        md.append(f"- [ ] 🎯 **Main Hifz Assignment:** {q_data['main_hifz']}")
        if q_data['review_surahs']:
            md.append(f"- [ ] 📖 **Weekly Review Surahs:** {', '.join(q_data['review_surahs'])}")
        md.append(f"- [ ] 🕌 **Friday Surah Practice:** {q_data['friday_recitation']}")
        
        md.append("**📝 Arabic Class:**")
        md.append(f"- [ ] 📚 **Unit Title:** {q_data['arabic_unit']}")
        md.append(f"- [ ] 📝 **Study Guide:** {q_data['study_guide']}")
        if q_data['flashcards']:
            md.append(f"- [ ] 🎴 **Quizlet & Wordwall Flashcard Review:**")
            for fc in q_data['flashcards']:
                md.append(f"  - [ ] {fc}")
        md.append("")

    # --- 5. ISLAMIC STUDIES ---
    if 'Islamic Studies' in subjects:
        is_data = subjects['Islamic Studies']
        md.append(f"### Islamic Studies *(Teacher: {is_data['teacher']})*")
        md.append(f"**Chapter Topic:** {is_data['chapter_topic']}")
        if is_data['subtopics']:
            md.append(f"**Lesson Coverage:** {', '.join(is_data['subtopics'])}")
        md.append(f"- [ ] 📝 {is_data['workbook_task']}")
        if is_data['presentation_task']:
            md.append(f"- [ ] 💻 {is_data['presentation_task']}")
        md.append("")

    # --- 6. COMPUTERS ---
    if 'Computers' in subjects:
        c_data = subjects['Computers']
        md.append(f"### Computers *(Teacher: {c_data['teacher']})*")
        md.append(f"**Tech Unit:** {c_data['tech_topic']}")
        md.append(f"- [ ] 💻 {c_data['edclub_task']}")
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
    week_title = data.get('week_title') or data.get('subjects', {}).get("Qur'an & Arabic", {}).get('week') or "Quarter 1 Week 8"
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
        for task in ela['writing_tasks']:
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
            if s_data['video_summary']:
                html += f'<li class="task-item"><input type="checkbox"><div>🎬 {s_data["video_summary"]}</div></li>'
            if s_data['ixl_items']:
                due_str = f" ({s_data['ixl_due']})" if s_data['ixl_due'] else ""
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
        if m_data['has_deltamath']:
            html += '<li class="task-item"><input type="checkbox"><div><span class="deltamath-badge">📐 DeltaMath</span> Complete online DeltaMath assignment</div></li>'
        if m_data['ixl_codes']:
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
            <div class="topic-tag">Active Week: {q_data['week']}</div>
            <div style="font-weight: 700; color: #0f172a; margin-top: 8px; margin-bottom: 4px;">📖 Qur'an (Hifz & Recitation):</div>
            <ul class="task-list">
                <li class="task-item"><input type="checkbox"><div>🎯 <strong>Main Hifz Assignment:</strong> {q_data['main_hifz']}</div></li>
"""
        if q_data['review_surahs']:
            html += f'<li class="task-item"><input type="checkbox"><div>📖 <strong>Weekly Review Surahs:</strong> {", ".join(q_data["review_surahs"])}</div></li>'
        html += f'<li class="task-item"><input type="checkbox"><div>🕌 <strong>Friday Recitation:</strong> {q_data["friday_recitation"]}</div></li>'
        html += """
            </ul>
            <div style="font-weight: 700; color: #0f172a; margin-top: 12px; margin-bottom: 4px;">📝 Arabic Class:</div>
            <ul class="task-list">
"""
        html += f'<li class="task-item"><input type="checkbox"><div>📚 <strong>Unit Title:</strong> {q_data["arabic_unit"]}</div></li>'
        html += f'<li class="task-item"><input type="checkbox"><div>📝 <strong>Study Guide:</strong> {q_data["study_guide"]}</div></li>'
        if q_data['flashcards']:
            html += f'<li class="task-item"><input type="checkbox"><div>🎴 <strong>Quizlet & Wordwall Flashcards:</strong></div></li><ul class="sub-task-list">'
            for fc in q_data['flashcards']:
                html += f'<li class="task-item"><input type="checkbox"><div>{fc}</div></li>'
            html += '</ul>'
        html += "</ul></div>"

    # --- 5. ISLAMIC STUDIES ---
    if 'Islamic Studies' in subjects:
        is_data = subjects['Islamic Studies']
        html += f"""
        <div class="subject-card">
            <div class="subject-header">
                <span class="subject-name">Islamic Studies</span>
                <span class="teacher-name">{is_data['teacher']}</span>
            </div>
            <div class="topic-tag">Chapter: {is_data['chapter_topic']}</div>
"""
        if is_data['subtopics']:
            html += f'<div style="font-size: 13px; color: #64748b; margin-bottom: 8px;">Coverage: {", ".join(is_data["subtopics"])}</div>'
        html += f'<ul class="task-list"><li class="task-item"><input type="checkbox"><div>📝 {is_data["workbook_task"]}</div></li>'
        if is_data['presentation_task']:
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
            <div class="topic-tag">Tech Unit: {c_data['tech_topic']}</div>
            <ul class="task-list">
                <li class="task-item"><input type="checkbox"><div>💻 {c_data['edclub_task']}</div></li>
                <li class="task-item"><input type="checkbox"><div>⌨️ {c_data['typing_task']}</div></li>
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
        for ev in events:
            html += f"<li>🗓️ {ev}</li>"
        html += """
            </ul>
        </div>
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
