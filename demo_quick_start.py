#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Demo: Detailed Thai Sentiment Analysis
การสาธิตระบบ sentiment analysis ภาษาไทยแบบละเอียด
"""

def demo_quick_start():
    """Demo การใช้งานแบบเร็ว"""
    print("🚀 Quick Demo: Detailed Thai Sentiment Analysis")
    print("=" * 60)
    
    try:
        from detailed_thai_sentiment import DetailedThaiSentimentAnalyzer
        from sentiment_integration import analyze_detailed_sentiment
        
        # สร้าง analyzer
        analyzer = DetailedThaiSentimentAnalyzer()
        
        # ข้อมูลทดสอบ
        demo_texts = [
            "โกรธจนขำอะ! ทำไมต้องมาแบบนี้ด้วย 555 😡😂",
            "ดีใจมากเลย รักเธอที่สุดเลย ❤️😍", 
            "อ่อ... เยี่ยมจริงๆ เนอะ บริการดีมากเลย 🙄",
            "ข้อมูลข่าวสารประจำวันครับ สถานการณ์ปกติดี",
            "เศร้าใจมาก ผิดหวังจริงๆ 😢💔"
        ]
        
        print("\n📍 SINGLE-LABEL ANALYSIS (เลือก 1 อารมณ์):")
        print("-" * 50)
        
        for i, text in enumerate(demo_texts, 1):
            result = analyzer.analyze_single_label(text)
            print(f"{i}. ข้อความ: {text}")
            print(f"   → อารมณ์: {result['label']} (กลุ่ม: {result['group']})")
            print(f"   → ความมั่นใจ: {result['confidence']:.3f} | บริบท: {result['context']}")
            print()
        
        print("\n📍 MULTI-LABEL ANALYSIS (เลือกได้หลายอารมณ์):")
        print("-" * 50)
        
        for i, text in enumerate(demo_texts, 1):
            result = analyzer.analyze_multi_label(text, threshold=0.25)
            print(f"{i}. ข้อความ: {text}")
            print(f"   → อารมณ์: {result['labels']} (กลุ่ม: {result['groups']})")
            print(f"   → บริบท: {result['context']}")
            print()
        
        print("\n📍 INTEGRATION MODULE (เชื่อมต่อกับระบบเดิม):")
        print("-" * 50)
        
        for i, text in enumerate(demo_texts, 1):
            result = analyze_detailed_sentiment(text, mode="single", include_scores=True)
            print(f"{i}. ข้อความ: {text}")
            print(f"   → Basic Sentiment: {result['sentiment']}")
            print(f"   → Detailed Emotion: {result['detailed_emotion']} ({result['emotion_group']})")
            print(f"   → Confidence: {result['confidence']:.3f}")
            print()
        
        print("✅ Demo completed successfully!")
        print("\n📚 สำหรับการใช้งานเพิ่มเติม:")
        print("   • รัน: python example_detailed_sentiment.py")
        print("   • รัน: python test_detailed_sentiment.py")
        print("   • อ่าน: docs/DETAILED_SENTIMENT_README.md")
        
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\n💡 การแก้ไข:")
        print("   1. ตรวจสอบว่าไฟล์ detailed_thai_sentiment.py อยู่ในโฟลเดอร์เดียวกัน")
        print("   2. ตรวจสอบว่าไฟล์ sentiment_integration.py อยู่ในโฟลเดอร์เดียวกัน")
        print("   3. ติดตั้ง dependencies: pip install pandas tqdm")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def demo_supported_emotions():
    """แสดงรายการอารมณ์ที่รองรับ"""
    print("\n📝 Supported Emotions (รายการอารมณ์ที่รองรับ):")
    print("=" * 60)
    
    try:
        from detailed_thai_sentiment import EMOTION_GROUPS
        
        for group, emotions in EMOTION_GROUPS.items():
            emoji = {
                "Positive": "😊",
                "Negative": "😔", 
                "Neutral": "😐",
                "Others": "🤔"
            }.get(group, "📝")
            
            print(f"\n{emoji} {group}:")
            for emotion in emotions:
                print(f"   • {emotion}")
        
        print(f"\nรวมทั้งหมด: {sum(len(emotions) for emotions in EMOTION_GROUPS.values())} อารมณ์")
        
    except ImportError:
        print("❌ ไม่สามารถโหลดรายการอารมณ์ได้")

def demo_usage_examples():
    """แสดงตัวอย่างการใช้งาน"""
    print("\n💡 Usage Examples (ตัวอย่างการใช้งาน):")
    print("=" * 60)
    
    examples = [
        {
            "title": "1. การใช้งานพื้นฐาน",
            "code": """
from detailed_thai_sentiment import DetailedThaiSentimentAnalyzer

analyzer = DetailedThaiSentimentAnalyzer()
result = analyzer.analyze_single_label("ดีใจมาก!")
print(result['label'])  # → "ดีใจ"
"""
        },
        {
            "title": "2. การวิเคราะห์หลายอารมณ์",
            "code": """
result = analyzer.analyze_multi_label("โกรธจนขำอะ!", threshold=0.3)
print(result['labels'])  # → ["โกรธ", "ขำขัน"]
"""
        },
        {
            "title": "3. การใช้ Integration Module",
            "code": """
from sentiment_integration import analyze_detailed_sentiment

result = analyze_detailed_sentiment("เสียใจมาก", mode="single")
print(f"Basic: {result['sentiment']}")      # → "negative"
print(f"Detail: {result['detailed_emotion']}")  # → "เสียใจ"
"""
        },
        {
            "title": "4. การประมวลผลแบบ Batch",
            "code": """
texts = ["ดีใจ", "โกรธ", "เศร้า"]
results = analyzer.analyze_batch(texts, multi_label=True)
stats = analyzer.get_emotion_statistics(results)
"""
        },
        {
            "title": "5. การสร้างข้อมูล Training",
            "code": """
from detailed_thai_sentiment import create_training_data_format

# Single label
data = create_training_data_format("ดีใจมาก", "ดีใจ", "classification")

# Multi label  
data = create_training_data_format("โกรธจนขำ", ["โกรธ", "ขำขัน"], "classification")

# LLM format
data = create_training_data_format("ประชดเก่ง", "ประชด", "instruction")
"""
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}:")
        print(example['code'])

def demo_cli_usage():
    """แสดงการใช้งาน Command Line"""
    print("\n⚡ Command Line Usage (การใช้งาน CLI):")
    print("=" * 60)
    
    cli_examples = [
        {
            "desc": "Basic sentiment analysis",
            "cmd": "python app.py --sentiment-mode basic"
        },
        {
            "desc": "Enhanced sentiment (backward compatible)",  
            "cmd": "python app.py --sentiment-mode enhanced"
        },
        {
            "desc": "Detailed single-label analysis",
            "cmd": "python app.py --sentiment-mode detailed --detailed-mode single"
        },
        {
            "desc": "Detailed multi-label analysis",
            "cmd": "python app.py --sentiment-mode detailed --detailed-mode multi"
        },
        {
            "desc": "With privacy protection",
            "cmd": "python app.py --sentiment-mode detailed --privacy mask"
        },
        {
            "desc": "Custom input/output files",
            "cmd": "python app.py --links my_links.txt --output my_results.jsonl --sentiment-mode detailed"
        }
    ]
    
    for example in cli_examples:
        print(f"\n• {example['desc']}:")
        print(f"  {example['cmd']}")

if __name__ == "__main__":
    # รัน demo ทั้งหมด
    demo_quick_start()
    demo_supported_emotions()
    demo_usage_examples()
    demo_cli_usage()
    
    print("\n🎉 Demo สำเร็จ! ลองใช้งานระบบได้เลย")
    print("\n📖 สำหรับข้อมูลเพิ่มเติม:")
    print("   • python example_detailed_sentiment.py (ตัวอย่างครบถ้วน)")
    print("   • python test_detailed_sentiment.py (ทดสอบระบบ)")
    print("   • docs/DETAILED_SENTIMENT_README.md (คู่มือใช้งาน)")
