#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean test script for sentiment analysis
"""

import sys
import os

# เพิ่ม path ปัจจุบันเข้าไปใน sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sentiment_integration import analyze_detailed_sentiment, get_sentiment_statistics
    print("✅ Successfully imported sentiment_integration")
except Exception as e:
    print(f"❌ Error importing sentiment_integration: {e}")
    sys.exit(1)

def test_basic_functionality():
    """ทดสอบฟังก์ชันพื้นฐาน"""
    print("\n🔍 Testing Basic Functionality")
    print("=" * 50)
    
    test_cases = [
        "สวัสดีครับ ดีใจที่ได้พบ",
        "ห่วยแตกมาก ไม่ชอบเลย",
        "ข้อมูลข่าวสารประจำวัน",
        "เยี่ยมมากครับ... ถ้าชอบความล้มเหลว 🙄"
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {text}")
        
        try:
            # Single label test
            result = analyze_detailed_sentiment(text, mode="single")
            print(f"   Single: {result['sentiment']} ({result['detailed_emotion']})")
            print(f"   Confidence: {result['confidence']:.2f}")
            
            # Multi label test
            result_multi = analyze_detailed_sentiment(text, mode="multi")
            print(f"   Multi: {result_multi['sentiment']} ({result_multi['detailed_emotions']})")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_social_media():
    """ทดสอบฟังก์ชัน social media"""
    print("\n📱 Testing Social Media Analysis")
    print("=" * 50)
    
    from sentiment_integration import analyze_social_media_batch
    
    sample_comments = [
        {"text": "รักเลย ❤️", "author": "user1", "platform": "facebook"},
        {"text": "แย่มาก ไม่ชอบ", "author": "user2", "platform": "twitter"},
        {"text": "ธรรมดา ไม่มีอะไรพิเศษ", "author": "user3", "platform": "youtube"}
    ]
    
    try:
        results = analyze_social_media_batch(
            sample_comments, 
            mode="single", 
            show_progress=False
        )
        
        for comment in results:
            print(f"Platform: {comment['platform']}")
            print(f"Text: {comment['text']}")
            print(f"Sentiment: {comment['sentiment']}")
            print(f"Detailed: {comment['sentiment_analysis']['detailed_emotion']}")
            print()
            
        # สถิติ
        stats = get_sentiment_statistics(results)
        print(f"📊 Total comments: {stats['total_comments']}")
        print(f"📊 Sentiment distribution: {stats['sentiment_counts']}")
        
    except Exception as e:
        print(f"❌ Error in social media analysis: {e}")

if __name__ == "__main__":
    print("🚀 Starting Clean Sentiment Analysis Test")
    
    test_basic_functionality()
    test_social_media()
    
    print("\n✅ Test completed successfully!")
