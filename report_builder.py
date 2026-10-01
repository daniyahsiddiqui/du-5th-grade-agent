import os
import re
from datetime import datetime

def generate_markdown_report(data):
    date_str = data.get('scrape_date', datetime.now().strftime('%Y-%m-%d'))
    week_title = data.get('week_title') or "Quarter 1 Week 8 (Sep 28 - Oct 2)"
    if week_title.startswith("Q1"):
        week_title = week_title.replace("Q1", "Quarter 1")
    elif week_title.startswith("Q2"):
        week_title = week_title.replace("Q2", "Quarter 2")
    
    md = []
    md.append(f"# 📋 DU 8th Grade Weekly Homework Digest & Student Checklist")
    md.append(f"## 🗓️ {week_title}")
    md.append(f"**Report Date:** {date_str} | **Grade:** 8th Grade\n")
    
    # 1. High Priority Tests & Deadlines
    md.append("## 🚨 Upcoming Tests & High Priority Deadlines")
    has_tests = False
    for subj_name, subj_data in data['subjects'].items():
        tests = subj_data.get('tests', [])
        for test in tests:
            if test and len(test.strip()) > 3:
                has_tests = True
                md.append(f"- **{subj_name}**: {test.strip()}")
    if not has_tests:
        md.append("- No explicit upcoming tests flagged for this week. Check subject details below.")
    md.append("")

    # 2. Printable Weekly Homework Checklist
    md.append("## 🔲 Weekly Student Homework Checklist")
    md.append("*Print this page and check off each item as you complete it throughout the week!*\n")

    subjects = data['subjects']
    for subj_name, subj_data in subjects.items():
        teacher = subj_data.get('teacher', 'Subject Teacher')
        module = subj_data.get('module', '')
        tasks = subj_data.get('tasks', [])
        
        md.append(f"### {subj_name} *(Teacher: {teacher})*")
        if module and module != subj_name:
            md.append(f"**Current Unit/Topic:** {module}")
        
        if tasks:
            for task in tasks:
                t_clean = task.strip()
                if t_clean:
                    if 'IXL' in t_clean or 'DeltaMath' in t_clean or 'Quizlet' in t_clean or 'Wordwall' in t_clean:
                        md.append(f"- [ ] 🎯 **[{t_clean}]**")
                    else:
                        md.append(f"- [ ] 📝 {t_clean}")
        else:
            md.append("- [ ] No explicit homework listed for this week.")
        md.append("")

    # 3. Announcements & Events Section
    events = data.get('upcoming_events', [])
    if events:
        md.append("## 📢 School Announcements & Upcoming Events")
        for ev in events:
            md.append(f"- 🗓️ {ev.strip()}")
        md.append("")

    md.append("---\n*Generated automatically by DU 8th Grade Weekly Agent • 100% Live Site Fidelity.*")
    return "\n".join(md)

def generate_html_report(data):
    date_str = data.get('scrape_date', datetime.now().strftime('%Y-%m-%d'))
    week_title = data.get('week_title') or "Quarter 1 Week 8 (Sep 28 - Oct 2)"
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
    <title>DU 8th Grade Weekly Digest & Checklist</title>
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
        .task-list {{ list-style: none; padding: 0; margin: 0; }}
        .task-item {{
            display: flex; align-items: flex-start; gap: 10px;
            padding: 6px 0; font-size: 14px; border-bottom: 1px dashed #f1f5f9;
        }}
        .task-item input[type="checkbox"] {{
            width: 18px; height: 18px; margin-top: 2px; cursor: pointer; accent-color: #0284c7;
        }}
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
                    <h1>📋 DU 8th Grade Weekly Digest & Student Checklist</h1>
                    <div class="week-badge">🗓️ {week_title}</div>
                    <div class="meta"><strong>Report Date:</strong> {date_str} | 8th Grade Weekly Homework & Test Tracker</div>
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
            if test and len(test.strip()) > 3:
                has_tests = True
                html += f"<li><strong>{subj_name}:</strong> {test.strip()}</li>"
    if not has_tests:
        html += "<li>No explicit tests flagged for this week. Please review individual subject checklists below.</li>"

    html += """
            </ul>
        </div>

        <!-- Weekly Student Checklist -->
        <div class="section">
            <div class="section-title">🔲 Weekly Student Homework Checklist</div>
"""

    for subj_name, subj_data in subjects.items():
        teacher = subj_data.get('teacher', 'Subject Teacher')
        module = subj_data.get('module', '')
        tasks = subj_data.get('tasks', [])
        
        html += f"""
        <div class="subject-card">
            <div class="subject-header">
                <span class="subject-name">{subj_name}</span>
                <span class="teacher-name">{teacher}</span>
            </div>
"""
        if module and module != subj_name:
            html += f'<div class="topic-tag">Unit/Topic: {module}</div>'
            
        html += '<ul class="task-list">'
        if tasks:
            for task in tasks:
                t_clean = task.strip()
                if t_clean:
                    if 'IXL' in t_clean or 'DeltaMath' in t_clean or 'Quizlet' in t_clean:
                        html += f'<li class="task-item"><input type="checkbox"><div><span class="ixl-badge">ONLINE TASK</span> <strong>{t_clean}</strong></div></li>'
                    else:
                        html += f'<li class="task-item"><input type="checkbox"><div>📝 {t_clean}</div></li>'
        else:
            html += '<li class="task-item"><input type="checkbox"><div>No explicit homework listed for this week.</div></li>'
        html += '</ul></div>'

    # Announcements Section
    events = data.get('upcoming_events', [])
    if events:
        html += """
        <div class="section">
            <div class="section-title">📢 School Announcements & Upcoming Events</div>
            <ul style="padding-left: 20px; font-size: 14px;">
"""
        for ev in events:
            html += f"<li>🗓️ {ev.strip()}</li>"
        html += """
            </ul>
        </div>
"""

    html += """
        <div class="footer">
            Darul Uloom 8th Grade Automated Weekly Agent • 100% Live Site Fidelity
        </div>
    </div>
</body>
</html>
"""
    return html
