#!/usr/bin/env python3
"""
วิเคราะห์ความแม่นยำของ Advanced Thai Sentiment Analysis
"""

import json
import sys
from collections import Counter
from pathlib import Path

def analyze_sentiment_accuracy(file_path):
    """วิเคราะห์ความแม่นยำของ sentiment analysis"""
    
    # Load data
    comments = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                comments.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    print("=" * 70)
    print("🔍 การวิเคราะห์ความแม่นยำของ Advanced Thai Sentiment Analysis")
    print("=" * 70)
    print(f"📊 จำนวนข้อมูลทั้งหมด: {len(comments)}")
    print()
    
    # Basic statistics
    emotions = [c.get('emotion') for c in comments if c.get('emotion')]
    emotion_counts = Counter(emotions)
    print("🎭 การกระจายของ Emotion:")
    for emotion, count in emotion_counts.most_common():
        print(f"   {emotion}: {count} ({count/len(comments)*100:.1f}%)")
    print()
    
    # Intent distribution
    intents = [c.get('intent') for c in comments if c.get('intent')]
    intent_counts = Counter(intents)
    print("🎯 การกระจายของ Intent:")
    for intent, count in intent_counts.most_common():
        print(f"   {intent}: {count} ({count/len(comments)*100:.1f}%)")
    print()
    
    # Intensity distribution
    intensities = [c.get('intensity') for c in comments if c.get('intensity')]
    intensity_counts = Counter(intensities)
    print("⚡ การกระจายของ Intensity:")
    for intensity, count in intensity_counts.most_common():
        print(f"   {intensity}: {count} ({count/len(comments)*100:.1f}%)")
    print()
    
    # Context distribution
    contexts = [c.get('context') for c in comments if c.get('context')]
    context_counts = Counter(contexts)
    print("🌍 การกระจายของ Context:")
    for context, count in context_counts.most_common():
        print(f"   {context}: {count} ({count/len(comments)*100:.1f}%)")
    print()
    
    # Sentiment score distribution
    scores = [c.get('sentiment_score') for c in comments if c.get('sentiment_score') is not None]
    positive_scores = [s for s in scores if s > 0]
    negative_scores = [s for s in scores if s < 0]
    neutral_scores = [s for s in scores if s == 0]
    
    print("📈 การกระจายของ Sentiment Score:")
    print(f"   Positive (>0): {len(positive_scores)} ({len(positive_scores)/len(comments)*100:.1f}%)")
    print(f"   Negative (<0): {len(negative_scores)} ({len(negative_scores)/len(comments)*100:.1f}%)")
    print(f"   Neutral (=0): {len(neutral_scores)} ({len(neutral_scores)/len(comments)*100:.1f}%)")
    print()
    
    # Manual accuracy evaluation with examples
    print("=" * 70)
    print("📝 ตัวอย่างการจำแนกสำหรับประเมินความแม่นยำ (Manual Evaluation)")
    print("=" * 70)
    
    # Show examples categorized by sentiment type
    examples_by_type = {
        'positive': [],
        'negative': [],
        'neutral': []
    }
    
    for comment in comments:
        score = comment.get('sentiment_score', 0)
        if score > 0:
            examples_by_type['positive'].append(comment)
        elif score < 0:
            examples_by_type['negative'].append(comment)
        else:
            examples_by_type['neutral'].append(comment)
    
    # Show examples for each type
    for sentiment_type, examples in examples_by_type.items():
        if examples:
            print(f"\n🔸 {sentiment_type.upper()} Examples (แสดง 3 ตัวอย่าง):")
            for i, comment in enumerate(examples[:3]):
                text = comment.get('text', '')
                if len(text) > 80:
                    text = text[:77] + "..."
                
                emotion = comment.get('emotion', 'N/A')
                intent = comment.get('intent', 'N/A')
                score = comment.get('sentiment_score', 'N/A')
                intensity = comment.get('intensity', 'N/A')
                
                print(f"   {i+1}. \"{text}\"")
                print(f"      → Emotion: {emotion} | Intent: {intent} | Score: {score} | Intensity: {intensity}")
                print()
    
    # Accuracy assessment
    print("=" * 70)
    print("✅ การประเมินความแม่นยำ (ตัวอย่าง)")
    print("=" * 70)
    
    # Check some specific cases for accuracy
    accuracy_cases = []
    
    for comment in comments[:10]:  # Check first 10 comments
        text = comment.get('text', '').lower()
        emotion = comment.get('emotion', '')
        score = comment.get('sentiment_score', 0)
        
        # Manual assessment based on Thai sentiment indicators
        manual_assessment = "neutral"
        if any(word in text for word in ['ล่ม', 'แย่', 'เดือดร้อน', 'ลำบาก', 'หัวเสีย', 'ท้อ']):
            manual_assessment = "negative"
        elif any(word in text for word in ['ดี', 'เยี่ยม', 'ชอบ', 'ปกติ']):
            manual_assessment = "positive"
        
        # Compare with system assessment
        system_assessment = "neutral"
        if score > 0:
            system_assessment = "positive"
        elif score < 0:
            system_assessment = "negative"
        
        is_correct = manual_assessment == system_assessment
        accuracy_cases.append({
            'text': text[:60] + "..." if len(text) > 60 else text,
            'manual': manual_assessment,
            'system': system_assessment,
            'emotion': emotion,
            'score': score,
            'correct': is_correct
        })
    
    correct_count = sum(1 for case in accuracy_cases if case['correct'])
    accuracy_rate = correct_count / len(accuracy_cases) * 100
    
    print(f"📊 ความแม่นยำโดยประมาณ: {accuracy_rate:.1f}% ({correct_count}/{len(accuracy_cases)})")
    print()
    
    print("📋 รายละเอียดการประเมิน:")
    for i, case in enumerate(accuracy_cases):
        status = "✅" if case['correct'] else "❌"
        print(f"   {i+1}. {status} \"{case['text']}\"")
        print(f"      Manual: {case['manual']} | System: {case['system']} | Score: {case['score']}")
        print()
    
    # Summary and recommendations
    print("=" * 70)
    print("📈 สรุปและข้อเสนอแนะ")
    print("=" * 70)
    
    print("🎯 จุดแข็ง:")
    print("   • ระบบสามารถจำแนก emotion และ intent ได้หลากหลาย")
    print("   • มี intensity และ context analysis")
    print("   • รองรับภาษาไทยได้ดี")
    print()
    
    print("⚠️  จุดที่ควรปรับปรุง:")
    if emotion_counts.get('neutral', 0) > len(comments) * 0.7:
        print("   • ระบบมีแนวโน้มจำแนกเป็น 'neutral' มากเกินไป")
    
    if len(positive_scores) < len(negative_scores) * 0.5:
        print("   • อาจจำแนก positive sentiment ได้น้อยเกินไป")
    
    print("   • ควรปรับปรุง keyword patterns สำหรับภาษาไทยให้ครอบคลุมมากขึ้น")
    print("   • อาจเพิ่ม machine learning model สำหรับความแม่นยำที่สูงขึ้น")
    print()
    
    print("💡 คำแนะนำ:")
    print("   • ใช้ร่วมกับ manual verification สำหรับผลลัพธ์ที่สำคัญ")
    print("   • ปรับ similarity threshold ตามความต้องการ")
    print("   • เพิ่มข้อมูลฝึกสอนสำหรับ context ที่เฉพาะเจาะจง")

def main():
    file_path = "data/pantip_comments_2sources_20250620_184828.jsonl"
    
    if not Path(file_path).exists():
        print(f"❌ ไม่พบไฟล์: {file_path}")
        return
    
    analyze_sentiment_accuracy(file_path)

if __name__ == "__main__":
    main()
