import argparse
import os
import json
import subprocess
from glob import glob
from tqdm import tqdm
from ml_sentiment_analysis import analyze_sentiment  # ต้องมีไฟล์นี้ในโฟลเดอร์เดียวกัน
import time
import random
import hashlib
import re

# --- Helper: Run yt-dlp for a single link ---
def run_ytdlp(link, outtmpl=None):
    video_id = link.split('v=')[-1].split('&')[0]
    infojson = f"{video_id}.info.json"
    if os.path.exists(infojson):
        return infojson
    cmd = [
        'python', '-m', 'yt_dlp',
        '--write-comments',
        '--skip-download',
    link
    ]
    if outtmpl:
        cmd += ['-o', outtmpl]
    subprocess.run(cmd, check=True)
    # Find the .info.json file
    files = glob(f"*{video_id}*.info.json")
    return files[0] if files else None

def mask_author(author):
    if not author:
        return None
    return hashlib.sha256(author.encode('utf-8')).hexdigest()[:12]

def clean_text_privacy(text):
    if not text:
        return text
    # Mask phone numbers
    text = re.sub(r'\b\d{8,}\b', '[MASKED_PHONE]', text)
    # Mask emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[MASKED_EMAIL]', text)
    # Mask URLs
    text = re.sub(r'https?://\S+', '[MASKED_URL]', text)
    text = re.sub(r'www\.\S+', '[MASKED_URL]', text)
    return text

# --- Helper: Recursively flatten comments and replies ---
def flatten_comments(comments, video_id, parent_id=None, privacy_mode='none'):
    rows = []
    for c in comments:
        # Sentiment analysis (dict)
        sentiment_result = analyze_sentiment(c.get('text', ''))
        # Privacy handling
        author = c.get('author')
        if privacy_mode == 'mask':
            author = mask_author(author)
        elif privacy_mode == 'remove':
            author = None
        text = c.get('text')
        if privacy_mode in ('mask', 'remove'):
            text = clean_text_privacy(text)
        row = {
            'video_id': video_id,
            'comment_id': c.get('id'),
            'parent_id': parent_id,
            'author': author,
            'text': text,
            'like_count': c.get('like_count'),
            'published': c.get('published'),
            'is_reply': parent_id is not None,
            # --- มาตรฐาน sentiment schema ---
            'sentiment': sentiment_result.get('sentiment'),
            'confidence': sentiment_result.get('confidence'),
            'sentiment_score': sentiment_result.get('sentiment_score'),
            'probabilities': sentiment_result.get('probabilities'),
            'model_type': sentiment_result.get('model_type'),
            'privacy_notice': 'This dataset is for research only. Do not use for commercial or personal identification.'
        }
        rows.append(row)
        # Recursively add replies
        replies = c.get('replies', [])
        if replies:
            rows.extend(flatten_comments(replies, video_id, parent_id=c.get('id'), privacy_mode=privacy_mode))
    return rows

# --- Main ---
def main():
    parser = argparse.ArgumentParser(description='Extract YouTube comments using yt-dlp and export as JSONL with sentiment.')
    parser.add_argument('--links', default='youtube_real_links_1500.txt', help='Text file with YouTube links (one per line)')
    parser.add_argument('--output', default='youtube_comments.jsonl', help='Output JSONL file')
    parser.add_argument('--privacy', default='none', choices=['none', 'mask', 'remove'], help='Privacy mode: mask (hash author, mask PII), remove (no author, mask PII), none (no privacy)')
    args = parser.parse_args()

    # Read links
    with open(args.links, encoding='utf-8') as f:
        links = [line.strip() for line in f if line.strip()]

    all_rows = []
    for link in tqdm(links, desc='Processing videos'):
        try:
            infojson = run_ytdlp(link)
            if not infojson or not os.path.exists(infojson):
                print(f"[WARN] No info.json for {link}")
                continue
            with open(infojson, encoding='utf-8') as f:
                data = json.load(f)
            video_id = data.get('id') or os.path.splitext(os.path.basename(infojson))[0]
            comments = data.get('comments', [])
            rows = flatten_comments(comments, video_id, privacy_mode=args.privacy)
            all_rows.extend(rows)
        except Exception as e:
            print(f"[ERROR] {link}: {e}")
        # --- ป้องกัน rate limit/bot block ---
        delay = random.uniform(2.0, 5.0)
        time.sleep(delay)

    # Write JSONL
    with open(args.output, 'w', encoding='utf-8') as f:
        for row in all_rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(f"Exported {len(all_rows)} comments to {args.output}")

if __name__ == '__main__':
    main()
