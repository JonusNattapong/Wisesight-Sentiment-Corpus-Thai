#!/usr/bin/env python3
"""
DekDataset Social Media Comments Extractor
สคริปสำหรับดึงความคิดเห็นจาก social media platforms
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from social_media_utils import extract_social_media_comments, save_comments_for_training

def show_sample_data(comments, max_samples=3):
    """Show sample comments data"""
    if not comments:
        return
    
    print(f"\nตัวอย่างข้อมูลที่ได้ ({min(len(comments), max_samples)} รายการ):")
    print("-" * 60)
    
    for i, comment in enumerate(comments[:max_samples]):
        print(f"[{i+1}] {comment.get('text', '')[:100]}...")
        if 'sentiment' in comment:
            print(f"    Sentiment: {comment['sentiment']}")
        if 'emotion' in comment:
            print(f"    Emotion: {comment['emotion']}")
        if 'ml_enhanced' in comment:
            ml_status = "ML-Enhanced" if comment['ml_enhanced'] else "Rule-based"
            print(f"    Analysis: {ml_status}")
            if comment.get('ml_confidence'):
                print(f"    ML Confidence: {comment['ml_confidence']:.2f}")
        if 'author' in comment and comment['author'] != 'Unknown':
            print(f"    Author: {comment['author']}")
        print()

def read_urls_from_file(file_path):
    """Read URLs from a text file (one URL per line)"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    urls.append(line)
        
        print(f"[INFO] อ่านได้ {len(urls)} URLs จากไฟล์: {file_path}")
        return urls
        
    except FileNotFoundError:
        print(f"[ERROR] ไม่พบไฟล์: {file_path}")
        return []
    except Exception as e:
        print(f"[ERROR] เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description="DekDataset: ดึงความคิดเห็นจาก social media platforms"
    )
    
    parser.add_argument(
        "platform",
        choices=["facebook", "twitter", "x", "youtube", "reddit", "pantip", "threads", "file"],
        help="Platform to extract from"
    )
    
    parser.add_argument(
        "query",
        nargs="*",  # Allow 0 or more URLs/queries when using --from_file
        help="URL, video ID, topic ID, or search query (can specify multiple or use --from_file)"
    )
    
    parser.add_argument(
        "--max_results",
        type=int,
        default=None,  # No limit by default
        help="Maximum number of comments to extract (default: unlimited)"
    )
    
    parser.add_argument(
        "--include_sentiment",
        action="store_true",
        help="Include sentiment analysis"
    )
    
    parser.add_argument(
        "--include_advanced_sentiment",
        action="store_true", 
        help="Include Advanced Thai Sentiment Analysis (emotion, intent, intensity, context)"
    )
    
    parser.add_argument(
        "--use_ml_sentiment",
        action="store_true",
        help="Use Machine Learning enhanced sentiment analysis (requires --include_advanced_sentiment)"
    )
    
    parser.add_argument(
        "--no_spam_filter",
        action="store_true",
        help="Disable spam filtering"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: auto-generated)"
    )
    
    parser.add_argument(
        "--format",
        choices=["jsonl", "csv", "txt"],
        default="jsonl",
        help="Output format (default: jsonl)"
    )
    
    parser.add_argument(
        "--lang",
        type=str,
        default="th",
        help="Language filter (default: th)"
    )
    
    parser.add_argument(
        "--time_filter",
        choices=["hour", "day", "week", "month", "year", "all"],
        default="week",
        help="Time filter for Reddit (default: week)"
    )
    
    parser.add_argument(
        "--from_file",
        type=str,
        help="Read URLs from text file (one URL per line, # for comments)"
    )
    
    args = parser.parse_args()

    # Validation: ML sentiment requires advanced sentiment
    if args.use_ml_sentiment and not args.include_advanced_sentiment:
        print("[ERROR] --use_ml_sentiment requires --include_advanced_sentiment")
        print("Please use both options together:")
        print("  --include_advanced_sentiment --use_ml_sentiment")
        return

    # Handle URLs from file or command line
    queries = []
    if args.from_file:
        # Read URLs from file
        file_queries = read_urls_from_file(args.from_file)
        if not file_queries:
            print("[ERROR] ไม่สามารถอ่าน URLs จากไฟล์ได้")
            return
        queries.extend(file_queries)
        print(f"[INFO] โหลด {len(file_queries)} URLs จากไฟล์")
        
        # Also add command line queries if provided
        if args.query:
            queries.extend(args.query)
            print(f"[INFO] เพิ่ม {len(args.query)} URLs จาก command line")
    else:
        # Use command line queries
        if not args.query:
            print("[ERROR] ไม่มี URLs หรือ queries ให้ประมวลผล")
            print("ใช้งาน:")
            print("  python get_comments.py PLATFORM URL1 URL2 ...")
            print("  python get_comments.py PLATFORM --from_file urls.txt")
            print("  python get_comments.py PLATFORM URL1 --from_file urls.txt")
            return
        queries = args.query

    if not queries:
        print("[ERROR] ไม่มี URLs หรือ queries ให้ประมวลผล")
        return

    # Handle multiple queries
    if len(queries) > 1:
        print(f"กำลังดึงข้อมูลจาก {args.platform} ({len(queries)} URLs/queries)...")
    else:
        print(f"กำลังดึงข้อมูลจาก {args.platform}...")
    
    # Start timing
    start_time = time.time()
    
    try:
        # Check if required dependencies are available
        if args.platform in ["facebook", "pantip", "twitter", "x", "threads"]:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                print("[ERROR] Playwright is required for this platform but not installed.")
                print("Please install it with: pip install playwright")
                print("Then run: playwright install chromium")
                return
        
        # Add timeout warning for Facebook
        if args.platform == "facebook":
            print("[WARNING] Facebook extraction includes privacy protection:")
            print("- Personal information (phone, email, Line ID) will be anonymized")
            print("- URLs and author names will be redacted")  
            print("- May timeout due to anti-bot detection")
            print("- Consider using existing data instead")
            print("Trying with reduced timeout...")
        
        # Extract comments (pass list of queries)
        comments = extract_social_media_comments(
            platform=args.platform,
            query=queries,  # Pass the list of queries
            max_results=args.max_results,
            include_sentiment=args.include_sentiment,
            include_advanced_sentiment=args.include_advanced_sentiment,
            use_ml_sentiment=args.use_ml_sentiment,  # Add ML option
            filter_spam=not args.no_spam_filter,
            silent=False,
            lang=args.lang,
            time_filter=args.time_filter
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        print(f"ดึงข้อมูลได้ {len(comments)} ความคิดเห็น ใช้เวลา {elapsed_time:.1f} วินาที")
        
        if not comments:
            print("ไม่พบข้อมูลความคิดเห็น")
            print(f"Tips for {args.platform}:")
            if args.platform == "facebook":
                print("- Facebook มีการป้องกัน bot สูงมาก")
                print("- URL ต้องเป็น public post เท่านั้น")
                print("- ข้อมูลส่วนตัวจะถูก anonymize เพื่อความปลอดภัย")
                print("- แนะนำใช้ YouTube หรือ Pantip แทน เพราะมีข้อมูลมากกว่า")
                print("- Facebook blocking ตรวจพบ automation tools")
                
                # Show existing data with privacy note
                print(f"\nข้อมูล Facebook ที่มีอยู่แล้ว (ปลอดภัย):")
                print("- data/facebook_comments.jsonl (10 comments)")
                print("- เนื้อหาเกี่ยวกับความคิดเห็นส่วนตัว (anonymized)")
                print("- สามารถใช้ได้ทันทีโดยไม่ต้องดึงใหม่")
                print("- ข้อมูลส่วนตัวได้รับการปกป้อง")

            elif args.platform == "pantip":
                print("- ตรวจสอบว่า topic ID ถูกต้อง (เช่น 43494778)")
                print("- หรือใช้ URL เต็ม https://pantip.com/topic/43494778")
                print("- ลองโพสต์ที่มีความคิดเห็นเยอะกว่า")
            elif args.platform == "youtube":
                print("- ตรวจสอบว่า video มี comments เปิดให้")
                print("- ใช้ URL เต็ม https://www.youtube.com/watch?v=VIDEO_ID")
                print("- ลองวิดีโอยอดนิยมที่มี comments เยอะ")
            
            # Show successful examples from existing data files
            print(f"\nตัวอย่าง URL/ID ที่ทำงานได้:")
            if args.platform == "youtube":
                print("- K150FJzooLM หรือ https://www.youtube.com/watch?v=K150FJzooLM")
                print("  (เรื่องหลวงพ่อแย้ม - ได้ 20 comments)")
            elif args.platform == "pantip":
                print("- 43494778 (ปัญหาเน็ต TRUE - ได้ 10 comments)")
                print("- https://pantip.com/topic/43494778")
            elif args.platform == "facebook":
                print("- ข้อมูลที่มีอยู่: data/facebook_comments.jsonl")
                print("- Facebook detection ป้องกันการดึงข้อมูลใหม่")
            
            return
        
        # Generate output filename if not provided
        if not args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("data")
            output_dir.mkdir(exist_ok=True)
            
            # Add suffix for multiple sources
            if len(queries) > 1:
                filename = f"{args.platform}_comments_{len(queries)}sources_{timestamp}.{args.format}"
            else:
                filename = f"{args.platform}_comments_{timestamp}.{args.format}"
            
            args.output = output_dir / filename
        
        # Save comments (only once)
        saved_path = save_comments_for_training(
            comments=comments,
            output_path=str(args.output),
            format=args.format,
            exclude_spam=not args.no_spam_filter,
            save_spam_separately=True
        )
        
        if saved_path:
            print(f"บันทึกข้อมูลสำเร็จ: {saved_path}")
            
            # Show sample data
            show_sample_data(comments)
            
            # Show statistics
            if args.include_sentiment or args.include_advanced_sentiment:
                sentiment_counts = {}
                ml_stats = {"ml_enhanced": 0, "rule_based": 0}
                
                for comment in comments:
                    sentiment = comment.get("sentiment", "unknown")
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                    
                    # Count ML vs rule-based
                    if args.use_ml_sentiment and comment.get("ml_enhanced", False):
                        ml_stats["ml_enhanced"] += 1
                    else:
                        ml_stats["rule_based"] += 1
                
                print("\nสถิติ sentiment:")
                for sentiment, count in sentiment_counts.items():
                    print(f"  {sentiment}: {count}")
                
                # Show ML statistics if ML was used
                if args.use_ml_sentiment:
                    print(f"\nสถิติ ML enhancement:")
                    print(f"  ML-enhanced: {ml_stats['ml_enhanced']}")
                    print(f"  Rule-based fallback: {ml_stats['rule_based']}")
                    if ml_stats['ml_enhanced'] > 0:
                        accuracy_rate = (ml_stats['ml_enhanced'] / len(comments)) * 100
                        print(f"  ML success rate: {accuracy_rate:.1f}%")
            
            # Show platform breakdown
            platform_counts = {}
            source_counts = {}
            for comment in comments:
                platform = comment.get("platform", "unknown")
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                # Count by source if multiple queries
                if len(queries) > 1:
                    source = comment.get("source_query", "unknown")
                    # Truncate long URLs for display
                    if len(source) > 50:
                        source = source[:47] + "..."
                    source_counts[source] = source_counts.get(source, 0) + 1
            
            print("\nสถิติ platform:")
            for platform, count in platform_counts.items():
                print(f"  {platform}: {count}")
            
            # Show source breakdown for multiple queries
            if len(queries) > 1 and source_counts:
                print("\nสถิติแยกตาม source:")
                for source, count in source_counts.items():
                    print(f"  {source}: {count}")
                print(f"  รวม {len(queries)} sources")
                
        else:
            print("เกิดข้อผิดพลาดในการบันทึกข้อมูล")
            
    except KeyboardInterrupt:
        print(f"\n[INFO] การดึงข้อมูลถูกยกเลิกโดยผู้ใช้")
        return
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
        print(f"[DEBUG] Error details: {type(e).__name__}: {str(e)}")
        
        # Suggest alternatives based on platform
        if args.platform == "facebook":
            print("\n[SUGGESTION] Facebook มีปัญหาในการดึงข้อมูล แนะนำ:")
            print("1. ใช้ข้อมูลที่มีอยู่: data/facebook_comments.jsonl (ปลอดภัย)")
            print("2. ลองใช้ YouTube แทน: python src/python/get_comments.py youtube VIDEO_URL")
            print("3. ลองใช้ Pantip แทน: python src/python/get_comments.py pantip TOPIC_ID")
            print("4. Facebook มี privacy protection และ anti-bot สูง")

        sys.exit(1)

if __name__ == "__main__":
    main()
