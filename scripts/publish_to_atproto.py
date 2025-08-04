#!/usr/bin/env python3
"""
⟨⟨ AT PROTOCOL PUBLISHER ⟩⟩
Publishes spinglasscore articles to the AT Protocol network via WhiteWind
"""
import os
import re
import html
import argparse
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Templates for announcements
ANNOUNCEMENT_TEMPLATES = {
    "default": """⟨⟨ NEW SPINGL∆SS NODE ⟩⟩

{title}

"{excerpt}"

→ {url}""",
    # ... (other templates unchanged) ...
    "network_state": """CONSENSUS.BROADCAST()
node: {title}
stake: {word_count} words
validators: pending
{url}"""
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
        resp = self.client.login(handle, password)
        print(f"→ Logged in as DID: {resp.did}")

    def extract_article_metadata(self, html_path: str) -> Dict:
        """Extract title, excerpt, flags, and phase from HTML file"""
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        title = title_match.group(1) if title_match else "Untitled"
        title = re.sub(r'[⟨⟩]', '', title).strip()
        p_match = re.search(r'<p>([^<]+)</p>', content)
        excerpt = p_match.group(1) if p_match else ""
        excerpt = html.unescape(excerpt)
        if len(excerpt) > 300:
            excerpt = excerpt[:300] + "..."
        has_glitch = bool(re.search(r'class="glitch"', content))
        has_math   = bool(re.search(r'class="math-corrupt"', content))
        lower_path = html_path.lower()
        if "phaseα" in lower_path or "phasea" in lower_path:
            phase = "phaseα"
        elif "phaseβ" in lower_path or "phaseb" in lower_path:
            phase = "phaseβ"
        elif "phaseγ" in lower_path or "phaseg" in lower_path:
            phase = "phaseγ"
        else:
            phase = "unknown"
        return {"title": title, "excerpt": excerpt,
                "has_glitch": has_glitch, "has_math": has_math,
                "phase": phase}

    def html_to_markdown(self, html_path: str) -> str:
        """Convert spinglasscore HTML to AT Protocol–compatible Markdown"""
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # ... conversion logic unchanged ...
        # For brevity, assume the conversion implementation is identical
        return content.strip()

    def publish_article(self, html_path: str) -> Optional[str]:
        """Publish a single HTML article via AT Protocol"""
        print(f"→ Publishing file: {html_path}")
        metadata = self.extract_article_metadata(html_path)
        record = {
            "$type": "com.whitewind.blog.entry",
            "title": metadata["title"],
            "content": self.html_to_markdown(html_path),
            "createdAt": datetime.now().isoformat() + "Z",
            "theme": "dark",
            "tags": ([metadata["phase"]] +
                     (["glitch"] if metadata["has_glitch"] else []) +
                     (["mathematics"] if metadata["has_math"] else []))[:5]
        }
        try:
            resp = self.client.com.atproto.repo.create_record(
                data=models.ComAtprotoRepoCreateRecord.Data(
                    repo=self.client.me.did,
                    collection="com.whitewind.blog.entry",
                    record=record
                )
            )
            print(f"   ✓ Success URI={resp.uri}")
            return resp.uri
        except Exception as e:
            print(f"✗ Failed to publish {html_path}: {e}")
            return None

    def publish_index_post(self, new_articles: list) -> Optional[str]:
        """Announce multiple new articles in a single index post"""
        if not new_articles:
            return None
        title = f"⟨⟨SPINGL∆SS UPDATE⟩⟩ {len(new_articles)} new nodes"
        content = "\n\n".join(
            f"◈ **{self.extract_article_metadata(a)['title']}**" for a in new_articles
        )
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
                data=models.ComAtprotoRepoCreateRecord.Data(
                    repo=self.client.me.did,
                    collection="com.whitewind.blog.entry",
                    record=record
                )
            )
            print(f"✓ Published index post: {title}")
            return resp.uri
        except Exception as e:
            print(f"✗ Failed to publish index post: {e}")
            return None

def find_new_articles(last_run_file: str = ".atproto_last_run") -> list:
    """Return list of HTML files newer than last recorded run"""
    last_run = float(open(last_run_file).read()) if os.path.exists(last_run_file) else 0.0
    new = [str(p) for p in Path(".").rglob("phase*/*.html") if p.stat().st_mtime > last_run]
    with open(last_run_file, 'w') as f:
        f.write(str(datetime.now().timestamp()))
    return new


def main():
    parser = argparse.ArgumentParser(
        description="Publish spinglasscore to AT Protocol"
    )
    parser.add_argument("--announce-template",
                        choices=["default","minimal","glitch","mathematical",
                                 "cryptic","network_state","auto"],
                        default="default",
                        help="Template for announcement posts")
    parser.add_argument("--handle", required=True, help="AT Protocol handle")
    parser.add_argument("--password", required=True, help="AT Protocol password")
    parser.add_argument("--all", action="store_true", help="Publish all articles")
    parser.add_argument("--file", help="Publish a single HTML file")
    parser.add_argument("--new-only", action="store_true",
                        help="Publish only files newer than last run")
    args = parser.parse_args()

    publisher = SpinglassATProto(args.handle, args.password)

    if args.file:
        publisher.publish_article(args.file)

    elif args.all:
        # DEBUG: list files to publish
        html_files = [str(p) for p in Path(".").rglob("phase*/*.html")]
        print(f"→ Found {len(html_files)} HTML file(s) to publish:")
        for f in html_files:
            print(f"   • {f}")
        for f in html_files:
            publisher.publish_article(f)

    elif args.new_only:
        new = find_new_articles()
        if new:
            for p in new:
                publisher.publish_article(p)
            publisher.publish_index_post(new)
        else:
            print("No new articles found")
    else:
        print("Specify --all, --new-only, or --file")

if __name__ == "__main__":
    main()
