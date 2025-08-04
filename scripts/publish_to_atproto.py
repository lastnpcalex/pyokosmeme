#!/usr/bin/env python3
"""
⟨⟨ AT PROTOCOL PUBLISHER ⟩⟩
Publishes spinglasscore articles to the AT Protocol network via WhiteWind PDS and broadcasts on Bluesky
"""
import os
import re
import html
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

try:
    from atproto import Client, models
except ImportError:
    print("ERROR: atproto library not installed")
    print("Install with: pip install atproto")
    exit(1)

# Announcement templates
ANNOUNCEMENT_TEMPLATES = {
    "default": """⟨⟨ NEW SPINGL∆SS NODE ⟩⟩

{title}

"{excerpt}"

→ {url}""",
    "minimal": """new node: {title}\n{url}""",
    "phase_specific": {
        "phaseα": """⟨⟨ PH∆SE Α EMISSION ⟩⟩\n{title}\n"{excerpt}"\n∂S/∂t → ∞\n{url}""",
        "phaseβ": """⟨⟨ PH∆SE β CRYSTALLIZATION ⟩⟩\n{title}\nspin glass transition detected\n{url}""",
        "phaseγ": """⟨⟨ PH∆SE γ RADIATION ⟩⟩\n{title}\ntopology: {topology_status}\n{url}"""
    },
    "glitch": """g̸l̸i̸t̸c̸h̸ ̸d̸e̸t̸e̸c̸t̸e̸d̸\n{title}\nsys.tem.mal//function\n{url}""",
    "mathematical": """∂[NEW]/∂t = {title}\n∫∫∫ {excerpt} dx dy dz\nlim(t→∞) = {url}""",
    "cryptic": """◈◈◈◈◈◈◈◈◈◈◈◈\n{encoded_title}\n◈◈◈◈◈◈◈◈◈◈◈◈\n{url}""",
    "network_state": """CONSENSUS.BROADCAST()\nnode: {title}\nstake: {word_count} words\nvalidators: pending\n{url}"""
}

class SpinglassATProto:
    """Handles publishing to both WhiteWind PDS and Bluesky"""
    def __init__(self,
                 handle: str,
                 password: str,
                 blog_url: str,
                 feed_url: str):
        # Client for WhiteWind blog posts
        self.blog_client = Client(blog_url)
        # Client for Bluesky feed posts
        self.feed_client = Client(feed_url)

        # Login both clients
        self.blog_client.login(handle, password)
        self.feed_client.login(handle, password)
        print(f"→ Authenticated user: {handle}")

    def extract_article_metadata(self, html_path: str) -> Dict:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        title = title_match.group(1) if title_match else 'Untitled'
        title = re.sub(r'[⟨⟩]', '', title).strip()
        p_match = re.search(r'<p>([^<]+)</p>', content)
        excerpt = html.unescape(p_match.group(1) if p_match else '')
        if len(excerpt) > 300:
            excerpt = excerpt[:300] + '...'
        has_glitch = bool(re.search(r'class="glitch"', content))
        has_math = bool(re.search(r'class="math-corrupt"', content))
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
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Simple conversion: strip HTML tags
        markdown = re.sub(r'<[^>]+>', '', content)
        return markdown.strip()

    def _format_announcement(self,
                             metadata: Dict,
                             title: str,
                             excerpt: str,
                             url: str,
                             template: str) -> str:
        if template == 'auto':
            if metadata['has_glitch']:
                template = 'glitch'
            elif metadata['has_math']:
                template = 'mathematical'
            elif metadata['phase'] in ANNOUNCEMENT_TEMPLATES['phase_specific']:
                template = metadata['phase']
            else:
                template = 'default'
        if template in ANNOUNCEMENT_TEMPLATES['phase_specific']:
            tpl = ANNOUNCEMENT_TEMPLATES['phase_specific'][template]
        else:
            tpl = ANNOUNCEMENT_TEMPLATES.get(template, ANNOUNCEMENT_TEMPLATES['default'])
        encoded_title = ''.join([chr(ord(c)+1) for c in title])
        word_count = len(excerpt.split())
        topology_status = 'WARPED' if metadata['has_glitch'] else 'STABLE'
        return tpl.format(
            title=title,
            excerpt=excerpt,
            url=url,
            encoded_title=encoded_title,
            word_count=word_count,
            topology_status=topology_status
        )

    def create_announcement(self,
                            metadata: Dict,
                            title: str,
                            excerpt: str,
                            url: str,
                            template: str = 'default') -> Dict:
        text = self._format_announcement(metadata, title, excerpt, url, template)
        return {
            '$type': 'app.bsky.feed.post',
            'text': text,
            'createdAt': datetime.now().isoformat() + 'Z'
        }

    def publish_blog(self, html_path: str) -> Optional[str]:
        meta = self.extract_article_metadata(html_path)
        rec = {
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
                record=rec
            )
        )
        print(f"✓ Blog published: {resp.uri}")
        return resp.uri

    def publish_feed(self, announcement: Dict) -> Optional[str]:
        resp = self.feed_client.com.atproto.repo.create_record(
            data=models.ComAtprotoRepoCreateRecord.Data(
                repo=self.feed_client.me.did,
                collection='app.bsky.feed.post',
                record=announcement
            )
        )
        print(f"✓ Announcement posted: {resp.uri}")
        return resp.uri

    def publish_article(self, html_path: str) -> None:
        print(f"→ Processing {html_path}")
        blog_uri = self.publish_blog(html_path)
        meta = self.extract_article_metadata(html_path)
        ann = self.create_announcement(meta, meta['title'], meta['excerpt'], blog_uri)
        self.publish_feed(ann)

    def publish_index(self, paths: List[str]) -> None:
        title = f"⟨⟨SPINGL∆SS UPDATE⟩⟩ {len(paths)} new nodes"
        excerpt = '\n'.join([self.extract_article_metadata(p)['title'] for p in paths])
        idx_uri = self.publish_blog(paths[0])
        ann = self.create_announcement({'has_glitch': False, 'has_math': False, 'phase': 'update'}, title, excerpt, idx_uri)
        self.publish_feed(ann)


def find_new_articles(last_run_file: str = '.atproto_last_run') -> List[str]:
    last_run = float(open(last_run_file).read()) if os.path.exists(last_run_file) else 0.0
    new = [str(p) for p in Path('.').rglob('phase*/*.html') if p.stat().st_mtime > last_run]
    with open(last_run_file, 'w') as f:
        f.write(str(datetime.now().timestamp()))
    return new


def main():
    parser = argparse.ArgumentParser(description='Publish spinglasscore to AT Protocol')
    parser.add_argument('--handle', required=True, help='AT Protocol handle')
    parser.add_argument('--password', required=True, help='AT Protocol password')
    parser.add_argument('--blog-url',
                        default='https://blog.whitewind.com/xrpc',
                        help='WhiteWind PDS XRPC endpoint')
    parser.add_argument('--feed-url',
                        default='https://bsky.social/xrpc',
                        help='Bluesky XRPC endpoint')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Publish all HTML files')
    group.add_argument('--file', help='Publish a single HTML file')
    group.add_argument('--new-only', action='store_true', help='Publish only files newer than last run')
    args = parser.parse_args()

    publisher = SpinglassATProto(
        args.handle,
        args.password,
        args.blog_url,
        args.feed_url
    )

    if args.all:
        paths = [str(p) for p in Path('.').rglob('phase*/*.html')]
        for p in paths:
            publisher.publish_article(p)
    elif args.file:
        publisher.publish_article(args.file)
    else:
        new_paths = find_new_articles()
        if new_paths:
            for p in new_paths:
                publisher.publish_article(p)
            publisher.publish_index(new_paths)
        else:
            print('No new articles found')

if __name__ == '__main__':
    main()
