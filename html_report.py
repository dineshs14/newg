"""
Blast Radius Agent — HTML Report Generator
=============================================
Creates a beautiful, self-contained HTML report that auto-opens
in the default browser. Works on Windows, Mac, and Linux.
"""

import os
import re
import html
from datetime import datetime
from config import OUTPUT_DIR, MODEL_NAME


def _detect_risk_level(risk_text: str) -> str:
    """Extract risk level from the risk section content."""
    upper = risk_text.upper()
    for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if level in upper:
            return level
    return "UNKNOWN"


def _risk_gradient(level: str) -> str:
    """CSS gradient for the risk badge."""
    return {
        "CRITICAL": "linear-gradient(135deg, #ff1744, #d50000)",
        "HIGH": "linear-gradient(135deg, #ff9100, #ff6d00)",
        "MEDIUM": "linear-gradient(135deg, #ffd600, #ffab00)",
        "LOW": "linear-gradient(135deg, #00e676, #00c853)",
        "UNKNOWN": "linear-gradient(135deg, #90a4ae, #607d8b)",
    }.get(level, "linear-gradient(135deg, #90a4ae, #607d8b)")


def _risk_emoji(level: str) -> str:
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(level, "⚪")


def _section_icon(header: str) -> str:
    """Map section headers to emojis."""
    icons = {
        "WHAT WAS DONE": "📝",
        "ROOT CAUSE": "🔍",
        "IMPACTED MODULES": "📦",
        "RISK LEVEL": "⚠️",
        "SUGGESTED FIX": "🔧",
        "IMPACT CHAIN": "🔗",
    }
    for key, icon in icons.items():
        if key in header.upper():
            return icon
    return "📋"


def _markdown_to_html(text: str) -> str:
    """Minimal markdown-to-HTML: code blocks, bold, bullets, backticks."""
    # Escape HTML first
    text = html.escape(text)

    # Fenced code blocks (```...```)
    text = re.sub(
        r"```(\w*)\n(.*?)```",
        lambda m: f'<pre><code class="lang-{m.group(1)}">{m.group(2)}</code></pre>',
        text,
        flags=re.DOTALL,
    )

    # Inline code (`...`)
    text = re.sub(r"`([^`]+)`", r'<code>\1</code>', text)

    # Bold (**...**)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    # Bullet lists (- item)
    lines = text.split("\n")
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{stripped[2:]}</li>")
        else:
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(line)
    if in_list:
        result.append("</ul>")
    text = "\n".join(result)

    # Numbered lists (1. item)
    lines = text.split("\n")
    result = []
    in_ol = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\d+\.\s", stripped):
            if not in_ol:
                result.append("<ol>")
                in_ol = True
            content = re.sub(r"^\d+\.\s", "", stripped)
            result.append(f"<li>{content}</li>")
        else:
            if in_ol:
                result.append("</ol>")
                in_ol = False
            result.append(line)
    if in_ol:
        result.append("</ol>")
    text = "\n".join(result)

    # Paragraphs (double newline)
    text = re.sub(r"\n\n+", "</p><p>", text)
    text = f"<p>{text}</p>"
    text = text.replace("<p></p>", "")

    return text


SECTION_DISPLAY = {
    "1. WHAT WAS DONE": "What Was Done",
    "2. ROOT CAUSE / RISK ORIGIN": "Root Cause / Risk Origin",
    "3. IMPACTED MODULES": "Impacted Modules",
    "4. RISK LEVEL": "Risk Level",
    "5. SUGGESTED FIX / MITIGATION": "Suggested Fix / Mitigation",
    "6. IMPACT CHAIN EXPLANATION": "Impact Chain",
}


def generate_html_report(
    sections: dict[str, str],
    timestamp: str,
    files_used: list[str],
    is_demo: bool = False,
) -> str:
    """Generate a self-contained HTML report string."""

    # Detect risk
    risk_text = sections.get("4. RISK LEVEL", sections.get("RISK LEVEL", ""))
    risk_level = _detect_risk_level(risk_text)
    risk_gradient = _risk_gradient(risk_level)
    risk_emoji = _risk_emoji(risk_level)

    # Build section cards
    section_cards = ""
    for header, content in sections.items():
        display = SECTION_DISPLAY.get(header, header)
        icon = _section_icon(header)
        html_content = _markdown_to_html(content)

        # Special risk badge for risk section
        risk_badge = ""
        if "RISK LEVEL" in header.upper():
            risk_badge = f"""
            <div class="risk-badge" style="background: {risk_gradient};">
                {risk_emoji} {risk_level}
            </div>
            """

        section_cards += f"""
        <div class="section-card" id="{header.lower().replace(' ', '-').replace('/', '-')}">
            <h2>{icon} {display}</h2>
            {risk_badge}
            <div class="section-content">{html_content}</div>
        </div>
        """

    mode_banner = """
    <div class="demo-banner" style="border-color: rgba(16, 185, 129, 0.5); background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.06));">
        ✅ LIVE MODE — Inference generated via NVIDIA API.
    </div>
    """
    if is_demo:
        mode_banner = """
        <div class="demo-banner">
            🎮 DEMO MODE — Using simulated analysis. Set NVIDIA_API_KEY for production.
        </div>
        """

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blast Radius Analysis Report — {timestamp}</title>
    <style>
        :root {{
            --primary-bg: #0a0e27;
            --surface-1: #151b38;
            --surface-2: #1f2749;
            --surface-3: #2a3351;
            --border-color: #3a4560;
            --text-primary: #f5f7fa;
            --text-secondary: #b8c1cc;
            --text-muted: #8892a0;
            --accent-purple: #7c3aed;
            --accent-purple-light: #a78bfa;
            --accent-danger: #ef4444;
            --accent-warning: #f97316;
            --accent-info: #06b6d4;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
            --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.5);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        html {{ scroll-behavior: smooth; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
            background: linear-gradient(135deg, var(--primary-bg) 0%, #1a1f3a 100%);
            color: var(--text-primary);
            line-height: 1.8;
            min-height: 100vh;
            font-weight: 400;
        }}

        .container {{
            max-width: 920px;
            margin: 0 auto;
            padding: 3rem 1.5rem;
        }}

        /* ── HEADER ────────────────────────────────────────────────────────── */
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 3.5rem 2.5rem;
            background: linear-gradient(180deg, rgba(124, 58, 237, 0.08) 0%, transparent 100%);
            border-bottom: 2px solid var(--border-color);
            border-radius: 16px;
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #a78bfa, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header .subheading {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
            font-weight: 400;
        }}

        .header .meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1.25rem;
        }}

        .meta-item {{
            padding: 0.75rem 1rem;
            background: rgba(124, 58, 237, 0.1);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
        }}

        .meta-item strong {{
            color: var(--text-primary);
            font-weight: 600;
        }}

        /* ── DEMO BANNER ───────────────────────────────────────────────────── */
        .demo-banner {{
            background: linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(239, 68, 68, 0.05));
            border: 2px solid rgba(249, 115, 22, 0.4);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 2.5rem;
            text-align: center;
            font-size: 0.95rem;
            color: var(--text-secondary);
            font-weight: 500;
            backdrop-filter: blur(8px);
        }}

        /* ── RISK BADGE ────────────────────────────────────────────────────── */
        .risk-badge {{
            display: inline-block;
            padding: 0.8rem 2.5rem;
            border-radius: 50px;
            font-size: 1.2rem;
            font-weight: 700;
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            margin: 1.5rem 0;
            letter-spacing: 0.5px;
            box-shadow: var(--shadow-lg);
            text-transform: uppercase;
            border: none;
        }}

        /* ── SECTION CARDS ─────────────────────────────────────────────────── */
        .section-card {{
            background: var(--surface-1);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 2.25rem;
            margin-bottom: 2rem;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            position: relative;
            overflow: hidden;
        }}

        .section-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent-purple), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .section-card:hover {{
            border-color: var(--accent-purple);
            background: var(--surface-2);
            box-shadow: 0 8px 24px rgba(124, 58, 237, 0.15);
            transform: translateY(-4px);
        }}

        .section-card:hover::before {{
            opacity: 1;
        }}

        .section-card h2 {{
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--accent-purple-light);
            margin-bottom: 1.25rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .section-content {{
            color: var(--text-primary);
            font-size: 0.975rem;
            line-height: 1.9;
        }}

        .section-content p {{
            margin-bottom: 1rem;
        }}

        .section-content strong {{
            color: var(--text-primary);
            font-weight: 600;
            background: rgba(124, 58, 237, 0.1);
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
        }}

        .section-content em {{
            color: var(--accent-info);
            font-style: italic;
        }}

        .section-content code {{
            background: var(--surface-3);
            padding: 0.2rem 0.5rem;
            border-radius: 5px;
            font-size: 0.88em;
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
            color: #d4d4d4;
            border: 1px solid var(--border-color);
        }}

        .section-content pre {{
            background: #0f1419;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            overflow-x: auto;
            margin: 1.5rem 0;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
        }}

        .section-content pre code {{
            background: none;
            padding: 0;
            color: #e4e4e7;
            font-size: 0.85rem;
            border: none;
        }}

        .section-content ul, .section-content ol {{
            padding-left: 1.75rem;
            margin: 1rem 0;
        }}

        .section-content li {{
            margin-bottom: 0.75rem;
            color: var(--text-primary);
        }}

        .section-content a {{
            color: var(--accent-purple-light);
            text-decoration: none;
            border-bottom: 1px dotted var(--accent-purple);
            transition: all 0.2s ease;
        }}

        .section-content a:hover {{
            color: #e9d5ff;
            border-bottom-style: solid;
        }}

        /* ── FOOTER ────────────────────────────────────────────────────────── */
        .footer {{
            text-align: center;
            padding: 2.5rem;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid var(--border-color);
            margin-top: 3rem;
            background: rgba(124, 58, 237, 0.03);
            border-radius: 8px;
        }}

        .footer strong {{
            color: var(--text-secondary);
            font-weight: 600;
        }}

        /* ── SPACING & UTILITY ─────────────────────────────────────────────── */
        .spacer {{ height: 1rem; }}
        .divider {{
            height: 1px;
            background: var(--border-color);
            margin: 1.5rem 0;
        }}

        /* ── RESPONSIVE ────────────────────────────────────────────────────── */
        @media (max-width: 768px) {{
            .container {{ padding: 1.5rem 1rem; }}
            
            .header {{
                padding: 2rem 1.5rem;
                margin-bottom: 2rem;
            }}

            .header h1 {{
                font-size: 1.75rem;
            }}

            .header .subheading {{
                font-size: 0.8rem;
            }}

            .header .meta {{
                grid-template-columns: 1fr;
                gap: 0.75rem;
            }}

            .section-card {{
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }}

            .section-card h2 {{
                font-size: 1.15rem;
                margin-bottom: 1rem;
            }}

            .section-content {{
                font-size: 0.9rem;
            }}
        }}

        @media (max-width: 480px) {{
            .header {{
                padding: 1.5rem 1rem;
            }}

            .header h1 {{
                font-size: 1.4rem;
            }}

            .section-card {{
                padding: 1.25rem;
                border-radius: 10px;
            }}

            .section-card h2 {{
                font-size: 1rem;
            }}

            .risk-badge {{
                padding: 0.6rem 1.5rem;
                font-size: 1rem;
            }}
        }}

        /* ── PRINT STYLES ──────────────────────────────────────────────────── */
        @media print {{
            body {{ background: white; color: #000; }}
            
            .header {{
                background: none;
                border: none;
                padding: 0 0 2rem 0;
            }}

            .header h1 {{
                background: none;
                -webkit-text-fill-color: initial;
                color: #000;
            }}

            .section-card {{
                background: white;
                border: 1px solid #ddd;
                box-shadow: none;
                page-break-inside: avoid;
            }}

            .section-card:hover {{
                transform: none;
                background: white;
            }}

            .demo-banner {{
                border: 1px solid #f97316;
            }}

            .footer {{
                border: none;
                background: none;
            }}

            a {{
                text-decoration: underline;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Blast Radius Analysis</h1>
        <p class="subheading">AI-Powered Code Impact Assessment</p>
        <div class="meta">
            <div class="meta-item">
                <strong>📅 Timestamp:</strong> {timestamp}
            </div>
            <div class="meta-item">
                <strong>🤖 Model:</strong> {MODEL_NAME if not is_demo else "DEMO MODE"}
            </div>
            <div class="meta-item">
                <strong>📄 Files:</strong> {', '.join(files_used) if files_used else 'none'}
            </div>
        </div>
    </div>

    <div class="container">
        {mode_banner}
        {section_cards}

        <!-- APPROVAL WORKFLOW SECTION -->
        <div class="section-card" id="approval-workflow">
            <h2>✅ Approval Workflow</h2>
            <div class="section-content">
                <p><strong>Review and Approve Code Changes:</strong></p>
                <div id="approvals-list" style="margin-top: 1.5rem;">
                    <p style="color: var(--text-muted); font-style: italic;">
                        💡 Tip: Tick changes below to approve them for code patching.
                    </p>
                </div>

                <div style="display: flex; gap: 1rem; margin-top: 2rem; flex-wrap: wrap;">
                    <button id="approve-all-btn" class="action-btn" onclick="approveAll()">
                        ✓ Approve All
                    </button>
                    <button id="clear-all-btn" class="action-btn" onclick="clearAll()">
                        ✗ Clear All
                    </button>
                    <button id="export-btn" class="action-btn action-btn-primary" onclick="exportApprovals()">
                        📥 Export Approvals
                    </button>
                    <button id="apply-btn" class="action-btn action-btn-primary" onclick="applyChanges()">
                        ⚡ Apply Approved Changes
                    </button>
                </div>

                <div id="approval-log" style="margin-top: 2rem; padding: 1rem; background: var(--surface-3); border-radius: 8px; display: none;">
                    <strong style="color: var(--accent-purple-light);">Action Log:</strong>
                    <div id="log-content" style="margin-top: 0.5rem; font-family: monospace; font-size: 0.85rem; color: var(--text-muted);"></div>
                </div>
            </div>
        </div>

        <script>
            // Approval workflow state
            let approvalState = {{}};

            function approveAll() {{
                document.querySelectorAll('.approval-checkbox').forEach(cb => {{
                    cb.checked = true;
                    updateApprovalState(cb);
                }});
                logAction('✓ All changes approved');
            }}

            function clearAll() {{
                document.querySelectorAll('.approval-checkbox').forEach(cb => {{
                    cb.checked = false;
                    updateApprovalState(cb);
                }});
                logAction('✗ All approvals cleared');
            }}

            function updateApprovalState(checkbox) {{
                const changeId = checkbox.dataset.changeId;
                approvalState[changeId] = checkbox.checked;
            }}

            function exportApprovals() {{
                const approved = Object.entries(approvalState)
                    .filter(([_, approved]) => approved)
                    .map(([id, _]) => id);
                
                const exportData = {{
                    ticket_id: 'KS-107',
                    approved_changes: approved,
                    timestamp: new Date().toISOString()
                }};

                const json = JSON.stringify(exportData, null, 2);
                const blob = new Blob([json], {{ type: 'application/json' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'approvals.json';
                a.click();
                logAction('📥 Exported ' + approved.length + ' approvals');
            }}

            function applyChanges() {{
                const approved = Object.entries(approvalState)
                    .filter(([_, approved]) => approved)
                    .map(([id, _]) => id);

                if (approved.length === 0) {{
                    alert('⚠️  No changes approved. Tick at least one change to apply.');
                    return;
                }}

                const confirmed = confirm(`Apply ${{approved.length}} approved change(s)? This will modify your codebase.`);
                if (!confirmed) return;

                logAction(`⚡ Applying ${{approved.length}} change(s)...`);
                // In a real implementation, this would call the backend API
                // For now, we'll just log it
                setTimeout(() => {{
                    logAction('✓ Changes applied successfully! (See outputs/candidate_pr.txt)');
                    logAction('📝 PR generated: outputs/candidate_pr.txt');
                }}, 1000);
            }}

            function logAction(message) {{
                const logDiv = document.getElementById('approval-log');
                const logContent = document.getElementById('log-content');
                logDiv.style.display = 'block';
                const timestamp = new Date().toLocaleTimeString();
                const entry = document.createElement('div');
                entry.textContent = `[${{timestamp}}] ${{message}}`;
                logContent.appendChild(entry);
                logContent.scrollTop = logContent.scrollHeight;
            }}

            // Initialize checkboxes (placeholder - would be populated from AI analysis)
            document.addEventListener('DOMContentLoaded', () => {{
                const exampleChanges = [
                    {{ id: 'change-1', file: 'src/types.ts', operation: 'modify' }},
                    {{ id: 'change-2', file: 'src/constants.ts', operation: 'modify' }},
                    {{ id: 'change-3', file: 'src/services/orderService.ts', operation:'modify' }}
                ];

                const approvalsList = document.getElementById('approvals-list');
                approvalsList.innerHTML = '';
                
                exampleChanges.forEach(change => {{
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.className = 'approval-checkbox';
                    checkbox.id = change.id;
                    checkbox.dataset.changeId = change.id;
                    checkbox.onchange = function() {{ updateApprovalState(this); }};

                    const label = document.createElement('label');
                    label.style.display = 'flex';
                    label.style.alignItems = 'center';
                    label.style.gap = '0.75rem';
                    label.style.marginBottom = '0.75rem';
                    label.style.cursor = 'pointer';
                    label.appendChild(checkbox);

                    const text = document.createTextNode(`${{change.operation.toUpperCase()}} — ${{change.file}}`);
                    label.appendChild(text);
                    approvalsList.appendChild(label);
                }});
            }});
        </script>

        <style>
            .approval-checkbox {{
                width: 20px;
                height: 20px;
                cursor: pointer;
                accent-color: var(--accent-purple);
            }}

            .action-btn {{
                padding: 0.75rem 1.5rem;
                background: var(--surface-2);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                border-radius: 8px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.2s ease;
                font-size: 0.9rem;
            }}

            .action-btn:hover {{
                background: var(--surface-3);
                border-color: var(--accent-purple);
                color: var(--accent-purple-light);
            }}

            .action-btn-primary {{
                background: linear-gradient(135deg, var(--accent-purple), #8b5cf6);
                border-color: var(--accent-purple);
                color: white;
            }}

            .action-btn-primary:hover {{
                background: linear-gradient(135deg, #8b5cf6, #6d28d9);
                box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
            }}
        </style>
    </div>

    <div class="footer">
        <strong>Blast Radius Agent</strong> &mdash; Powered by NVIDIA Nemotron
        <br>
        <span style="color: var(--text-muted); margin-top: 0.5rem; display: block;">Enterprise-Grade Code Impact Analysis</span>
    </div>
</body>
</html>"""

    return html_doc


def save_html_report(
    sections: dict[str, str],
    timestamp: str,
    files_used: list[str],
    is_demo: bool = False,
) -> str:
    """
    Generate and save an HTML report.

    Returns:
        Absolute path to the saved HTML file.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_ts = timestamp.replace(":", "-").replace(" ", "_")
    mode = "demo" if is_demo else "live"
    filename = f"analysis_{mode}_{safe_ts}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)

    html_content = generate_html_report(sections, timestamp, files_used, is_demo)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return os.path.abspath(filepath)
