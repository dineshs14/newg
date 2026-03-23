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

    demo_banner = ""
    if is_demo:
        demo_banner = """
        <div class="demo-banner">
            🎮 DEMO MODE — This is a simulated analysis using mock data.
            Set your NVIDIA_API_KEY for real analysis.
        </div>
        """

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blast Radius Report — {timestamp}</title>
    <style>
        :root {{
            --bg: #0f0f17;
            --surface: #1a1a2e;
            --surface2: #222240;
            --border: #2d2d5e;
            --text: #e0e0f0;
            --text-dim: #8888aa;
            --accent: #7c5cfc;
            --accent-light: #9d85fd;
            --glow: rgba(124, 92, 252, 0.15);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            min-height: 100vh;
        }}

        .container {{
            max-width: 880px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 3rem 2rem;
            background: linear-gradient(180deg, var(--surface) 0%, var(--bg) 100%);
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }}

        .header h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-light), #e0c3fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}

        .header .meta {{
            color: var(--text-dim);
            font-size: 0.85rem;
        }}

        .header .meta span {{
            margin: 0 0.75rem;
        }}

        /* Demo Banner */
        .demo-banner {{
            background: linear-gradient(135deg, #1a1a3e, #2d1a4e);
            border: 1px solid #7c5cfc44;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            text-align: center;
            font-size: 0.9rem;
            color: var(--accent-light);
            margin-bottom: 2rem;
        }}

        /* Risk Badge */
        .risk-badge {{
            display: inline-block;
            padding: 0.6rem 2rem;
            border-radius: 50px;
            font-size: 1.4rem;
            font-weight: 800;
            color: white;
            text-shadow: 0 1px 3px rgba(0,0,0,0.4);
            margin: 1rem 0;
            letter-spacing: 2px;
        }}

        /* Section Cards */
        .section-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: all 0.2s ease;
            position: relative;
        }}

        .section-card:hover {{
            border-color: var(--accent);
            box-shadow: 0 0 30px var(--glow);
            transform: translateY(-2px);
        }}

        .section-card h2 {{
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--accent-light);
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border);
        }}

        .section-content {{
            color: var(--text);
            font-size: 0.95rem;
        }}

        .section-content p {{
            margin-bottom: 0.75rem;
        }}

        .section-content strong {{
            color: #fff;
        }}

        .section-content code {{
            background: var(--surface2);
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            font-size: 0.88em;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            color: var(--accent-light);
        }}

        .section-content pre {{
            background: #0d0d1a;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.25rem;
            overflow-x: auto;
            margin: 1rem 0;
        }}

        .section-content pre code {{
            background: none;
            padding: 0;
            color: #b8b8d0;
            font-size: 0.85rem;
        }}

        .section-content ul, .section-content ol {{
            padding-left: 1.5rem;
            margin: 0.75rem 0;
        }}

        .section-content li {{
            margin-bottom: 0.5rem;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-dim);
            font-size: 0.8rem;
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }}

        /* Responsive */
        @media (max-width: 640px) {{
            .container {{ padding: 1rem; }}
            .header {{ padding: 2rem 1rem; }}
            .header h1 {{ font-size: 1.5rem; }}
            .section-card {{ padding: 1.25rem; }}
        }}

        /* Print styles */
        @media print {{
            body {{ background: white; color: black; }}
            .section-card {{ border: 1px solid #ddd; box-shadow: none; }}
            .section-card:hover {{ transform: none; }}
            .demo-banner {{ border: 1px solid #7c5cfc; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 Blast Radius Analysis</h1>
        <div class="meta">
            <span>📅 {timestamp}</span>
            <span>🤖 {MODEL_NAME if not is_demo else "DEMO MODE"}</span>
            <span>📄 {', '.join(files_used) if files_used else 'none'}</span>
        </div>
    </div>

    <div class="container">
        {demo_banner}
        {section_cards}
    </div>

    <div class="footer">
        Generated by Blast Radius Agent &mdash; Powered by NVIDIA Nemotron
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
    filename = f"analysis_{safe_ts}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)

    html_content = generate_html_report(sections, timestamp, files_used, is_demo)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return os.path.abspath(filepath)
