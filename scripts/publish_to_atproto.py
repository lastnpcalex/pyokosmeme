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

# AT Protocol imports (install with: pip install atproto)
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
            
        # Extract title from h1 tag
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        title = title_match.group(1) if title_match else "Untitled"
        
        # Clean up spinglasscore formatting
        title = re.sub(r'[⟨⟩]', '', title).strip()
        
        # Extract first paragraph as excerpt
        p_match = re.search(r'<p>([^<]+)</p>', content)
        excerpt = p_match.group(1) if p_match else ""
        excerpt = html.unescape(excerpt)[:300] + "..." if len(excerpt) > 300 else excerpt
        
        # Extract sections
        sections = re.findall(r'<h2>([^<]+)</h2>', content)
        
        # Detect glitch elements and math corruptions for tags
        has_glitch = bool(re.search(r'class="glitch"', content))
        has_math = bool(re.search(r'class="math-corrupt"', content))
        
        # Determine phase from path
        phase = "unknown"
        if "phaseα" in html_path or "phasea" in html_path.lower():
            phase = "phaseα"
        elif "phaseβ" in html_path or "phaseb" in html_path.lower():
            phase = "phaseβ"
        elif "phaseγ" in html_path or "phaseg" in html_path.lower():
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
        """Convert spinglasscore HTML to AT Protocol markdown"""
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Remove HTML boilerplate
        body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
        if body_match:
            content = body_match.group(1)
            
        # Remove scanlines div
        content = re.sub(r'<div class="scanlines"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
        
        # Convert headers
        content = re.sub(r'<h1[^>]*>([^<]+)</h1>', r'# \1\n', content)
        content = re.sub(r'<h2[^>]*>([^<]+)</h2>', r'\n## \1\n', content)
        
        # Convert paragraphs
        content = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', content, flags=re.DOTALL)
        
        # Convert emphasis
        content = re.sub(r'<em>(.*?)</em>', r'*\1*', content)
        
        # Convert glitch and math-corrupt spans to special notation
        content = re.sub(r'<span class="glitch">([^<]+)</span>', r'⟨\1⟩', content)
        content = re.sub(r'<span class="math-corrupt">([^<]+)</span>', r'∂[\1]∂', content)
        
        # Convert code blocks
        content = re.sub(r'<pre><code>(.*?)</code></pre>', r'\n```\n\1\n```\n', content, flags=re.DOTALL)
        content = re.sub(r'<code>(.*?)</code>', r'`\1`', content)
        
        # Convert lists
        content = re.sub(r'<ul[^>]*>(.*?)</ul>', self._convert_list, content, flags=re.DOTALL)
        
        # Remove remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Add metadata footer
        content += f"\n\n---\n\n*Originally published at [spin.pyokosmeme.group](https://spin.pyokosmeme.group)*"
        content += f"\n\n⟨⟨ ∂S/∂t → ∞ ⟩⟩"
        
        return content.strip()
    
    def _convert_list(self, match):
        """Convert HTML list to markdown"""
        list_html = match.group(1)
        items = re.findall(r'<li[^>]*>(.*?)</li>', list_html, re.DOTALL)
        return '\n' + '\n'.join(f'- {item.strip()}' for item in items) + '\n'
    
    def create_blog_post(self, html_path: str) -> Dict:
        """Create AT Protocol blog post from HTML article"""
        metadata = self.extract_article_metadata(html_path)
        markdown_content = self.html_to_markdown(html_path)
        
        # Create blog post record
        record = {
            "$type": "com.whitewind.blog.entry",
            "title": metadata["title"],
            "content": markdown_content,
            "createdAt": datetime.now().isoformat() + "Z",
            "theme": "dark",  # Always dark for spinglasscore
            "tags": []
        }
        
        # Add tags based on content analysis
        tags = [metadata["phase"]]
        
        if metadata["has_glitch"]:
            tags.append("glitch")
        if metadata["has_math"]:
            tags.append("mathematics")
            
        # Add thematic tags
        if "network" in markdown_content.lower():
            tags.append("network-state")
        if "outside" in markdown_content.lower() or "0utside" in markdown_content.lower():
            tags.append("outsideness")
        if "spin" in markdown_content.lower() and "glass" in markdown_content.lower():
            tags.append("spin-glass")
        if "rhizome" in markdown_content.lower():
            tags.append("rhizome")
            
        record["tags"] = tags[:5]  # Limit to 5 tags
        
        return record
    
    def publish_article(self, html_path: str) -> Optional[str]:
        """Publish article to AT Protocol and return URI"""
        try:
            record = self.create_blog_post(html_path)
            
            # Create the post
            response = self.client.com.atproto.repo.create_record(
                repo=self.client.me.did,
                collection="com.whitewind.blog.entry",
                record=record
            )
            
            uri = response.uri
            print(f"✓ Published: {record['title']}")
            print(f"  URI: {uri}")
            print(f"  Tags: {', '.join(record['tags'])}")
            
            return uri
            
        except Exception as e:
            print(f"✗ Failed to publish {html_path}: {e}")
            return None
    
    def publish_index_post(self, new_articles: list) -> Optional[str]:
        """Create an index/announcement post for new articles"""
        if not new_articles:
            return None
            
        title = f"⟨⟨SPINGL∆SS UPDATE⟩⟩ {len(new_articles)} new nodes"
        
        content = f"The archive expands. {len(new_articles)} new documents detected.\n\n"
        
        for article in new_articles:
            metadata = self.extract_article_metadata(article)
            content += f"◈ **{metadata['title']}** ({metadata['phase']})\n"
            content += f"  {metadata['excerpt']}\n\n"
            
        content += "\nAccess the full archive at [spin.pyokosmeme.group](https://spin.pyokosmeme.group)\n\n"
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
            response = self.client.com.atproto.repo.create_record(
                repo=self.client.me.did,
                collection="com.whitewind.blog.entry",
                record=record
            )
            
            print(f"✓ Published index post: {title}")
            return response.uri
            
        except Exception as e:
            print(f"✗ Failed to publish index post: {e}")
            return None


def find_new_articles(last_run_file: str = ".atproto_last_run") -> list:
    """Find articles added since last run"""
    last_run = 0
    if os.path.exists(last_run_file):
        with open(last_run_file, 'r') as f:
            last_run = float(f.read().strip())
    
    new_articles = []
    for phase_dir in Path(".").glob("phase*/"):
        for html_file in phase_dir.glob("*.html"):
            if html_file.stat().st_mtime > last_run:
                new_articles.append(str(html_file))
                
    # Update last run time
    with open(last_run_file, 'w') as f:
        f.write(str(datetime.now().timestamp()))
        
    return new_articles


def main():
    parser = argparse.ArgumentParser(description="Publish spinglasscore to AT Protocol")
    parser.add_argument("--handle", required=True, help="AT Protocol handle")
    parser.add_argument("--password", required=True, help="AT Protocol password")
    parser.add_argument("--all", action="store_true", help="Publish all articles")
    parser.add_argument("--file", help="Publish specific file")
    parser.add_argument("--new-only", action="store_true", help="Only publish new articles")
    
    args = parser.parse_args()
    
    publisher = SpinglassATProto(args.handle, args.password)
    
    if args.file:
        # Publish single file
        publisher.publish_article(args.file)
        
    elif args.all:
        # Publish all articles
        for phase_dir in Path(".").glob("phase*/"):
            for html_file in phase_dir.glob("*.html"):
                publisher.publish_article(str(html_file))
                
    elif args.new_only:
        # Publish only new articles
        new_articles = find_new_articles()
        if new_articles:
            print(f"Found {len(new_articles)} new articles")
            for article in new_articles:
                publisher.publish_article(article)
            publisher.publish_index_post(new_articles)
        else:
            print("No new articles found")
            
    else:
        print("Specify --all, --new-only, or --file")


if __name__ == "__main__":
    main()
