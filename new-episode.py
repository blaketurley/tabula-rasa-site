#!/usr/bin/env python3
"""
new-episode.py — Create and publish a new Tabula Rasa episode.

Usage:
  python new-episode.py "Episode Title" --number 006 --duration "45 min"
  python new-episode.py "Episode Title" --number 006 --duration "45 min" --description "Show notes here"
  python new-episode.py "Episode Title" --number 006 --duration "45 min" --youtube "https://youtu.be/xxx" --spotify "https://open.spotify.com/xxx"

What happens:
  1. Creates content/episodes/006-episode-title.md with front matter
  2. Git add + commit + push to main
  3. GitHub Actions picks up the push, builds Hugo, deploys to Netlify
  4. Live at tabularasawithblaketurley.com in ~60 seconds

To auto-detect the next episode number, omit --number:
  python new-episode.py "Episode Title" --duration "45 min"
"""

import argparse
import os
import re
import subprocess
import sys
import glob
from datetime import datetime


SITE_DIR = os.path.dirname(os.path.abspath(__file__))
EPISODES_DIR = os.path.join(SITE_DIR, "content", "episodes")


def slugify(title):
    """Convert title to URL-friendly slug."""
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def get_next_number():
    """Auto-detect the next episode number from existing files."""
    existing = glob.glob(os.path.join(EPISODES_DIR, "[0-9]*.md"))
    if not existing:
        return "001"

    numbers = []
    for f in existing:
        basename = os.path.basename(f)
        match = re.match(r'^(\d+)', basename)
        if match:
            numbers.append(int(match.group(1)))

    next_num = max(numbers) + 1 if numbers else 1
    return f"{next_num:03d}"


def create_episode(title, number, duration, description=None, youtube_url="", spotify_url="", show_notes=""):
    """Create a new episode markdown file."""
    slug = slugify(title)
    filename = f"{number}-{slug}.md"
    filepath = os.path.join(EPISODES_DIR, filename)

    if os.path.exists(filepath):
        print(f"ERROR: Episode file already exists: {filepath}")
        sys.exit(1)

    date = datetime.now().strftime("%Y-%m-%d")
    desc = description or f"Episode {number} of Tabula Rasa with Blake Turley."
    notes = show_notes or desc

    content = f"""---
title: "{title}"
date: {date}
number: "{number}"
duration: "{duration}"
description: "{desc}"
youtube: "{youtube_url}"
spotify: "{spotify_url}"
draft: false
---

{notes}
"""

    os.makedirs(EPISODES_DIR, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Created: {filepath}")
    return filepath


def git_push(filepath, title, number):
    """Git add, commit, push to trigger GitHub Actions deploy."""
    print("\nPushing to GitHub (auto-deploys via Actions)...")

    # Add the new file
    result = subprocess.run(
        ["git", "add", filepath],
        cwd=SITE_DIR,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"ERROR: git add failed:\n{result.stderr}")
        sys.exit(1)

    # Commit
    commit_msg = f"episode: EP{number} — {title}"
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=SITE_DIR,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"ERROR: git commit failed:\n{result.stderr}")
        sys.exit(1)

    print(f"Committed: {commit_msg}")

    # Push
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=SITE_DIR,
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode != 0:
        print(f"ERROR: git push failed:\n{result.stderr}")
        sys.exit(1)

    print("Pushed to GitHub.")
    print("GitHub Actions will build Hugo and deploy to Netlify (~60s).")


def main():
    parser = argparse.ArgumentParser(
        description="Create and publish a new Tabula Rasa episode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Why Every Founder Needs a Lawyer" --duration "42 min"
  %(prog)s "Contract Tricks" --number 007 --duration "38 min" --youtube "https://youtu.be/abc"
  %(prog)s "The Big One" --duration "1 hr 12 min" --description "Show notes here" --draft
        """
    )
    parser.add_argument("title", help="Episode title")
    parser.add_argument("--number", help="Episode number (e.g., 006). Auto-detects if omitted.")
    parser.add_argument("--duration", required=True, help="Duration (e.g., '45 min')")
    parser.add_argument("--description", help="Short description / show notes summary")
    parser.add_argument("--show-notes", help="Full show notes body text (markdown)")
    parser.add_argument("--youtube", default="", help="YouTube URL")
    parser.add_argument("--spotify", default="", help="Spotify URL")
    parser.add_argument("--draft", action="store_true", help="Create as draft (won't appear on site)")
    parser.add_argument("--no-push", action="store_true", help="Create file only, don't git push")

    args = parser.parse_args()

    # Auto-detect episode number if not provided
    number = args.number or get_next_number()
    print(f"Episode number: {number}")

    # Create the episode file
    filepath = create_episode(
        title=args.title,
        number=number,
        duration=args.duration,
        description=args.description,
        youtube_url=args.youtube,
        spotify_url=args.spotify,
        show_notes=args.show_notes or ""
    )

    # Handle draft flag
    if args.draft:
        # Rewrite with draft: true
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('draft: false', 'draft: true')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Marked as DRAFT (won't appear on live site).")

    slug = slugify(args.title)
    url = f"https://tabularasawithblaketurley.com/episodes/{number}-{slug}/"

    if args.no_push:
        print(f"\nFile created. To publish: git add, commit, push to main.")
        print(f"Will be live at: {url}")
    elif args.draft:
        print(f"\nDraft created. When ready, change 'draft: true' to 'draft: false' and push.")
    else:
        git_push(filepath, args.title, number)
        print(f"\nWill be live at: {url}")


if __name__ == "__main__":
    main()
