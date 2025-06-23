#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ตัวอย่างการใช้งาน Advanced Thai Sentiment Analysis
"""

import json
from social_media_utils import (
    advanced_thai_sentiment_analysis,
    batch_advanced_sentiment_analysis,
    save_advanced_sentiment_data,
    demo_advanced_sentiment
)

def example_single_text_analysis():
    """ตัวอย่างการวิเคราะห์ข้อความเดี่ยว"""
    print("🔍 Single Text Analysis")
    print("=" * 50)
    
    texts = [
        "ห่วยแตก! ร้านนี้ไม่ควรเปิดเลย",
        "อ่อ... ดีจริง ๆ เนอะ",
        "ช่วยหน่อยนะคะ งานต้องส่งพรุ่งนี้",
        "ดีจังเลย วันนี้เหนื่อยมาก แต่ยังได้กินของอร่อย",
        "โคตรดีเลย! สุดยอดมาก ชอบมาก 555"
    ]
    
    for text in texts:
        result = advanced_thai_sentiment_analysis(text)
        print(f"\nข้อความ: {text}")
        print(f"อารมณ์: {result['emotion']}")
        print(f"เจตนา: {result['intent']}")
        print(f"ความเข้ม: {result['intensity']}")
        print(f"บริบท: {result['context']}")
        print(f"คะแนน: {result['sentiment_score']}")
        if result['target']:
            print(f"เป้าหมาย: {result['target']}")
        print("-" * 30)

def example_batch_analysis():
    """ตัวอย่างการวิเคราะห์แบบ batch"""
    print("\n📦 Batch Analysis")
    print("=" * 50)
    
    # สร้างข้อมูลตัวอย่าง
    sample_comments = [
        {"text": "ห่วยแตก! ร้านนี้ไม่ควรเปิดเลย", "author": "User1"},
        {"text": "อ่อ... ดีจริง ๆ เนอะ", "author": "User2"},
        {"text": "ช่วยหน่อยนะคะ งานต้องส่งพรุ่งนี้", "author": "User3"},
        {"text": "โคตรดีเลย! สุดยอดมาก", "author": "User4"}
    ]
    
    # วิเคราะห์แบบ batch
    analyzed_comments = batch_advanced_sentiment_analysis(sample_comments)
    
    # แสดงผล
    for comment in analyzed_comments:
        print(f"ข้อความ: {comment['text']}")
        print(f"อารมณ์: {comment['emotion']} | เจตนา: {comment['intent']}")
        print(f"คะแนน: {comment['sentiment_score']}")
        print("-" * 30)
    
    # บันทึกลงไฟล์
    output_file = "analyzed_comments.jsonl"
    save_advanced_sentiment_data(analyzed_comments, output_file, "jsonl")
    print(f"✅ บันทึกผลการวิเคราะห์ลง: {output_file}")

def example_social_media_extraction_with_analysis():
    """ตัวอย่างการดึงข้อมูลจาก Social Media พร้อมวิเคราะห์ sentiment"""
    print("\n🌐 Social Media + Advanced Sentiment")
    print("=" * 50)
    
    # ตัวอย่าง URL (ใช้ข้อมูลจำลอง)
    # สามารถแทนที่ด้วย URL จริงของ Twitter, Facebook, etc.
    
    # สร้างข้อมูลจำลอง
    mock_comments = [
        {
            "text": "ร้านนี้อาหารอร่อยมาก บริการดีด้วย ประทับใจ",
            "platform": "facebook",
            "author": "customer1"
        },
        {
            "text": "ห่วยแตก! รอนานมาก แล้วอาหารยังไม่อร่อย",
            "platform": "facebook", 
            "author": "customer2"
        },
        {
            "text": "อ่อ... เจ๋งจริงๆ เนอะ ร้านนี้ 555",
            "platform": "twitter",
            "author": "customer3"
        }
    ]
    
    # วิเคราะห์ sentiment แบบขั้นสูง
    analyzed_data = batch_advanced_sentiment_analysis(mock_comments)
    
    # แสดงผลแบบสรุป
    emotion_count = {}
    for comment in analyzed_data:
        emotion = comment['emotion']
        emotion_count[emotion] = emotion_count.get(emotion, 0) + 1
    
    print("📊 สรุปอารมณ์:")
    for emotion, count in emotion_count.items():
        print(f"  {emotion}: {count} ความคิดเห็น")
    
    # บันทึกผลการวิเคราะห์
    save_advanced_sentiment_data(analyzed_data, "social_media_sentiment.jsonl")
    
    return analyzed_data

def example_json_output():
    """ตัวอย่าง JSON Output ตาม Schema"""
    print("\n📄 JSON Schema Example")
    print("=" * 50)
    
    text = "อ่อ... ดีจริง ๆ เนอะ"
    result = advanced_thai_sentiment_analysis(text)
    
    # แสดง JSON ที่สวยงาม
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    # รันตัวอย่างทั้งหมด
    example_single_text_analysis()
    example_batch_analysis()
    example_social_media_extraction_with_analysis()
    example_json_output()
    
    # รัน demo
    print("\n" + "="*60)
    demo_advanced_sentiment()
