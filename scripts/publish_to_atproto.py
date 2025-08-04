#!/usr/bin/env python3
"""
⟨⟨ AT PROTOCOL PUBLISHER ⟩⟩
Publishes spinglasscore HTML articles to a WhiteWind blog PDS and makes announcements on Bluesky via the AT Protocol Python SDK.
Updated based on best practices for custom lexicon interaction.
"""
import os
import re
import html
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from atproto import Client, models
    from atproto.xrpc_client.models.com.atproto.repo import CreateRecord
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

    def __init__(self, handle: str, password: str, blog_url: str, feed_url: str):
        # Instantiate clients; pass PDS base URLs (no /xrpc suffix)
        self.blog_client = Client()
        self.feed_client = Client()

        # Login to the PDS for the blog (e.g., bsky.social)
        print(f"→ Authenticating with PDS at {blog_url}...")
        self.blog_client.login(handle, password, base_url=blog_url)
        
        # If the feed PDS is different, log in there too. Otherwise, reuse.
        if blog_url == feed_url:
            self.feed_client = self.blog_client
        else:
            print(f"→ Authenticating with Feed PDS at {feed_url}...")
            self.feed_client.login(handle, password, base_url=feed_url)
        
        print(f"→ Authenticated as {handle} ({self.blog_client.me.did})")

    def extract_article_metadata(self, html_path: str) -> Dict[str, Any]:
        content = Path(html_path).read_text(encoding='utf-8')
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        title = title_match.group(1).strip() if title_match else "Untitled"
        title = re.sub(r'[⟨⟩]', '', title)

        p_match = re.search(r'<p>([^<]+)</p>', content)
        excerpt = html.unescape(p_match.group(1).strip() if p_match else "")
        if len(excerpt) > 280:
            excerpt = excerpt[:280] + '...'

        has_glitch = 'glitch' in html_path.lower()
        has_math = 'math' in html_path.lower()

        lower_path = html_path.lower()
        phase = 'unknown'
        if 'phaseα' in lower_path or 'phasea' in lower_path:
            phase = 'phaseα'
        elif 'phaseβ' in lower_path or 'phaseb' in lower_path:
            phase = 'phaseβ'
        elif 'phaseγ' in lower_path or 'phaseg' in lower_path:
            phase = 'phaseγ'

        return {
            'title': title,
            'excerpt': excerpt,
            'has_glitch': has_glitch,
            'has_math': has_math,
            'phase': phase
        }

    def html_to_markdown(self, html_path: str) -> str:
        content = Path(html_path).read_text(encoding='utf-8')
        # A more robust conversion might be needed, but this is a simple start
        text = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

    def publish_blog(self, html_path: str) -> Optional[CreateRecord.Response]:
        """
        Constructs and publishes a com.whtwnd.blog.entry record.
        This function is updated to reflect the robust practices from the document.
        """
        print(f"→ Preparing blog post for: {html_path}")
        meta = self.extract_article_metadata(html_path)
        markdown_content = self.html_to_markdown(html_path)

        # The official NSID for WhiteWind blog entries.
        collection_nsid = 'com.whtwnd.blog.entry'

        # Per the spec, the timestamp must be a valid ISO 8601 string.
        created_at_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        # --- Construct the Record Payload ---
        # This dictionary must precisely match the com.whtwnd.blog.entry schema.
        record_data = {
            '$type': collection_nsid,
            'title': meta['title'],
            'content': markdown_content,
            'createdAt': created_at_iso,
            # 'theme' is an optional field from the schema.
            'theme': meta['phase'] if meta['phase'] != 'unknown' else 'default',
            # 'ogp' (for a banner image) is another optional field.
            # 'ogp': {
            #     'url': 'https://example.com/banner.png',
            #     'width': 1200,
            #     'height': 630
            # }
        }

        print(f"→ Publishing record to collection: {collection_nsid}")
        try:
            # Use the low-level create_record procedure for custom lexicons.
            response = self.blog_client.com.atproto.repo.create_record(
                repo=self.blog_client.me.did,
                collection=collection_nsid,
                record=record_data,
                # Best practice: always explicitly enable server-side validation.
                validate=True
            )
            print(f"✓ Blog post published successfully: {response.uri}")
            return response
        except Exception as e:
            print(f"✗ ERROR creating blog post record: {e}")
            print("  Please check that the record_data dictionary matches the lexicon schema.")
            return None

    def create_announcement(self, meta: Dict, title: str, excerpt: str, url_block: str) -> str:
        # This function now receives a pre-formatted block of URLs
        template = ANNOUNCEMENT_TEMPLATES.get('default', "{title}\n{excerpt}\n{url}")
        return template.format(title=title, excerpt=f'"{excerpt}"', url=url_block)

    def publish_feed(self, text: str) -> Optional[CreateRecord.Response]:
        try:
            post = self.feed_client.send_post(text=text)
            print(f"✓ Announcement posted: {post.uri}")
            return post
        except Exception as e:
            print(f"✗ Failed to post announcement on Bluesky: {e}")
            return None

    def publish_article(self, html_path: str) -> None:
        # This function was updated to correctly handle the response
        blog_post_response = self.publish_blog(html_path)

        if not blog_post_response:
            print(f"✗ Skipping announcement for {html_path} due to blog post failure.")
            return

        blog_uri = blog_post_response.uri
        meta = self.extract_article_metadata(html_path)
        rkey = blog_uri.split('/')[-1]
        handle = self.blog_client.me.handle

        # Build the user-friendly URLs for the announcement post
        whitewind_url = f"https://whtwnd.com/{handle}/entries/{rkey}"
        bluesky_url = f"https://bsky.app/profile/{handle}/post/{rkey}"
        custom_spin_url = "https://spin.pyokosmeme.group/"

        url_block = (
            f"→ Read on WhiteWind: {whitewind_url}\n"
            f"→ View on Bluesky: {bluesky_url}\n"
            f"→ Spin Group: {custom_spin_url}"
        )

        text = self.create_announcement(meta, meta['title'], meta['excerpt'], url_block)
        self.publish_feed(text)


def main():
    parser = argparse.ArgumentParser(description='Publish spinglasscore to AT Protocol')
    parser.add_argument('--handle', required=True, help='AT Protocol handle')
    parser.add_argument('--password', required=True, help='AT Protocol App Password')
    
    # Set the correct, robust defaults based on our previous discussions.
    parser.add_argument('--blog-url', default='https://bsky.social', help='PDS where blog records are stored')
    parser.add_argument('--feed-url', default='https://bsky.social', help='PDS for Bluesky announcements')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Publish all HTML files')
    group.add_argument('--file', help='Publish a single HTML file')
    
    args = parser.parse_args()
    
    try:
        publisher = SpinglassATProto(args.handle, args.password, args.blog_url, args.feed-url)

        if args.all:
            # Note: Path.glob is better than rglob with a wildcard if depth is known
            for p in Path('.').glob('phase*/*.html'):
                publisher.publish_article(str(p))
        elif args.file:
            publisher.publish_article(args.file)
            
    except Exception as e:
        print(f"\nAn unexpected error occurred in main: {e}")

if __name__ == '__main__':
    main()
