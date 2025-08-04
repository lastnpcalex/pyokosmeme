#!/usr/bin/env python3
"""
⟨⟨ AT PROTOCOL PUBLISHER ⟩⟩
Publishes spinglasscore HTML articles to a WhiteWind blog PDS and makes announcements on Bluesky via the AT Protocol Python SDK
"""
import os
import re
import html
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from atproto import Client, client_utils, models
except ImportError:
    print("ERROR: atproto library not installed")
    print("Install with: pip install atproto")
    exit(1)

# Announcement templates
ANNOUNCEMENT_TEMPLATES = {
    "default": """
⟨⟨ NEW SPINGL∆SS NODE ⟩⟩

{title}

"{excerpt}"

→ {url}
""",

    "minimal": """
new node: {title}
{url}
""",

    "phase_specific": {
        "phaseα": """
⟨⟨ PH∆SE Α EMISSION ⟩⟩
{title}
"{excerpt}"
∂S/∂t → ∞
{url}
""",
        "phaseβ": """
⟨⟨ PH∆SE β CRYSTALLIZATION ⟩⟩
{title}
spin glass transition detected
{url}
""",
        "phaseγ": """
⟨⟨ PH∆SE γ RADIATION ⟩⟩
{title}
topology: {topology_status}
{url}
""",
    },

    "glitch": """
g̸l̸i̸t̸c̸h̸ ̸d̸e̸t̸e̸c̸t̸e̸d̸
{title}
sys.tem.mal//function
{url}
""",

    "mathematical": """
∂[NEW]/∂t = {title}
∫∫∫ {excerpt} dx dy dz
lim(t→∞) = {url}
""",

    "cryptic": """
◈◈◈◈◈◈◈◈◈◈◈◈
{encoded_title}
◈◈◈◈◈◈◈◈◈◈◈◈
{url}
""",

    "network_state": """
CONSENSUS.BROADCAST()
node: {title}
stake: {word_count} words
validators: pending
{url}
"""
}

class SpinglassATProto:
    """Publishes blog posts to WhiteWind PDS and announcements to Bluesky"""

    def __init__(self,
                 handle: str,
                 password: str,
                 blog_url: str,
                 feed_url: str):
        # Instantiate clients; pass PDS base URLs (no /xrpc suffix)
        self.blog_client = Client(blog_url)
        self.feed_client = Client(feed_url)

        # Authenticate both
        self.blog_client.login(handle, password)
        self.feed_client.login(handle, password)
        print(f"→ Authenticated as {handle}")

    def extract_article_metadata(self, html_path: str) -> Dict:
        content = Path(html_path).read_text(encoding='utf-8')
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        title = (title_match.group(1).strip() if title_match else "Untitled")
        title = re.sub(r'[⟨⟩]', '', title)

        p_match = re.search(r'<p>([^<]+)</p>', content)
        excerpt = html.unescape(p_match.group(1) if p_match else "")
        if len(excerpt) > 300:
            excerpt = excerpt[:300] + '...'

        has_glitch = bool(re.search(r'class="glitch"', content))
        has_math   = bool(re.search(r'class="math-corrupt"', content))

        lower = html_path.lower()
        if 'phaseα' in lower or 'phasea' in lower:
            phase = 'phaseα'
        elif 'phaseβ' in lower or 'phaseb' in lower:
            phase = 'phaseβ'
        elif 'phaseγ' in lower or 'phaseg' in lower:
            phase = 'phaseγ'
        else:
            phase = 'unknown'

        return {
            'title': title,
            'excerpt': excerpt,
            'has_glitch': has_glitch,
            'has_math': has_math,
            'phase': phase
        }

    def html_to_markdown(self, html_path: str) -> str:
        # A simple HTML -> plain text conversion
        content = Path(html_path).read_text(encoding='utf-8')
        text = re.sub(r'<[^>]+>', '', content)
        return text.strip()

    def _format_announcement(self,
                             meta: Dict,
                             title: str,
                             excerpt: str,
                             url: str,
                             template: str) -> str:
        if template == 'auto':
            if meta['has_glitch']:
                template = 'glitch'
            elif meta['has_math']:
                template = 'mathematical'
            elif meta['phase'] in ANNOUNCEMENT_TEMPLATES.get('phase_specific', {}):
                template = meta['phase']
            else:
                template = 'default'

        if template in ANNOUNCEMENT_TEMPLATES.get('phase_specific', {}):
            tpl = ANNOUNCEMENT_TEMPLATES['phase_specific'][template]
        else:
            tpl = ANNOUNCEMENT_TEMPLATES.get(template, ANNOUNCEMENT_TEMPLATES['default'])

        encoded_title = ''.join(chr(ord(c)+1) for c in title)
        word_count    = len(excerpt.split())
        topology_status = 'WARPED' if meta['has_glitch'] else 'STABLE'

        return tpl.format(
            title=title,
            excerpt=excerpt,
            url=url,
            encoded_title=encoded_title,
            word_count=word_count,
            topology_status=topology_status
        )

    def create_announcement(self,
                            meta: Dict,
                            title: str,
                            excerpt: str,
                            url: str,
                            template: str = 'default') -> str:
        # Build a TextBuilder and send as plain text
        text = self._format_announcement(meta, title, excerpt, url, template)
        # Optionally use TextBuilder for rich formatting:
        # tb = client_utils.TextBuilder().text(text)
        return text

    def publish_blog(self, html_path: str) -> Optional[str]:
        meta = self.extract_article_metadata(html_path)
        record = {
            '$type': 'com.whitewind.blog.entry',
            'title': meta['title'],
            'content': self.html_to_markdown(html_path),
            'createdAt': datetime.now().isoformat() + 'Z',
            'theme': 'dark',
            'tags': ([meta['phase']] +
                     (['glitch'] if meta['has_glitch'] else []) +
                     (['mathematics'] if meta['has_math'] else []))[:5]
        }
        resp = self.blog_client.com.atproto.repo.create_record(
            data=models.ComAtprotoRepoCreateRecord.Data(
                repo=self.blog_client.me.did,
                collection='com.whitewind.blog.entry',
                record=record
            )
        )
        print(f"✓ Blog published: {resp.uri}")
        return resp.uri

    def publish_feed(self, text: str) -> Optional[str]:
        # Use high-level send_post convenience method
        try:
            post = self.feed_client.send_post(text=text)
            print(f"✓ Announcement posted: {post.uri}")
            return post.uri
        except Exception as e:
            print(f"✗ Failed to post announcement on Bluesky: {e}")
            return None

    def publish_article(self, html_path: str) -> None:
        print(f"→ Processing: {html_path}")
        blog_uri = self.publish_blog(html_path)
        meta = self.extract_article_metadata(html_path)
        text = self.create_announcement(meta, meta['title'], meta['excerpt'], blog_uri)
        self.publish_feed(text)

    def publish_index(self, paths: List[str]) -> None:
        title = f"⟨⟨SPINGL∆SS UPDATE⟩⟩ {len(paths)} new nodes"
        excerpt = '\n'.join(self.extract_article_metadata(p)['title'] for p in paths)
        idx_uri = self.publish_blog(paths[0])
        text = self.create_announcement({'has_glitch': False, 'has_math': False, 'phase': 'update'},
                                        title, excerpt, idx_uri)
        self.publish_feed(text)


def find_new_articles(last_run_file: str = '.atproto_last_run') -> List[str]:
    last_run = 0.0
    if os.path.exists(last_run_file):
        last_run = float(Path(last_run_file).read_text())
    new = [str(p) for p in Path('.').rglob('phase*/*.html') if p.stat().st_mtime > last_run]
    Path(last_run_file).write_text(str(datetime.now().timestamp()))
    return new


def main():
    parser = argparse.ArgumentParser(description='Publish spinglasscore to AT Protocol')
    parser.add_argument('--handle',    required=True, help='AT Protocol handle')
    parser.add_argument('--password',  required=True, help='AT Protocol password')
    parser.add_argument('--blog-url',  default='https://blog.whitewind.com', help='WhiteWind PDS base URL')
    parser.add_argument('--feed-url',  default='https://bsky.social',        help='Bluesky base URL')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all',      action='store_true', help='Publish all HTML files')
    group.add_argument('--file',     help='Publish a single HTML file')
    group.add_argument('--new-only', action='store_true', help='Publish only files newer than last run')

    args = parser.parse_args()
    publisher = SpinglassATProto(args.handle, args.password, args.blog_url, args.feed_url)

    if args.all:
        for p in Path('.').rglob('phase*/*.html'):
            publisher.publish_article(str(p))
    elif args.file:
        publisher.publish_article(args.file)
    else:
        new = find_new_articles()
        if new:
            for p in new:
                publisher.publish_article(p)
            publisher.publish_index(new)
        else:
            print('No new articles found')

if __name__ == '__main__':
    main()
