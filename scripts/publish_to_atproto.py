#!/usr/bin/env python3
"""
⟨⟨ AT PROTOCOL PUBLISHER ⟩⟩
Publishes spinglasscore articles to the AT Protocol network via WhiteWind and broadcasts on Bluesky
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
    # Other templates omitted for brevity
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
    """Bridges spinglasscore HTML articles to AT Protocol and Bluesky"""

    def __init__(self, handle: str, password: str):
        self.client = Client()
        resp = self.client.login(handle, password)
        print(f"→ Logged in as DID: {resp.did}")

    def extract_article_metadata(self, html_path: str) -> Dict:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        title = (re.search(r'<h1[^>]*>([^<]+)</h1>', content) or [None, 'Untitled'])[1]
        title = re.sub(r'[⟨⟩]', '', title).strip()
        excerpt = (re.search(r'<p>([^<]+)</p>', content) or [None, ''])[1]
        excerpt = html.unescape(excerpt)
        if len(excerpt) > 300:
            excerpt = excerpt[:300] + '...'
        has_glitch = bool(re.search(r'class="glitch"', content))
        has_math   = bool(re.search(r'class="math-corrupt"', content))
        lower_path = html_path.lower()
        if 'phaseα' in lower_path or 'phasea' in lower_path:
            phase = 'phaseα'
        elif 'phaseβ' in lower_path or 'phaseb' in lower_path:
            phase = 'phaseβ'
        elif 'phaseγ' in lower_path or 'phaseg' in lower_path:
            phase = 'phaseγ'
        else:
            phase = 'unknown'
        return {'title': title, 'excerpt': excerpt,
                'has_glitch': has_glitch, 'has_math': has_math,
                'phase': phase}

    def html_to_markdown(self, html_path: str) -> str:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Conversion logic omitted for brevity
        return content.strip()

    def create_announcement_post(self,
                                 title: str,
                                 excerpt: str,
                                 article_url: str,
                                 metadata: Dict,
                                 template: str = "default") -> Dict:
        # Auto-pick template
        if template == 'auto':
            if metadata.get('has_glitch'):
                template = 'glitch'
            elif metadata.get('has_math'):
                template = 'mathematical'
            elif metadata.get('phase') in ANNOUNCEMENT_TEMPLATES:
                template = metadata['phase']
            else:
                template = 'default'
        tpl = ANNOUNCEMENT_TEMPLATES.get(template, ANNOUNCEMENT_TEMPLATES['default'])
        word_count = len(metadata.get('excerpt', '').split())
        text = tpl.format(title=title,
                          excerpt=excerpt,
                          url=article_url,
                          word_count=word_count)
        return {'$type': 'app.bsky.feed.post',
                'text': text,
                'createdAt': datetime.now().isoformat() + 'Z'}

    def publish_article(self, html_path: str) -> Optional[str]:
        print(f"→ Publishing file: {html_path}")
        metadata = self.extract_article_metadata(html_path)
        # 1) Publish blog post
        record = {
            '$type': 'com.whtwnd.blog.entry',  # corrected collection ID
            'title': metadata['title'],
            'content': self.html_to_markdown(html_path),
            'createdAt': datetime.now().isoformat() + 'Z',
            'theme': 'dark',
            'tags': ([metadata['phase']] +
                     (['glitch'] if metadata['has_glitch'] else []) +
                     (['mathematics'] if metadata['has_math'] else []))[:5]
        }
        try:
            resp = self.client.com.atproto.repo.create_record(
                data=models.ComAtprotoRepoCreateRecord.Data(
                    repo=self.client.me.did,
                    collection='com.whtwnd.blog.entry',
                    record=record
                ),
                validate=False  # skip local Lexicon validation
            )
            blog_uri = resp.uri
            print(f"   ✓ Blog post URI={blog_uri}")
        except Exception as e:
            print(f"✗ Failed to publish blog entry {html_path}: {e}")
            return None
        # 2) Publish announcement on Bluesky
        ann = self.create_announcement_post(
            title=metadata['title'],
            excerpt=metadata['excerpt'],
            article_url=blog_uri,
            metadata=metadata
        )
        try:
            resp2 = self.client.com.atproto.repo.create_record(
                data=models.ComAtprotoRepoCreateRecord.Data(
                    repo=self.client.me.did,
                    collection='app.bsky.feed.post',
                    record=ann
                ),
                validate=False  # skip local Lexicon validation
            )
            print(f"   ✓ Bluesky announcement URI={resp2.uri}")
        except Exception as e:
            print(f"✗ Failed to post announcement on Bluesky: {e}")
        return blog_uri

    def publish_index_post(self, new_articles: list) -> Optional[str]:
        if not new_articles:
            return None
        title = f"⟨⟨SPINGL∆SS UPDATE⟩⟩ {len(new_articles)} new nodes"
        content = '\n\n'.join(
            f"◈ **{self.extract_article_metadata(a)['title']}**" for a in new_articles
        )
        record = {
            '$type': 'com.whtwnd.blog.entry',  # corrected collection ID
            'title': title,
            'content': content,
            'createdAt': datetime.now().isoformat() + 'Z',
            'theme': 'dark',
            'tags': ['spinglasscore', 'update', 'archive']
        }
        try:
            resp = self.client.com.atproto.repo.create_record(
                data=models.ComAtprotoRepoCreateRecord.Data(
                    repo=self.client.me.did,
                    collection='com.whtwnd.blog.entry',
                    record=record
                ),
                validate=False  # skip local Lexicon validation
            )
            idx_uri = resp.uri
            print(f"✓ Index blog post URI={idx_uri}")
        except Exception as e:
            print(f"✗ Failed to publish index post: {e}")
            return None
        # Announce index on Bluesky
        ann = self.create_announcement_post(
            title=title,
            excerpt=content[:200] + '...',
            article_url=idx_uri,
            metadata={'has_glitch': False, 'has_math': False, 'phase': 'update'}
        )
        try:
            resp2 = self.client.com.atproto.repo.create_record(
                data=models.ComAtprotoRepoCreateRecord.Data(
                    repo=self.client.me.did,
                    collection='app.bsky.feed.post',
                    record=ann
                ),
                validate=False  # skip local Lexicon validation
            )
            print(f"✓ Bluesky index announcement URI={resp2.uri}")
        except Exception as e:
            print(f"✗ Failed to announce index on Bluesky: {e}")
        return idx_uri


def find_new_articles(last_run_file: str = ".atproto_last_run") -> list:
    last_run = float(open(last_run_file).read()) if os.path.exists(last_run_file) else 0.0
    new = [str(p) for p in Path('.').rglob('phase*/*.html') if p.stat().st_mtime > last_run]
    with open(last_run_file, 'w') as f:
        f.write(str(datetime.now().timestamp()))
    return new


def main():
    parser = argparse.ArgumentParser(description="Publish spinglasscore to AT Protocol")
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
        html_files = [str(p) for p in Path('.').rglob('phase*/*.html')]
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
