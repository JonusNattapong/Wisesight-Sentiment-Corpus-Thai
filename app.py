import argparse
import os
import json
import subprocess
from glob import glob
from tqdm import tqdm
# เปลี่ยนจาก ml_sentiment_analysis เป็น sentiment_integration สำหรับระบบใหม่
try:
    from sentiment_integration import analyze_detailed_sentiment, enhanced_analyze_sentiment
    DETAILED_SENTIMENT_AVAILABLE = True
except ImportError:
    # Fallback ไปยังระบบเดิมถ้าโมดูลใหม่ไม่พร้อม
    try:
        from ml_sentiment_analysis import analyze_sentiment
        DETAILED_SENTIMENT_AVAILABLE = False
    except ImportError:
        def analyze_sentiment(text):
            return {"sentiment": "neutral", "confidence": 0.0, "sentiment_score": 0.0}
        DETAILED_SENTIMENT_AVAILABLE = False

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
def flatten_comments(comments, video_id, parent_id=None, privacy_mode='none', sentiment_mode='basic', detailed_mode='single'):
    rows = []
    for c in comments:
        comment_text = c.get('text', '')
        
        # Sentiment analysis based on mode
        if sentiment_mode == 'detailed' and DETAILED_SENTIMENT_AVAILABLE:
            # ใช้ระบบ detailed sentiment analysis
            sentiment_result = analyze_detailed_sentiment(
                comment_text, 
                mode=detailed_mode,  # 'single' หรือ 'multi'
                threshold=0.3,
                include_scores=True
            )
            
            # แปลงเป็น format ที่เข้ากับ schema เดิม
            sentiment_basic = sentiment_result.get('sentiment', 'neutral')
            confidence = sentiment_result.get('confidence', 0.0)
            sentiment_score = _sentiment_to_score(sentiment_basic)
            
        elif sentiment_mode == 'enhanced' and DETAILED_SENTIMENT_AVAILABLE:
            # ใช้ enhanced analysis (backward compatible)
            sentiment_result = enhanced_analyze_sentiment(comment_text)
            sentiment_basic = sentiment_result.get('sentiment', 'neutral')
            confidence = sentiment_result.get('confidence', 0.0)
            sentiment_score = sentiment_result.get('sentiment_score', 0.0)
            
        else:
            # ใช้ระบบเดิม (fallback)
            if DETAILED_SENTIMENT_AVAILABLE:
                sentiment_result = enhanced_analyze_sentiment(comment_text)
            else:
                sentiment_result = analyze_sentiment(comment_text)
            
            sentiment_basic = sentiment_result.get('sentiment', 'neutral')
            confidence = sentiment_result.get('confidence', 0.0)
            sentiment_score = sentiment_result.get('sentiment_score', 0.0)
        
        # Privacy handling
        author = c.get('author')
        if privacy_mode == 'mask':
            author = mask_author(author)
        elif privacy_mode == 'remove':
            author = None
        text = c.get('text')
        if privacy_mode in ('mask', 'remove'):
            text = clean_text_privacy(text)
        
        # Base row structure
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
            'sentiment': sentiment_basic,
            'confidence': confidence,
            'sentiment_score': sentiment_score,
            'model_type': sentiment_result.get('model_type', 'unknown'),
            'privacy_notice': 'This dataset is for research only. Do not use for commercial or personal identification.'
        }
        
        # เพิ่มข้อมูล detailed sentiment ถ้าเปิดใช้งาน
        if sentiment_mode == 'detailed' and DETAILED_SENTIMENT_AVAILABLE:
            row.update({
                'detailed_sentiment_analysis': sentiment_result,
                'analysis_mode': detailed_mode,
                'detailed_emotions': sentiment_result.get('detailed_emotions', []) if detailed_mode == 'multi' else [sentiment_result.get('detailed_emotion', '')],
                'emotion_groups': sentiment_result.get('emotion_groups', []) if detailed_mode == 'multi' else [sentiment_result.get('emotion_group', '')],
                'context': sentiment_result.get('context', 'unknown')
            })
        
        elif sentiment_mode == 'enhanced' and DETAILED_SENTIMENT_AVAILABLE:
            row.update({
                'detailed_emotion': sentiment_result.get('detailed_emotion', ''),
                'emotion_group': sentiment_result.get('emotion_group', ''),
                'context': sentiment_result.get('context', 'unknown')
            })
        
        rows.append(row)
        
        # Recursively add replies
        replies = c.get('replies', [])
        if replies:
            rows.extend(flatten_comments(replies, video_id, parent_id=c.get('id'), privacy_mode=privacy_mode, sentiment_mode=sentiment_mode, detailed_mode=detailed_mode))
    return rows

def _sentiment_to_score(sentiment: str) -> float:
    """แปลง sentiment เป็น score สำหรับ backward compatibility"""
    if sentiment == "positive":
        return 0.7
    elif sentiment == "negative":
        return -0.7
    else:
        return 0.0

# --- Main ---
def main():
    parser = argparse.ArgumentParser(description='Extract YouTube comments using yt-dlp and export as JSONL with advanced Thai sentiment analysis.')
    parser.add_argument('--links', default='youtube_real_links_1500.txt', help='Text file with YouTube links (one per line)')
    parser.add_argument('--output', default='youtube_comments.jsonl', help='Output JSONL file')
    parser.add_argument('--privacy', default='none', choices=['none', 'mask', 'remove'], help='Privacy mode: mask (hash author, mask PII), remove (no author, mask PII), none (no privacy)')
    
    # Sentiment analysis options
    parser.add_argument('--sentiment-mode', default='basic', 
                       choices=['basic', 'enhanced', 'detailed'], 
                       help='Sentiment analysis mode: basic (old system), enhanced (new system, backward compatible), detailed (full multi-emotion analysis)')
    parser.add_argument('--detailed-mode', default='single', 
                       choices=['single', 'multi'],
                       help='For detailed sentiment: single (single-label classification) or multi (multi-label classification)')
    parser.add_argument('--no-sentiment', action='store_true', 
                       help='Disable sentiment analysis completely')
    
    args = parser.parse_args()

    # Check sentiment availability
    if args.sentiment_mode in ['enhanced', 'detailed'] and not DETAILED_SENTIMENT_AVAILABLE:
        print(f"⚠️  Warning: Detailed sentiment analysis not available. Falling back to basic mode.")
        print("   To use advanced features, ensure detailed_thai_sentiment.py and sentiment_integration.py are available.")
        args.sentiment_mode = 'basic'

    print(f"🎯 Sentiment Analysis Configuration:")
    print(f"   Mode: {args.sentiment_mode}")
    if args.sentiment_mode == 'detailed':
        print(f"   Classification: {args.detailed_mode}-label")
    print(f"   Privacy: {args.privacy}")
    print()

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
            
            # Process comments with selected sentiment mode
            if args.no_sentiment:
                rows = flatten_comments_no_sentiment(comments, video_id, privacy_mode=args.privacy)
            else:
                rows = flatten_comments(comments, video_id, privacy_mode=args.privacy, 
                                      sentiment_mode=args.sentiment_mode, detailed_mode=args.detailed_mode)
            
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
    
    print(f"✅ Exported {len(all_rows)} comments to {args.output}")
    
    # Show summary statistics if detailed sentiment was used
    if args.sentiment_mode == 'detailed' and DETAILED_SENTIMENT_AVAILABLE and not args.no_sentiment:
        show_sentiment_statistics(all_rows, args.detailed_mode)

def flatten_comments_no_sentiment(comments, video_id, parent_id=None, privacy_mode='none'):
    """Flatten comments without sentiment analysis (for performance/testing)"""
    rows = []
    for c in comments:
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
            'privacy_notice': 'This dataset is for research only. Do not use for commercial or personal identification.'
        }
        rows.append(row)
        
        # Recursively add replies
        replies = c.get('replies', [])
        if replies:
            rows.extend(flatten_comments_no_sentiment(replies, video_id, parent_id=c.get('id'), privacy_mode=privacy_mode))
    return rows

def show_sentiment_statistics(rows, detailed_mode):
    """Show summary statistics for sentiment analysis"""
    if not rows:
        return
    
    print(f"\n📊 Sentiment Analysis Statistics:")
    print(f"   Total comments analyzed: {len(rows)}")
    
    # Basic sentiment counts
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    emotion_counts = {}
    group_counts = {}
    context_counts = {}
    
    for row in rows:
        # Basic sentiment
        sentiment = row.get('sentiment', 'neutral')
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
        
        # Detailed emotions (if available)
        if detailed_mode == 'single':
            emotions = [row.get('detailed_emotions', [''])[0]] if row.get('detailed_emotions') else ['']
            groups = [row.get('emotion_groups', [''])[0]] if row.get('emotion_groups') else ['']
        else:  # multi
            emotions = row.get('detailed_emotions', [])
            groups = row.get('emotion_groups', [])
        
        for emotion in emotions:
            if emotion:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        for group in groups:
            if group:
                group_counts[group] = group_counts.get(group, 0) + 1
        
        # Context
        context = row.get('context', '')
        if context:
            context_counts[context] = context_counts.get(context, 0) + 1
    
    print(f"   Basic sentiment distribution:")
    for sentiment, count in sentiment_counts.items():
        percentage = (count / len(rows)) * 100
        print(f"     {sentiment}: {count} ({percentage:.1f}%)")
    
    if emotion_counts:
        print(f"   Top emotions detected:")
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for emotion, count in sorted_emotions:
            percentage = (count / len(rows)) * 100
            print(f"     {emotion}: {count} ({percentage:.1f}%)")
    
    if group_counts:
        print(f"   Emotion group distribution:")
        for group, count in group_counts.items():
            percentage = (count / len(rows)) * 100
            print(f"     {group}: {count} ({percentage:.1f}%)")
    
    if context_counts:
        print(f"   Language context distribution:")
        for context, count in context_counts.items():
            percentage = (count / len(rows)) * 100
            print(f"     {context}: {count} ({percentage:.1f}%)")
    
    print()

if __name__ == '__main__':
    main()
