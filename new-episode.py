#!/usr/bin/env python3
"""
new-episode.py — Scaffold and publish a new Tabula Rasa episode.

Usage:
  python new-episode.py "Episode Title Here" --number 006 --duration "45 min"
  python new-episode.py "Episode Title Here" --number 006 --duration "45 min" --publish

Creates a markdown file in content/episodes/, builds Hugo, and optionally
deploys to Netlify. The site auto-deploys on git push to Netlify anyway,
so --publish is just for immediate manual deploys.
"""

import argparse
import os
import re
import subprocess
import sys
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


def create_episode(title, number, duration, description=None, youtube_url="", spotify_url=""):
    """Create a new episode markdown file."""
    slug = slugify(title)
    filename = f"{number}-{slug}.md"
    filepath = os.path.join(EPISODES_DIR, filename)

    if os.path.exists(filepath):
        print(f"ERROR: Episode file already exists: {filepath}")
        sys.exit(1)

    date = datetime.now().strftime("%Y-%m-%d")
    desc = description or f"Episode {number} of Tabula Rasa with Blake Turley."

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

{desc}
"""

    os.makedirs(EPISODES_DIR, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Created: {filepath}")
    return filepath


def build_site():
    """Build the Hugo site."""
    print("\nBuilding site...")
    result = subprocess.run(
        ["hugo", "--gc", "--minify"],
        cwd=SITE_DIR,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"ERROR: Hugo build failed:\n{result.stderr}")
        sys.exit(1)

    print(result.stdout)
    print("Build successful.")


def deploy_site():
    """Deploy to Netlify."""
    print("\nDeploying to Netlify...")
    result = subprocess.run(
        ["npx", "netlify-cli", "deploy", "--prod", "--dir=public"],
        cwd=SITE_DIR,
        capture_output=True,
        text=True,
        timeout=120
    )

    if result.returncode != 0:
        print(f"ERROR: Deploy failed:\n{result.stderr}")
        sys.exit(1)

    print(result.stdout)
    print("Deploy successful.")


def main():
    parser = argparse.ArgumentParser(description="Create a new Tabula Rasa episode")
    parser.add_argument("title", help="Episode title")
    parser.add_argument("--number", required=True, help="Episode number (e.g., 006)")
    parser.add_argument("--duration", required=True, help="Duration (e.g., '45 min')")
    parser.add_argument("--description", help="Episode description")
    parser.add_argument("--youtube", default="", help="YouTube URL")
    parser.add_argument("--spotify", default="", help="Spotify URL")
    parser.add_argument("--publish", action="store_true", help="Build and deploy immediately")
    parser.add_argument("--build-only", action="store_true", help="Build but don't deploy")

    args = parser.parse_args()

    # Create the episode file
    filepath = create_episode(
        title=args.title,
        number=args.number,
        duration=args.duration,
        description=args.description,
        youtube_url=args.youtube,
        spotify_url=args.spotify
    )

    print(f"\nEpisode scaffolded: {filepath}")
    print(f"Edit the file to add show notes / full description.")

    if args.publish or args.build_only:
        build_site()

    if args.publish:
        deploy_site()
        print(f"\nLive at https://tabularasawithblaketurley.com/episodes/{args.number}-{slugify(args.title)}/")
    elif not args.build_only:
        print(f"\nTo publish: python new-episode.py ... --publish")
        print(f"Or: git add & push (Netlify auto-deploys from git)")


if __name__ == "__main__":
    main()
