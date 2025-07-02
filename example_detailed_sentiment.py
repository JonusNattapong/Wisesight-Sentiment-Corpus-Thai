#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of Detailed Thai Sentiment Analysis System
ตัวอย่างการใช้งานระบบ sentiment analysis ภาษาไทยแบบละเอียด
"""

import json
from detailed_thai_sentiment import (
    DetailedThaiSentimentAnalyzer,
    create_training_data_format,
    save_training_data,
    EMOTION_LABELS,
    EMOTION_GROUPS
)

def example_basic_usage():
    """ตัวอย่างการใช้งานพื้นฐาน"""
    print("🚀 Basic Usage Example")
    print("=" * 50)
    
    # สร้าง analyzer
    analyzer = DetailedThaiSentimentAnalyzer()
    
    # ทดสอบข้อความต่างๆ
    test_texts = [
        "โกรธจนขำอะ! ทำไมต้องมาแบบนี้ด้วย 555",
        "ดีใจมากเลย รักเธอที่สุด ❤️😍",
        "เสียใจมากเลย ผิดหวังจริงๆ",
        "ข้อมูลข่าวสารวันนี้ สถานการณ์ปกติดี",
        "อ่อ... ดีจริงๆ เนอะ ประชดเก่งจัง 🙄"
    ]
    
    print("\n📍 Single Label Analysis:")
    for text in test_texts:
        result = analyzer.analyze_single_label(text)
        print(f"ข้อความ: {text}")
        print(f"→ อารมณ์: {result['label']} (กลุ่ม: {result['group']}, ความมั่นใจ: {result['confidence']})")
        print()
    
    print("\n📍 Multi-Label Analysis:")
    for text in test_texts:
        result = analyzer.analyze_multi_label(text, threshold=0.25)
        print(f"ข้อความ: {text}")
        print(f"→ อารมณ์: {result['labels']} (กลุ่ม: {result['groups']})")
        print()

def example_batch_processing():
    """ตัวอย่างการประมวลผลแบบ batch"""
    print("📦 Batch Processing Example")
    print("=" * 50)
    
    analyzer = DetailedThaiSentimentAnalyzer()
    
    # ข้อมูลตัวอย่างจำนวนมาก
    sample_comments = [
        "สุดยอดมากเลย ชอบมาก! 😍",
        "ห่วยแตกจริงๆ ไม่ควรซื้อเลย",
        "โอเค ปกติดี ใช้ได้",
        "โกรธมากเลย แต่ก็ขำดี 555",
        "เศร้าใจมาก ผิดหวังจริงๆ 😢",
        "ประชดเก่งมาก เสียดสีเป็นเลิศ 🙄",
        "ข่าวสารประจำวัน อัปเดตสถานการณ์",
        "สับสนมาก เข้าใจไม่ได้เลย 🤔",
        "กลัวมากเลย ตกใจจริงๆ 😱",
        "รำคาญแล้ว เบื่อมากเลย 😤"
    ]
    
    # วิเคราะห์แบบ single label
    print("\n🏷️ Single Label Results:")
    single_results = analyzer.analyze_batch(sample_comments, multi_label=False)
    
    for i, result in enumerate(single_results):
        print(f"{i+1}. {result['text']}")
        print(f"   → {result['label']} ({result['group']}) - มั่นใจ: {result['confidence']}")
    
    # วิเคราะห์แบบ multi-label
    print("\n🏷️ Multi-Label Results:")
    multi_results = analyzer.analyze_batch(sample_comments, multi_label=True, threshold=0.2)
    
    for i, result in enumerate(multi_results):
        print(f"{i+1}. {result['text']}")
        print(f"   → {result['labels']} ({result['groups']})")
    
    # แสดงสถิติ
    print("\n📊 Statistics:")
    single_stats = analyzer.get_emotion_statistics(single_results)
    multi_stats = analyzer.get_emotion_statistics(multi_results)
    
    print(f"Single Label - Top emotions: {sorted(single_stats['emotion_counts'].items(), key=lambda x: x[1], reverse=True)}")
    print(f"Multi Label - Top emotions: {sorted(multi_stats['emotion_counts'].items(), key=lambda x: x[1], reverse=True)}")

def example_training_data_creation():
    """ตัวอย่างการสร้างข้อมูลสำหรับ training model"""
    print("🎓 Training Data Creation Example")
    print("=" * 50)
    
    # ข้อมูลตัวอย่างพร้อม labels
    sample_data = [
        # Single label examples
        {"text": "ดีใจมากเลย! สุดยอด", "label": "ดีใจ"},
        {"text": "โกรธมากเลย แย่จริงๆ", "label": "โกรธ"},
        {"text": "เศร้าใจมาก ผิดหวัง", "label": "เสียใจ"},
        {"text": "ข้อมูลข่าวสารประจำวัน", "label": "ข้อมูลข่าวสาร"},
        
        # Multi-label examples
        {"text": "โกรธจนขำอะ! แปลกดี 555", "labels": ["โกรธ", "ขำขัน"]},
        {"text": "ประชดเก่งมาก เสียดสีจนเศร้า", "labels": ["ประชด", "เสียใจ"]},
        {"text": "ชอบมาก แต่ก็ผิดหวังนิดหน่อย", "labels": ["ชอบ", "ผิดหวัง"]},
        {"text": "สับสนมาก กลัวด้วย", "labels": ["สับสน", "กลัว"]}
    ]
    
    # สร้างข้อมูลสำหรับ traditional ML models
    print("\n🤖 For Traditional ML Models (BERT, RoBERTa, etc.):")
    ml_training_data = []
    
    for item in sample_data:
        if "label" in item:  # Single label
            formatted = create_training_data_format(item["text"], item["label"], "classification")
        else:  # Multi label
            formatted = create_training_data_format(item["text"], item["labels"], "classification")
        
        ml_training_data.append(formatted)
        print(json.dumps(formatted, ensure_ascii=False, indent=2))
        print()
    
    # สร้างข้อมูลสำหรับ LLM fine-tuning
    print("\n🧠 For LLM Fine-tuning:")
    llm_training_data = []
    
    for item in sample_data:
        if "label" in item:  # Single label
            formatted = create_training_data_format(item["text"], item["label"], "instruction")
        else:  # Multi label
            formatted = create_training_data_format(item["text"], item["labels"], "instruction")
        
        llm_training_data.append(formatted)
        print(json.dumps(formatted, ensure_ascii=False, indent=2))
        print()
    
    # บันทึกข้อมูล
    save_training_data(ml_training_data, "ml_training_data.jsonl", "jsonl")
    save_training_data(llm_training_data, "llm_training_data.jsonl", "jsonl")
    
    print("✅ Training data saved!")
    print("📁 ml_training_data.jsonl - สำหรับ traditional ML models")
    print("📁 llm_training_data.jsonl - สำหรับ LLM fine-tuning")

def example_social_media_analysis():
    """ตัวอย่างการวิเคราะห์ข้อมูล social media"""
    print("📱 Social Media Analysis Example")
    print("=" * 50)
    
    analyzer = DetailedThaiSentimentAnalyzer()
    
    # จำลองข้อมูล social media comments
    social_media_comments = [
        {
            "platform": "facebook",
            "post_id": "123456",
            "comment": "ร้านนี้อาหารอร่อยมาก บริการดีด้วย ประทับใจจริงๆ 😍",
            "author": "user1",
            "timestamp": "2025-07-02T10:30:00"
        },
        {
            "platform": "twitter",
            "post_id": "789012",
            "comment": "อ้าว... ดีจริงๆ เนอะ บริการแบบนี้ 🙄 #ประชด",
            "author": "user2", 
            "timestamp": "2025-07-02T11:15:00"
        },
        {
            "platform": "youtube",
            "post_id": "345678",
            "comment": "โกรธจนขำอะ! คลิปนี้ตลกดีแต่ก็น่าหงุดหงิด 555",
            "author": "user3",
            "timestamp": "2025-07-02T12:00:00"
        },
        {
            "platform": "pantip",
            "post_id": "901234",
            "comment": "ข้อมูลดีครับ ขอบคุณสำหรับการแชร์",
            "author": "user4",
            "timestamp": "2025-07-02T13:45:00"
        }
    ]
    
    # วิเคราะห์ sentiment สำหรับแต่ละ comment
    print("\n📊 Analysis Results:")
    analyzed_comments = []
    
    for comment_data in social_media_comments:
        # Single label analysis
        single_result = analyzer.analyze_single_label(comment_data["comment"])
        
        # Multi-label analysis  
        multi_result = analyzer.analyze_multi_label(comment_data["comment"], threshold=0.25)
        
        # รวมข้อมูล
        analyzed_comment = {
            **comment_data,
            "single_label_analysis": single_result,
            "multi_label_analysis": multi_result
        }
        
        analyzed_comments.append(analyzed_comment)
        
        print(f"Platform: {comment_data['platform']}")
        print(f"Comment: {comment_data['comment']}")
        print(f"Single Label: {single_result['label']} (กลุ่ม: {single_result['group']}, มั่นใจ: {single_result['confidence']})")
        print(f"Multi Label: {multi_result['labels']} (กลุ่ม: {multi_result['groups']})")
        print(f"Context: {single_result['context']}")
        print("-" * 50)
    
    # สรุปสถิติแยกตาม platform
    print("\n📈 Platform Statistics:")
    platform_stats = {}
    
    for comment in analyzed_comments:
        platform = comment["platform"]
        if platform not in platform_stats:
            platform_stats[platform] = {"comments": 0, "emotions": []}
        
        platform_stats[platform]["comments"] += 1
        platform_stats[platform]["emotions"].extend(comment["multi_label_analysis"]["labels"])
    
    for platform, stats in platform_stats.items():
        emotion_counts = {}
        for emotion in stats["emotions"]:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        print(f"{platform}: {stats['comments']} comments")
        print(f"  Top emotions: {sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)}")
    
    # บันทึกผลการวิเคราะห์
    with open("social_media_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(analyzed_comments, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Results saved to: social_media_analysis_results.json")

def example_advanced_features():
    """ตัวอย่างฟีเจอร์ขั้นสูง"""
    print("🎯 Advanced Features Example")
    print("=" * 50)
    
    analyzer = DetailedThaiSentimentAnalyzer()
    
    # ปรับ threshold สำหรับ multi-label
    test_text = "โกรธมากเลย แต่ก็ขำดีนะ ประชดเก่งจัง 555 😡😂"
    
    print(f"ข้อความทดสอบ: {test_text}")
    print("\n🎚️ Different Threshold Results:")
    
    for threshold in [0.1, 0.2, 0.3, 0.4, 0.5]:
        result = analyzer.analyze_multi_label(test_text, threshold=threshold)
        print(f"Threshold {threshold}: {result['labels']} (จำนวน: {len(result['labels'])})")
    
    # แสดงคะแนนทั้งหมด
    detailed_result = analyzer.analyze_multi_label(test_text, threshold=0.2)
    print(f"\n📊 Detailed Scores:")
    sorted_scores = sorted(detailed_result["scores"].items(), key=lambda x: x[1], reverse=True)
    for emotion, score in sorted_scores:
        if score > 0:
            group = LABEL_TO_GROUP.get(emotion, "Unknown")
            print(f"  {emotion} ({group}): {score}")
    
    # ทดสอบบริบทต่างๆ
    context_tests = [
        "ขอบคุณครับ สำหรับข้อมูลดีๆ",  # formal
        "เจ๋งมากเลย บินแล้ว! 555",      # slang
        "โอเค นะคะ ไม่เป็นไรเลย",      # informal  
        "ผมคิดว่าเรื่องนี้สำคัญมาก"    # personal
    ]
    
    print(f"\n🗣️ Context Detection:")
    for text in context_tests:
        result = analyzer.analyze_single_label(text)
        print(f"'{text}' → Context: {result['context']}")

def show_supported_emotions():
    """แสดงรายการอารมณ์ที่รองรับ"""
    print("📝 Supported Emotions and Groups")
    print("=" * 50)
    
    print(f"จำนวนอารมณ์ที่รองรับทั้งหมด: {len(EMOTION_LABELS)} อารมณ์")
    print()
    
    for group, emotions in EMOTION_GROUPS.items():
        print(f"📂 {group}:")
        for emotion in emotions:
            print(f"   • {emotion}")
        print()
    
    print("💡 Tips:")
    print("   • ใช้ single label สำหรับ classification ทั่วไป")
    print("   • ใช้ multi-label สำหรับข้อความที่มีอารมณ์ผสม")
    print("   • ปรับ threshold ตามความต้องการความละเอียด")
    print("   • ตรวจสอบ confidence score เพื่อความน่าเชื่อถือ")

if __name__ == "__main__":
    print("🎯 Detailed Thai Sentiment Analysis - Examples")
    print("=" * 60)
    
    # แสดงรายการอารมณ์ที่รองรับ
    show_supported_emotions()
    print("\n" + "="*60 + "\n")
    
    # รันตัวอย่างต่างๆ
    example_basic_usage()
    print("\n" + "="*60 + "\n")
    
    example_batch_processing()
    print("\n" + "="*60 + "\n")
    
    example_training_data_creation()
    print("\n" + "="*60 + "\n")
    
    example_social_media_analysis()
    print("\n" + "="*60 + "\n")
    
    example_advanced_features()
    
    print("\n🎉 All examples completed!")
    print("📚 Check generated files:")
    print("   • ml_training_data.jsonl")
    print("   • llm_training_data.jsonl")
    print("   • social_media_analysis_results.json")
