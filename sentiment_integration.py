#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration module for Detailed Thai Sentiment Analysis
โมดูลเชื่อมต่อระบบ sentiment analysis ใหม่กับระบบเดิม
"""

from typing import Dict, List, Any, Optional, Union
from detailed_thai_sentiment import DetailedThaiSentimentAnalyzer, EMOTION_GROUPS
import json

# สร้าง global analyzer instance
_detailed_analyzer = None

def get_detailed_analyzer() -> DetailedThaiSentimentAnalyzer:
    """ได้รับ analyzer instance (singleton pattern)"""
    global _detailed_analyzer
    if _detailed_analyzer is None:
        _detailed_analyzer = DetailedThaiSentimentAnalyzer()
    return _detailed_analyzer

def analyze_detailed_sentiment(
    text: str, 
    mode: str = "single",  # "single" หรือ "multi"
    threshold: float = 0.3,
    include_scores: bool = False
) -> Dict[str, Any]:
    """
    วิเคราะห์ sentiment แบบละเอียด
    
    Args:
        text: ข้อความที่ต้องการวิเคราะห์
        mode: "single" สำหรับ single-label, "multi" สำหรับ multi-label
        threshold: threshold สำหรับ multi-label (default: 0.3)
        include_scores: รวมคะแนนทั้งหมดในผลลัพธ์หรือไม่
    
    Returns:
        Dict ที่มีผลการวิเคราะห์
    """
    analyzer = get_detailed_analyzer()
    
    if mode == "single":
        result = analyzer.analyze_single_label(text)
        
        # แปลงให้เข้ากับ format เดิม
        formatted_result = {
            "text": text,
            "sentiment": _map_emotion_to_sentiment(result["label"]),
            "detailed_emotion": result["label"],
            "emotion_group": result["group"],
            "confidence": result["confidence"],
            "context": result["context"],
            "analysis_mode": "single_label"
        }
        
        if include_scores:
            formatted_result["all_scores"] = result["scores"]
            
    elif mode == "multi":
        result = analyzer.analyze_multi_label(text, threshold=threshold)
        
        # สำหรับ multi-label ใช้อารมณ์หลักเป็น sentiment
        primary_emotion = result["labels"][0] if result["labels"] else "เฉย ๆ"
        
        formatted_result = {
            "text": text,
            "sentiment": _map_emotion_to_sentiment(primary_emotion),
            "detailed_emotions": result["labels"],
            "emotion_groups": result["groups"],
            "primary_emotion": primary_emotion,
            "context": result["context"],
            "threshold": threshold,
            "analysis_mode": "multi_label"
        }
        
        if include_scores:
            formatted_result["all_scores"] = result["scores"]
    
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 'single' or 'multi'")
    
    return formatted_result

def _map_emotion_to_sentiment(emotion: str) -> str:
    """แปลงอารมณ์เป็น sentiment แบบเดิม (positive/negative/neutral)"""
    group = EMOTION_GROUPS.get(emotion)
    if not group:
        # หากไม่พบใน group ให้ดูจาก EMOTION_GROUPS
        for group_name, emotions in EMOTION_GROUPS.items():
            if emotion in emotions:
                group = group_name
                break
    
    if group == "Positive":
        return "positive"
    elif group == "Negative":
        return "negative"
    elif group == "Neutral":
        return "neutral"
    elif group == "Others":
        # สำหรับ Others ให้ดูจากอารมณ์เฉพาะ
        if emotion in ["ขำขัน"]:
            return "positive"
        elif emotion in ["ประชด", "เสียดสี"]:
            return "negative"
        else:
            return "neutral"
    else:
        return "neutral"

def batch_analyze_detailed_sentiment(
    texts: List[str],
    mode: str = "single",
    threshold: float = 0.3,
    include_scores: bool = False,
    show_progress: bool = False
) -> List[Dict[str, Any]]:
    """วิเคราะห์ sentiment แบบ batch"""
    results = []
    
    if show_progress:
        try:
            from tqdm import tqdm
            iterator = tqdm(texts, desc="Analyzing sentiment")
        except ImportError:
            iterator = texts
    else:
        iterator = texts
    
    for text in iterator:
        result = analyze_detailed_sentiment(text, mode, threshold, include_scores)
        results.append(result)
    
    return results

def analyze_comment_sentiment(
    comment_data: Dict[str, Any],
    text_field: str = "text",
    mode: str = "single",
    threshold: float = 0.3
) -> Dict[str, Any]:
    """
    วิเคราะห์ sentiment สำหรับ comment data
    เหมาะสำหรับข้อมูลจาก social media
    """
    if text_field not in comment_data:
        return comment_data
    
    text = comment_data[text_field]
    if not text or not text.strip():
        return comment_data
    
    # วิเคราะห์ sentiment
    sentiment_result = analyze_detailed_sentiment(text, mode, threshold, include_scores=True)
    
    # เพิ่มผลการวิเคราะห์เข้าไปใน comment data
    enhanced_comment = comment_data.copy()
    enhanced_comment.update({
        "sentiment_analysis": sentiment_result,
        "sentiment": sentiment_result["sentiment"],  # เพื่อ backward compatibility
        "detailed_sentiment_enabled": True
    })
    
    return enhanced_comment

def analyze_social_media_batch(
    comments: List[Dict[str, Any]],
    text_field: str = "text",
    mode: str = "single",
    threshold: float = 0.3,
    show_progress: bool = True
) -> List[Dict[str, Any]]:
    """วิเคราะห์ sentiment สำหรับข้อมูล social media แบบ batch"""
    results = []
    
    if show_progress:
        try:
            from tqdm import tqdm
            iterator = tqdm(comments, desc="Analyzing social media sentiment")
        except ImportError:
            iterator = comments
    else:
        iterator = comments
    
    for comment in iterator:
        analyzed_comment = analyze_comment_sentiment(comment, text_field, mode, threshold)
        results.append(analyzed_comment)
    
    return results

def get_sentiment_statistics(
    analyzed_comments: List[Dict[str, Any]],
    detailed: bool = True
) -> Dict[str, Any]:
    """คำนวณสถิติของ sentiment จากผลการวิเคราะห์"""
    if not analyzed_comments:
        return {}
    
    stats = {
        "total_comments": len(analyzed_comments),
        "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
        "analysis_mode": "unknown"
    }
    
    if detailed:
        stats["detailed_emotion_counts"] = {}
        stats["emotion_group_counts"] = {}
        stats["context_counts"] = {}
    
    for comment in analyzed_comments:
        sentiment_data = comment.get("sentiment_analysis", {})
        
        if not sentiment_data:
            continue
        
        # นับ basic sentiment
        sentiment = sentiment_data.get("sentiment", "neutral")
        if sentiment in stats["sentiment_counts"]:
            stats["sentiment_counts"][sentiment] += 1
        
        # กำหนด analysis mode
        if "analysis_mode" in sentiment_data:
            stats["analysis_mode"] = sentiment_data["analysis_mode"]
        
        if detailed:
            # นับ detailed emotions
            if sentiment_data.get("analysis_mode") == "single_label":
                emotion = sentiment_data.get("detailed_emotion")
                if emotion:
                    stats["detailed_emotion_counts"][emotion] = stats["detailed_emotion_counts"].get(emotion, 0) + 1
                
                group = sentiment_data.get("emotion_group")
                if group:
                    stats["emotion_group_counts"][group] = stats["emotion_group_counts"].get(group, 0) + 1
            
            elif sentiment_data.get("analysis_mode") == "multi_label":
                emotions = sentiment_data.get("detailed_emotions", [])
                for emotion in emotions:
                    stats["detailed_emotion_counts"][emotion] = stats["detailed_emotion_counts"].get(emotion, 0) + 1
                
                groups = sentiment_data.get("emotion_groups", [])
                for group in groups:
                    stats["emotion_group_counts"][group] = stats["emotion_group_counts"].get(group, 0) + 1
            
            # นับ context
            context = sentiment_data.get("context")
            if context:
                stats["context_counts"][context] = stats["context_counts"].get(context, 0) + 1
    
    return stats

def export_detailed_sentiment_results(
    analyzed_comments: List[Dict[str, Any]],
    output_path: str,
    format: str = "jsonl",
    include_original: bool = True
) -> str:
    """ส่งออกผลการวิเคราะห์ sentiment แบบละเอียด"""
    
    # เตรียมข้อมูลสำหรับส่งออก
    export_data = []
    
    for comment in analyzed_comments:
        if include_original:
            export_item = comment.copy()
        else:
            # ส่งออกเฉพาะข้อมูล sentiment
            export_item = {
                "text": comment.get("text", ""),
                "sentiment_analysis": comment.get("sentiment_analysis", {})
            }
            
            # เพิ่มข้อมูลพื้นฐานถ้ามี
            for field in ["author", "timestamp", "platform", "comment_id"]:
                if field in comment:
                    export_item[field] = comment[field]
        
        export_data.append(export_item)
    
    # บันทึกไฟล์
    if format.lower() == "jsonl":
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in export_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    elif format.lower() == "json":
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return output_path

# === BACKWARD COMPATIBILITY ===

def enhanced_analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    ฟังก์ชันสำหรับ backward compatibility กับระบบเดิม
    แต่ใช้ระบบ sentiment analysis ใหม่
    """
    result = analyze_detailed_sentiment(
        text, 
        mode="single", 
        threshold=0.3, 
        include_scores=False
    )
    
    # แปลงให้เข้ากับ format เดิม
    return {
        "sentiment": result["sentiment"],
        "confidence": result["confidence"],
        "sentiment_score": _sentiment_to_score(result["sentiment"]),
        "model_type": "detailed_thai_sentiment",
        
        # ข้อมูลเพิ่มเติม
        "detailed_emotion": result["detailed_emotion"],
        "emotion_group": result["emotion_group"],
        "context": result["context"]
    }

def _sentiment_to_score(sentiment: str) -> float:
    """แปลง sentiment เป็น score เพื่อ compatibility"""
    if sentiment == "positive":
        return 0.7
    elif sentiment == "negative":
        return -0.7
    else:
        return 0.0

# === DEMO FUNCTION ===

def demo_integration():
    """Demo การใช้งาน integration module"""
    print("🔗 Detailed Thai Sentiment Integration Demo")
    print("=" * 50)
    
    # ทดสอบข้อความต่างๆ
    test_texts = [
        "โกรธจนขำอะ! ทำไมต้องมาแบบนี้ด้วย 555 😡😂",
        "ดีใจมากเลย รักเธอที่สุดเลย ❤️😍",
        "ข้อมูลข่าวสารประจำวันครับ สถานการณ์ปกติดี",
        "อ่อ... เยี่ยมจริงๆ เนอะ บริการดีมากเลย 🙄"
    ]
    
    print("\n📍 Single Label Analysis:")
    for text in test_texts:
        result = analyze_detailed_sentiment(text, mode="single", include_scores=True)
        print(f"ข้อความ: {text}")
        print(f"Basic: {result['sentiment']} | Detailed: {result['detailed_emotion']} ({result['emotion_group']})")
        print(f"Confidence: {result['confidence']} | Context: {result['context']}")
        print()
    
    print("\n📍 Multi Label Analysis:")
    for text in test_texts:
        result = analyze_detailed_sentiment(text, mode="multi", threshold=0.25, include_scores=True)
        print(f"ข้อความ: {text}")
        print(f"Basic: {result['sentiment']} | Detailed: {result['detailed_emotions']} ({result['emotion_groups']})")
        print(f"Primary: {result['primary_emotion']} | Context: {result['context']}")
        print()
    
    # ทดสอบ social media batch
    print("\n📱 Social Media Batch Analysis:")
    sample_comments = [
        {"text": test_texts[0], "author": "user1", "platform": "facebook"},
        {"text": test_texts[1], "author": "user2", "platform": "twitter"},
        {"text": test_texts[2], "author": "user3", "platform": "youtube"},
        {"text": test_texts[3], "author": "user4", "platform": "pantip"}
    ]
    
    analyzed = analyze_social_media_batch(sample_comments, mode="multi", threshold=0.25, show_progress=False)
    
    for comment in analyzed:
        print(f"Platform: {comment['platform']}")
        print(f"Text: {comment['text']}")
        sentiment_data = comment['sentiment_analysis']
        print(f"Result: {sentiment_data['sentiment']} -> {sentiment_data['detailed_emotions']}")
        print()
    
    # แสดงสถิติ
    stats = get_sentiment_statistics(analyzed, detailed=True)
    print("📊 Statistics:")
    print(f"Total: {stats['total_comments']}")
    print(f"Basic sentiment: {stats['sentiment_counts']}")
    print(f"Detailed emotions: {stats['detailed_emotion_counts']}")
    print(f"Emotion groups: {stats['emotion_group_counts']}")
    print(f"Contexts: {stats['context_counts']}")

if __name__ == "__main__":
    demo_integration()
