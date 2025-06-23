#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน Multiple URLs/Queries Extraction
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from social_media_utils import extract_social_media_comments, save_comments_for_training

def example_multiple_youtube_videos():
    """ตัวอย่างการดึงจาก YouTube หลายวิดีโอ"""
    print("=== ตัวอย่าง: YouTube หลายวิดีโอ ===")
    
    youtube_urls = [
        "https://www.youtube.com/watch?v=K150FJzooLM",  # หลวงพ่อแย้ม
        "K150FJzooLM",  # Same video, different format
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"   # Rick Roll (example)
    ]
    
    comments = extract_social_media_comments(
        platform="youtube",
        query=youtube_urls,
        max_results=50,
        include_advanced_sentiment=True,
        silent=False
    )
    
    print(f"\nได้รับ {len(comments)} comments จาก {len(youtube_urls)} วิดีโอ")
    
    # แสดงตัวอย่าง
    for i, comment in enumerate(comments[:3]):
        print(f"\n[{i+1}] {comment.get('text', '')[:100]}...")
        print(f"    Source: {comment.get('source_query', 'Unknown')}")
        if 'emotion' in comment:
            print(f"    Emotion: {comment['emotion']}")
        if 'intensity' in comment:
            print(f"    Intensity: {comment['intensity']}")
    
    return comments

def example_multiple_pantip_topics():
    """ตัวอย่างการดึงจาก Pantip หลายกระทู้"""
    print("\n=== ตัวอย่าง: Pantip หลายกระทู้ ===")
    
    pantip_topics = [
        "43494778",  # ปัญหาเน็ต TRUE
        "https://pantip.com/topic/43494778",  # Same topic, different format
        "43123456"   # Example topic (may not exist)
    ]
    
    comments = extract_social_media_comments(
        platform="pantip",
        query=pantip_topics,
        max_results=30,
        include_sentiment=True,
        silent=False
    )
    
    print(f"\nได้รับ {len(comments)} comments จาก {len(pantip_topics)} กระทู้")
    
    # แสดงตัวอย่าง
    for i, comment in enumerate(comments[:3]):
        print(f"\n[{i+1}] {comment.get('text', '')[:100]}...")
        print(f"    Source: {comment.get('source_query', 'Unknown')}")
        print(f"    Sentiment: {comment.get('sentiment', 'Unknown')}")
    
    return comments

def example_multiple_files():
    """ตัวอย่างการโหลดจากไฟล์หลายไฟล์"""
    print("\n=== ตัวอย่าง: โหลดจากหลายไฟล์ ===")
    
    # สร้างไฟล์ตัวอย่าง
    test_files = []
    
    # ไฟล์ 1
    file1 = Path("test_comments_1.jsonl")
    with open(file1, "w", encoding="utf-8") as f:
        f.write('{"text": "ความคิดเห็นจากไฟล์ 1", "platform": "test"}\n')
        f.write('{"text": "อีกความคิดเห็นจากไฟล์ 1", "platform": "test"}\n')
    test_files.append(str(file1))
    
    # ไฟล์ 2  
    file2 = Path("test_comments_2.jsonl")
    with open(file2, "w", encoding="utf-8") as f:
        f.write('{"text": "ความคิดเห็นจากไฟล์ 2", "platform": "test"}\n')
        f.write('{"text": "ข้อมูลจากไฟล์ที่สอง", "platform": "test"}\n')
    test_files.append(str(file2))
    
    try:
        comments = extract_social_media_comments(
            platform="file",
            query=test_files,
            max_results=50,
            include_advanced_sentiment=True,
            silent=False
        )
        
        print(f"\nได้รับ {len(comments)} comments จาก {len(test_files)} ไฟล์")
        
        # แสดงตัวอย่าง
        for i, comment in enumerate(comments):
            print(f"\n[{i+1}] {comment.get('text', '')}")
            print(f"    Source: {comment.get('source_query', 'Unknown')}")
            if 'emotion' in comment:
                print(f"    Emotion: {comment['emotion']}")
        
        return comments
        
    finally:
        # ลบไฟล์ทดสอบ
        for file_path in test_files:
            try:
                Path(file_path).unlink()
            except:
                pass

def example_save_multiple_results():
    """ตัวอย่างการบันทึกผลลัพธ์จากหลาย sources"""
    print("\n=== ตัวอย่าง: บันทึกผลจากหลาย Sources ===")
    
    # ดึงจากหลาย sources
    youtube_urls = [
        "K150FJzooLM",  # หลวงพ่อแย้ม
        "dQw4w9WgXcQ"   # Rick Roll
    ]
    
    comments = extract_social_media_comments(
        platform="youtube",
        query=youtube_urls,
        max_results=20,
        include_advanced_sentiment=True,
        silent=False
    )
    
    if comments:
        # บันทึกในรูปแบบต่างๆ
        output_dir = Path("data")
        output_dir.mkdir(exist_ok=True)
        
        # JSONL
        jsonl_path = save_comments_for_training(
            comments, 
            str(output_dir / "multiple_sources_example.jsonl"),
            "jsonl",
            exclude_spam=True
        )
        
        # CSV
        csv_path = save_comments_for_training(
            comments, 
            str(output_dir / "multiple_sources_example.csv"),
            "csv",
            exclude_spam=True
        )
        
        print(f"\nบันทึกไฟล์สำเร็จ:")
        print(f"- JSONL: {jsonl_path}")
        print(f"- CSV: {csv_path}")
        
        # แสดงสถิติ
        source_counts = {}
        for comment in comments:
            source = comment.get("source_query", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print(f"\nสถิติแยกตาม source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count} comments")

def main():
    """รันตัวอย่างทั้งหมด"""
    print("🔥 ตัวอย่างการใช้งาน Multiple URLs/Queries Extraction 🔥")
    print("=" * 60)
    
    try:
        # ตัวอย่าง 1: YouTube หลายวิดีโอ
        youtube_comments = example_multiple_youtube_videos()
        
        # ตัวอย่าง 2: Pantip หลายกระทู้  
        pantip_comments = example_multiple_pantip_topics()
        
        # ตัวอย่าง 3: หลายไฟล์
        file_comments = example_multiple_files()
        
        # ตัวอย่าง 4: บันทึกผลลัพธ์
        example_save_multiple_results()
        
        print("\n" + "=" * 60)
        print("✅ ทดสอบเสร็จสิ้น!")
        print("💡 ตอนนี้คุณสามารถใช้ CLI ดังนี้:")
        print("   python get_comments.py youtube URL1 URL2 URL3 --include_advanced_sentiment")
        print("   python get_comments.py pantip TOPIC1 TOPIC2 --max_results 100")
        print("   python get_comments.py file file1.jsonl file2.jsonl --format csv")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    main()
