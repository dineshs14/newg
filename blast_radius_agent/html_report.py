"""
Blast Radius Agent — HTML Report Generator
=============================================
Creates a beautiful, self-contained HTML report that auto-opens
in the default browser. Works on Windows, Mac, and Linux.
"""

import os
import re
import html
import json
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


def _extract_structured_suggestions(suggested_fix_text: str) -> list[dict[str, str]]:
    """
    Parse structured suggestions from section 5.

    Expected format per item:
      1. Title
         File: `path/to/file`
         Action: replace
         ```find
         old snippet
         ```
         ```replace
         new snippet
         ```
    """
    pattern = re.compile(
        r"(?ms)^\s*\d+\.\s*(.*?)\n"
        r"\s*File:\s*`?([^`\n]+)`?\s*\n"
        r"\s*Action:\s*(replace)\s*\n"
        r"\s*```find\n(.*?)\n```\s*\n"
        r"\s*```replace\n(.*?)\n```",
    )

    suggestions: list[dict[str, str]] = []
    for idx, match in enumerate(pattern.finditer(suggested_fix_text), start=1):
        title, file_path, action, find_text, replace_text = match.groups()
        normalized_path = file_path.strip().replace("\\", "/")
        suggestions.append(
            {
                "id": f"S{idx}",
                "title": title.strip(),
                "file": normalized_path,
                "action": action.strip().lower(),
                "find": find_text,
                "replace": replace_text,
            }
        )

    return suggestions


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

    suggestions = _extract_structured_suggestions(
        sections.get("5. SUGGESTED FIX / MITIGATION", "")
    )
    suggestions_json = json.dumps(suggestions).replace("</", "<\\/")

    suggestion_panel = ""
    if suggestions:
        suggestion_items = []
        for s in suggestions:
            suggestion_items.append(
                f"""
                <label class="suggestion-item">
                    <input type="checkbox" class="suggestion-check" data-id="{html.escape(s['id'])}" checked>
                    <div class="suggestion-meta">
                        <div class="suggestion-title">{html.escape(s['id'])}: {html.escape(s['title'])}</div>
                        <div class="suggestion-file">File: {html.escape(s['file'])}</div>
                    </div>
                </label>
                """
            )

        suggestion_panel = f"""
        <div class="section-card action-panel">
            <h2>🛠 Apply Suggested Fixes</h2>
            <p class="action-help">
                Select suggestions to apply into your project folder. Unselected suggestions will be saved into a text file.
            </p>
            <div id="browser-capability" class="capability-note"></div>
            <div class="action-buttons">
                <button id="choose-folder-btn" type="button">Choose Project Folder</button>
                <button id="apply-btn" type="button">Apply Selected + Save Unselected</button>
                <button id="download-plan-btn" type="button">Download Selection Plan</button>
            </div>
            <div id="selected-folder" class="selected-folder">No project folder selected.</div>
            <div class="suggestion-list">
                {''.join(suggestion_items)}
            </div>
            <pre id="action-log" class="action-log"></pre>
        </div>
        """
    else:
        suggestion_panel = """
        <div class="section-card action-panel">
            <h2>🛠 Apply Suggested Fixes</h2>
            <p class="action-help">
                No structured suggestions were detected. Ask the AI to output section 5 using File/Action/find/replace blocks.
            </p>
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

        .action-panel {{
            border-color: #3e4f85;
            background: linear-gradient(180deg, #1b2038, #171c31);
        }}

        .action-help {{
            color: var(--text-dim);
            margin-bottom: 1rem;
        }}

        .action-buttons {{
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-bottom: 0.75rem;
        }}

        .action-buttons button {{
            background: #2c3e73;
            color: #f2f4ff;
            border: 1px solid #5168b2;
            border-radius: 8px;
            padding: 0.6rem 0.9rem;
            font-weight: 600;
            cursor: pointer;
        }}

        .action-buttons button:hover {{
            background: #35509a;
        }}

        .selected-folder {{
            color: #b8c4f2;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}

        .capability-note {{
            color: #ffd9a0;
            font-size: 0.85rem;
            margin-bottom: 0.8rem;
        }}

        .suggestion-list {{
            display: grid;
            gap: 0.65rem;
            margin-bottom: 1rem;
        }}

        .suggestion-item {{
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 0.75rem;
            align-items: start;
            border: 1px solid #38466f;
            border-radius: 10px;
            padding: 0.7rem;
            background: #1a2544;
        }}

        .suggestion-check {{
            margin-top: 0.2rem;
        }}

        .suggestion-title {{
            color: #eef2ff;
            font-weight: 600;
        }}

        .suggestion-file {{
            color: #b3bfe7;
            font-size: 0.85rem;
            margin-top: 0.2rem;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
        }}

        .action-log {{
            background: #0f162e;
            border: 1px solid #354371;
            border-radius: 8px;
            min-height: 140px;
            padding: 0.75rem;
            color: #dce5ff;
            font-size: 0.85rem;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
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
        {suggestion_panel}
        {section_cards}
    </div>

    <div class="footer">
        Generated by Blast Radius Agent &mdash; Powered by NVIDIA Nemotron
    </div>

    <script>
        const suggestions = {suggestions_json};
        let projectDirHandle = null;

        const logEl = document.getElementById('action-log');
        const folderLabel = document.getElementById('selected-folder');
        const capabilityEl = document.getElementById('browser-capability');
        const chooseBtn = document.getElementById('choose-folder-btn');
        const applyBtn = document.getElementById('apply-btn');
        const downloadPlanBtn = document.getElementById('download-plan-btn');
        const hasFolderAccessApi = Boolean(window.isSecureContext && window.showDirectoryPicker);

        function log(message) {{
            if (!logEl) return;
            const time = new Date().toLocaleTimeString();
            logEl.textContent += `[${{time}}] ${{message}}\n`;
            logEl.scrollTop = logEl.scrollHeight;
        }}

        function getCheckedSuggestionIds() {{
            const checks = document.querySelectorAll('.suggestion-check');
            const ids = [];
            checks.forEach((c) => {{
                if (c.checked) ids.push(c.dataset.id);
            }});
            return ids;
        }}

        function downloadTextFile(filename, content) {{
            const blob = new Blob([content], {{ type: 'text/plain;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        }}

        function buildSelectionPlan() {{
            const selectedIds = new Set(getCheckedSuggestionIds());
            const selected = suggestions.filter((s) => selectedIds.has(s.id));
            const unselected = suggestions.filter((s) => !selectedIds.has(s.id));

            const lines = [];
            lines.push('BLAST RADIUS SELECTION PLAN');
            lines.push(`Generated: ${{new Date().toISOString()}}`);
            lines.push('');
            lines.push(`Selected: ${{selected.length}}`);
            lines.push(`Unselected: ${{unselected.length}}`);
            lines.push('');
            lines.push('SELECTED SUGGESTIONS');
            lines.push('--------------------');
            if (!selected.length) {{
                lines.push('None');
            }} else {{
                selected.forEach((s) => {{
                    lines.push(`${{s.id}} | ${{s.title}}`);
                    lines.push(`File: ${{s.file}}`);
                    lines.push(`Action: ${{s.action}}`);
                    lines.push('find:');
                    lines.push(s.find);
                    lines.push('replace:');
                    lines.push(s.replace);
                    lines.push('');
                }});
            }}

            lines.push('UNSELECTED SUGGESTIONS');
            lines.push('----------------------');
            if (!unselected.length) {{
                lines.push('None');
            }} else {{
                unselected.forEach((s) => {{
                    lines.push(`${{s.id}} | ${{s.title}}`);
                    lines.push(`File: ${{s.file}}`);
                    lines.push(`Action: ${{s.action}}`);
                    lines.push('');
                }});
            }}

            return lines.join('\\n');
        }}

        function downloadSelectionPlan() {{
            if (!suggestions.length) {{
                log('No structured suggestions available to export.');
                return;
            }}

            const ts = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `blast_radius_selection_plan_${{ts}}.txt`;
            const content = buildSelectionPlan();
            downloadTextFile(filename, content);
            log(`Selection plan downloaded: ${{filename}}`);
        }}

        async function chooseProjectFolder() {{
            if (!hasFolderAccessApi) {{
                alert('Direct folder write is unavailable in this browser/context. Use Download Selection Plan instead.');
                return;
            }}
            try {{
                projectDirHandle = await window.showDirectoryPicker();
                if (folderLabel) folderLabel.textContent = `Selected project folder: ${{projectDirHandle.name}}`;
                log(`Project folder selected: ${{projectDirHandle.name}}`);
            }} catch (err) {{
                log(`Folder selection cancelled: ${{err.message}}`);
            }}
        }}

        async function getFileHandleFromPath(rootHandle, path, create) {{
            const clean = path
                .replaceAll('\\\\', '/')
                .replace(/^\/+/, '');
            const parts = clean.split('/').filter(Boolean);
            if (parts.length === 0) throw new Error('Invalid file path.');

            let dir = rootHandle;
            for (let i = 0; i < parts.length - 1; i++) {{
                dir = await dir.getDirectoryHandle(parts[i], {{ create }});
            }}
            return await dir.getFileHandle(parts[parts.length - 1], {{ create }});
        }}

        async function readTextFile(fileHandle) {{
            const file = await fileHandle.getFile();
            return await file.text();
        }}

        async function writeTextFile(fileHandle, content) {{
            const writable = await fileHandle.createWritable();
            await writable.write(content);
            await writable.close();
        }}

        async function applySelectedSuggestions() {{
            if (!hasFolderAccessApi) {{
                log('Folder write API unavailable. Use Download Selection Plan for manual application.');
                downloadSelectionPlan();
                return;
            }}

            if (!projectDirHandle) {{
                alert('Choose the project folder first.');
                return;
            }}
            if (!suggestions.length) {{
                log('No structured suggestions available.');
                return;
            }}

            const selectedIds = new Set(getCheckedSuggestionIds());
            const selected = suggestions.filter((s) => selectedIds.has(s.id));
            const unselected = suggestions.filter((s) => !selectedIds.has(s.id));

            if (selected.length === 0) {{
                log('No suggestions selected; only unselected summary file will be written.');
            }} else {{
                log(`Applying ${{selected.length}} suggestion(s)...`);
            }}

            for (const s of selected) {{
                try {{
                    if (s.action !== 'replace') {{
                        log(`${{s.id}} skipped: unsupported action '${{s.action}}'.`);
                        continue;
                    }}

                    const handle = await getFileHandleFromPath(projectDirHandle, s.file, false);
                    const current = await readTextFile(handle);

                    if (!current.includes(s.find)) {{
                        log(`${{s.id}} failed: find block not found in ${{s.file}}.`);
                        continue;
                    }}

                    const updated = current.replace(s.find, s.replace);
                    await writeTextFile(handle, updated);
                    log(`${{s.id}} applied to ${{s.file}}.`);
                }} catch (err) {{
                    log(`${{s.id}} failed on ${{s.file}}: ${{err.message}}`);
                }}
            }}

            try {{
                const ts = new Date().toISOString().replace(/[:.]/g, '-');
                const filename = `blast_radius_unselected_${{ts}}.txt`;
                const handle = await getFileHandleFromPath(projectDirHandle, filename, true);

                const lines = [];
                lines.push('UNSELECTED SUGGESTIONS');
                lines.push('Generated from Blast Radius report');
                lines.push('');

                if (!unselected.length) {{
                    lines.push('None. All suggestions were selected and processed.');
                }} else {{
                    unselected.forEach((s) => {{
                        lines.push(`${{s.id}} | ${{s.title}}`);
                        lines.push(`File: ${{s.file}}`);
                        lines.push(`Action: ${{s.action}}`);
                        lines.push('---');
                    }});
                }}

                await writeTextFile(handle, lines.join('\\n'));
                log(`Unselected suggestions written to ${{filename}}.`);
            }} catch (err) {{
                log(`Failed to write unselected suggestions file: ${{err.message}}`);
            }}

            log('Done.');
        }}

        if (capabilityEl) {{
            if (hasFolderAccessApi) {{
                capabilityEl.textContent = 'Live apply is available in this browser.';
            }} else {{
                capabilityEl.textContent = 'Live apply is disabled for local file pages in this browser. Use Download Selection Plan.';
                if (chooseBtn) chooseBtn.disabled = true;
                if (applyBtn) applyBtn.disabled = true;
            }}
        }}

        if (chooseBtn) chooseBtn.addEventListener('click', chooseProjectFolder);
        if (applyBtn) applyBtn.addEventListener('click', applySelectedSuggestions);
        if (downloadPlanBtn) downloadPlanBtn.addEventListener('click', downloadSelectionPlan);
    </script>
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
