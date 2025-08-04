#!/usr/bin/env python3
"""
⟨⟨ AT PROTOCOL PUBLISHER ⟩⟩
Publishes spinglasscore articles to the AT Protocol network via Whitewind
"""
import os
import re
import json
import html
import argparse
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Section for customizable announcements
ANNOUNCEMENT_TEMPLATES = {
    "default": """⟨⟨ NEW SPINGL∆SS NODE ⟩⟩

{title}

"{excerpt}"

→ {url}""",
    "minimal": """new node: {title}
{url}""",
    "phase_specific": {
        "phaseα": """⟨⟨ PH∆SE Α EMISSION ⟩⟩
{title}
"{excerpt}"
∂S/∂t → ∞
{url}""",
        "phaseβ": """⟨⟨ PH∆SE β CRYSTALLIZATION ⟩⟩
{title}
spin glass transition detected
{url}""",
        "phaseγ": """⟨⟨ PH∆SE γ RADIATION ⟩⟩
{title}
topology: {topology_status}
{url}"""
    },
    "glitch": """g̸l̸i̸t̸c̸h̸ ̸d̸e̸t̸e̸c̸t̸e̸d̸
{title}
sys.tem.mal//function
{url}""",
    "mathematical": """∂[NEW]/∂t = {title}
∫∫∫ {excerpt} dx dy dz
lim(t→∞) = {url}""",
    "cryptic": """◈◈◈◈◈◈◈◈◈◈◈◈
{encoded_title}
◈◈◈◈◈◈◈◈◈◈◈◈
{url}""",
    "network_state": """CONSENSUS.BROADCAST()
node: {title}
stake: {word_count} words
validators: pending
{url}"""
}

def create_announcement_post(self,
                             title: str,
                             excerpt: str,
                             article_url: str,
                             blog_uri: str,
                             metadata: Dict,
                             template: str = "default") -> Dict:
    """Create a Bluesky post with customizable templates"""
    # Auto‐select logic
    if template == "auto":
        if metadata.get("has_glitch"):
            template = "glitch"
        elif metadata.get("has_math"):
            template = "mathematical"
        elif metadata.get("phase") in ANNOUNCEMENT_TEMPLATES.get("phase_specific", {}):
            template_text = ANNOUNCEMENT_TEMPLATES["phase_specific"][metadata["phase"]]
        else:
            template = "default"

    # Choose template text
    if template in ANNOUNCEMENT_TEMPLATES:
        template_text = ANNOUNCEMENT_TEMPLATES[template]
    else:
        template_text = ANNOUNCEMENT_TEMPLATES["default"]

    # Helpers for formatting
    word_count = len(metadata.get("content", "").split())
    encoded_title = "".join([chr(ord(c) + 1) for c in title[:20]])
    topology_status = "WARPED" if metadata.get("has_glitch") else "STABLE"

    # Build announcement
    announcement = template_text.format(
        title=title,
        excerpt=(excerpt[:100] + "...") if len(excerpt) > 100 else excerpt,
        url=article_url,
        phase=metadata.get("phase", "unknown"),
        word_count=word_count,
        encoded_title=encoded_title,
        topology_status=topology_status
    )

    # Enforce 300-char limit
    if len(announcement) > 300:
        announcement = ANNOUNCEMENT_TEMPLATES["minimal"].format(
            title=(title[:50] + "...") if len(title) > 50 else title,
            url=article_url
        )

    return {
        "$type": "app.bsky.feed.post",
        "text": announcement,
        "createdAt": datetime.now().isoformat() + "Z",
        "langs": ["en"]
    }

try:
    from atproto import Client, models
except ImportError:
    print("ERROR: atproto library not installed")
    print("Install with: pip install atproto")
    exit(1)

class SpinglassATProto:
    """Bridges spinglasscore HTML articles to AT Protocol"""

    def __init__(self, handle: str, password: str):
        self.client = Client()
        self.client.login(handle, password)

    def extract_article_metadata(self, html_path: str) -> Dict:
        """Extract metadata from spinglasscore HTML"""
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Title
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        title = title_match.group(1) if title_match else "Untitled"
        title = re.sub(r'[⟨⟩]', '', title).strip()

        # Excerpt
        p_match = re.search(r'<p>([^<]+)</p>', content)
        excerpt = p_match.group(1) if p_match else ""
        excerpt = html.unescape(excerpt)
        if len(excerpt) > 300:
            excerpt = excerpt[:300] + "..."

        # Sections, flags, phase
        sections = re.findall(r'<h2>([^<]+)</h2>', content)
        has_glitch = bool(re.search(r'class="glitch"', content))
        has_math = bool(re.search(r'class="math-corrupt"', content))
        phase = "unknown"
        lower = html_path.lower()
        if "phaseα" in html_path or "phasea" in lower:
            phase = "phaseα"
        elif "phaseβ" in html_path or "phaseb" in lower:
            phase = "phaseβ"
        elif "phaseγ" in html_path or "phaseg" in lower:
            phase = "phaseγ"

        return {
            "title": title,
            "excerpt": excerpt,
            "sections": sections,
            "phase": phase,
            "has_glitch": has_glitch,
            "has_math": has_math,
            "file_path": html_path,
            "filename": os.path.basename(html_path)
        }

    def html_to_markdown(self, html_path: str) -> str:
        """Convert spinglasscore HTML to markdown"""
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Strip <body> wrapper
        body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
        if body_match:
            content = body_match.group(1)

        # Remove scanlines
        content = re.sub(r'<div class="scanlines"[^>]*>.*?</div>', '',
                         content, flags=re.DOTALL)

        # Headings
        content = re.sub(r'<h1[^>]*>([^<]+)</h1>', r'# \1\n', content)
        content = re.sub(r'<h2[^>]*>([^<]+)</h2>', r'\n## \1\n',
                         content)

        # Paragraphs
        content = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n',
                         content, flags=re.DOTALL)

        # Emphasis
        content = re.sub(r'<em>(.*?)</em>', r'*\1*', content)

        # Glitch/math spans
        content = re.sub(r'<span class="glitch">([^<]+)</span>',
                         r'⟨\1⟩', content)
        content = re.sub(r'<span class="math-corrupt">([^<]+)</span>',
                         r'∂[\1]∂', content)

        # Code blocks
        content = re.sub(r'<pre><code>(.*?)</code></pre>',
                         r'\n```\n\1\n```\n', content,
                         flags=re.DOTALL)
        content = re.sub(r'<code>(.*?)</code>', r'`\1`', content)

        # Lists
        content = re.sub(r'<ul[^>]*>(.*?)</ul>',
                         self._convert_list, content, flags=re.DOTALL)

        # Strip any remaining HTML
        content = re.sub(r'<[^>]+>', '', content)

        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        # Footer
        content += "\n\n---\n\n*Originally published at [spin.pyokosmeme.group]"
        content += "(https://spin.pyokosmeme.group)*"
        content += "\n\n⟨⟨ ∂S/∂t → ∞ ⟩⟩"
        return content.strip()

    def _convert_list(self, match):
        items = re.findall(r'<li[^>]*>(.*?)</li>',
                           match.group(1), re.DOTALL)
        return '\n' + '\n'.join(f'- {item.strip()}'
                                for item in items) + '\n'

    def create_blog_post(self, html_path: str) -> Dict:
        """Create AT Protocol blog post from HTML article"""
        metadata = self.extract_article_metadata(html_path)
        markdown_content = self.html_to_markdown(html_path)

        record = {
            "$type": "com.whitewind.blog.entry",
            "title": metadata["title"],
            "content": markdown_content,
            "createdAt": datetime.now().isoformat() + "Z",
            "theme": "dark",
            "tags": []
        }

        # Tag logic
        tags = [metadata["phase"]]
        if metadata["has_glitch"]:
            tags.append("glitch")
        if metadata["has_math"]:
            tags.append("mathematics")
        lower = markdown_content.lower()
        if "network" in lower:
            tags.append("network-state")
        if "outside" in lower:
            tags.append("outsideness")
        if "spin" in lower and "glass" in lower:
            tags.append("spin-glass")
        if "rhizome" in lower:
            tags.append("rhizome")
        record["tags"] = tags[:5]

        return record

    def publish_article(self, html_path: str) -> Optional[str]:
        """Publish a single article and return its URI"""
        try:
            record = self.create_blog_post(html_path)
            resp = self.client.com.atproto.repo.create_record(
                repo=self.client.me.did,
                collection="com.whitewind.blog.entry",
                record=record
            )
            uri = resp.uri
            print(f"✓ Published: {record['title']}")
            print(f"  URI: {uri}")
            print(f"  Tags: {', '.join(record['tags'])}")
            return uri
        except Exception as e:
            print(f"✗ Failed to publish {html_path}: {e}")
            return None

    def publish_index_post(self, new_articles: list) -> Optional[str]:
        """Announce new articles as an index post"""
        if not new_articles:
            return None

        title = f"⟨⟨SPINGL∆SS UPDATE⟩⟩ {len(new_articles)} new nodes"
        content = (f"The archive expands. {len(new_articles)} new documents "
                   "detected.\n\n")
        for article in new_articles:
            m = self.extract_article_metadata(article)
            content += f"◈ **{m['title']}** ({m['phase']})\n"
            content += f"  {m['excerpt']}\n\n"
        content += ("Access the full archive at [spin.pyokosmeme.group]"
                    "(https://spin.pyokosmeme.group)\n\n")
        content += "⟨⟨ the network remembers what the archive forgets ⟩⟩"

        record = {
            "$type": "com.whitewind.blog.entry",
            "title": title,
            "content": content,
            "createdAt": datetime.now().isoformat() + "Z",
            "theme": "dark",
            "tags": ["spinglasscore", "update", "archive"]
        }

        try:
            resp = self.client.com.atproto.repo.create_record(
                repo=self.client.me.did,
                collection="com.whitewind.blog.entry",
                record=record
            )
            print(f"✓ Published index post: {title}")
            return resp.uri
        except Exception as e:
            print(f"✗ Failed to publish index post: {e}")
            return None

def find_new_articles(last_run_file: str = ".atproto_last_run") -> list:
    """Identify HTML files newer than the timestamp recorded."""
    last_run = 0.0
    if os.path.exists(last_run_file):
        with open(last_run_file, 'r') as f:
            last_run = float(f.read().strip())

    new = []
    for phase_dir in Path(".").glob("phase*/"):
        for html_file in phase_dir.glob("*.html"):
            if html_file.stat().st_mtime > last_run:
                new.append(str(html_file))

    # Update timestamp immediately
    with open(last_run_file, 'w') as f:
        f.write(str(datetime.now().timestamp()))
    return new

def main():
    parser = argparse.ArgumentParser(
        description="Publish spinglasscore to AT Protocol"
    )
    parser.add_argument(
        "--announce-template",
        choices=[
            "default", "minimal", "glitch", "mathematical",
            "cryptic", "network_state", "auto"
        ],
        default="default",
        help="Template for Bluesky announcement posts"
    )
    parser.add_argument("--handle", required=True,
                        help="AT Protocol handle")
    parser.add_argument("--password", required=True,
                        help="AT Protocol password")
    parser.add_argument("--all", action="store_true",
                        help="Publish every article in the repo")
    parser.add_argument("--file",
                        help="Publish a single specified HTML file")
    parser.add_argument("--new-only", action="store_true",
                        help="Publish only files newer than last run")

    args = parser.parse_args()

    publisher = SpinglassATProto(args.handle, args.password)

    if args.file:
        publisher.publish_article(args.file)

    elif args.all:
        for phase_dir in Path(".").glob("phase*/"):
            for html_file in phase_dir.glob("*.html"):
                publisher.publish_article(str(html_file))

    elif args.new_only:
        new = find_new_articles()
        if new:
            print(f"Found {len(new)} new articles")
            for a in new:
                publisher.publish_article(a)
            publisher.publish_index_post(new)
        else:
            print("No new articles found")

    else:
        print("Specify --all, --new-only, or --file")

if __name__ == "__main__":
    main()
