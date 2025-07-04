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
    # Check for sarcasm first using the enhanced detection
    try:
        from app import analyze_sarcasm, analyze_sentiment_builtin
        sarcasm_result = analyze_sarcasm(text)
        
        # If sarcasm is detected, use the builtin analysis with sarcasm handling
        if sarcasm_result.get('is_sarcastic', False):
            result = analyze_sentiment_builtin(text, mode=mode, threshold=threshold)
            formatted_result = {
                "text": text,
                "sentiment": result["sentiment"],
                "confidence": result["confidence"],
                "sentiment_score": result.get("sentiment_score", _sentiment_to_score(result["sentiment"])),
                "detailed_emotion": result.get("detailed_emotion", "เฉย ๆ"),
                "emotion_group": result.get("emotion_group", "Neutral"),
                "context": result.get("context", {}),
                "sarcasm_detected": True,
                "sarcasm_reason": sarcasm_result.get('reason', ''),
                "analysis_mode": mode,
                "model_used": "builtin_with_sarcasm"
            }
            if mode == "multi":
                formatted_result["detailed_emotions"] = result.get("detailed_emotions", [result.get("detailed_emotion", "เฉย ๆ")])
                formatted_result["emotion_groups"] = result.get("emotion_groups", [result.get("emotion_group", "Neutral")])
                formatted_result["primary_emotion"] = result.get("detailed_emotions", [result.get("detailed_emotion", "เฉย ๆ")])[0]
                formatted_result["threshold"] = threshold
            if include_scores:
                formatted_result["all_scores"] = result.get("scores", {})
            return formatted_result
    except ImportError:
        pass  # Fall back to original detailed analysis
    except Exception as e:
        print(f"Warning: Sarcasm detection failed: {e}")
    
    # Original detailed analysis for non-sarcastic text
    analyzer = get_detailed_analyzer()
    try:
        if mode == "single":
            result = analyzer.analyze_single_label(text)
            formatted_result = {
                "text": text,
                "sentiment": _map_emotion_to_sentiment(result.get("label", "เฉย ๆ")),
                "detailed_emotion": result.get("label", "เฉย ๆ"),
                "emotion_group": result.get("group", "Neutral"),
                "confidence": result.get("confidence", 0.0),
                "context": result.get("context", {}),
                "analysis_mode": "single_label",
                "model_used": "detailed_analyzer"
            }
            if include_scores:
                formatted_result["all_scores"] = result.get("scores", {})
        elif mode == "multi":
            result = analyzer.analyze_multi_label(text, threshold=threshold)
            labels = result.get("labels", [])
            primary_emotion = labels[0] if labels else "เฉย ๆ"
            formatted_result = {
                "text": text,
                "sentiment": _map_emotion_to_sentiment(primary_emotion),
                "detailed_emotions": labels,
                "emotion_groups": result.get("groups", []),
                "primary_emotion": primary_emotion,
                "context": result.get("context", {}),
                "threshold": threshold,
                "analysis_mode": "multi_label",
                "model_used": "detailed_analyzer"
            }
            if include_scores:
                formatted_result["all_scores"] = result.get("scores", {})
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'single' or 'multi'")
        return formatted_result
    except Exception as e:
        # กรณีเกิดข้อผิดพลาด ให้คืนค่า default ที่ไม่ทำให้ระบบล่ม
        if mode == "single":
            return {
                "text": text,
                "sentiment": "neutral",
                "detailed_emotion": "เฉย ๆ",
                "emotion_group": "Neutral",
                "confidence": 0.0,
                "context": {},
                "analysis_mode": "single_label",
                "error": str(e)
            }
        else:
            return {
                "text": text,
                "sentiment": "neutral",
                "detailed_emotions": ["เฉย ๆ"],
                "emotion_groups": ["Neutral"],
                "primary_emotion": "เฉย ๆ",
                "context": {},
                "threshold": threshold,
                "analysis_mode": "multi_label",
                "error": str(e)
            }

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
            
            # นับ context (serialize dict เป็น string เพื่อใช้เป็น key)
            context = sentiment_data.get("context")
            if context:
                if isinstance(context, dict):
                    context_key = json.dumps(context, ensure_ascii=False, sort_keys=True)
                else:
                    context_key = str(context)
                stats["context_counts"][context_key] = stats["context_counts"].get(context_key, 0) + 1
    
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
    เปลี่ยนเป็นใช้ AI Model จริง (detailed sentiment analyzer) เท่านั้น
    แต่เพิ่ม fallback ไปยัง builtin analysis ที่มี sarcasm detection
    """
    try:
        # Try detailed analysis first
        result = analyze_detailed_sentiment(
            text,
            mode="single",
            threshold=0.3,
            include_scores=False
        )
        return {
            "text": text,
            "sentiment": result["sentiment"],
            "confidence": result["confidence"],
            "sentiment_score": _sentiment_to_score(result["sentiment"]),
            "detailed_emotion": result.get("detailed_emotion", result.get("label", "")),
            "emotion_group": result.get("emotion_group", result.get("group", "")),
            "context": result.get("context", {})
        }
    except Exception as e:
        # Fallback to builtin analysis with enhanced sarcasm detection
        try:
            from app import analyze_sentiment_builtin
            result = analyze_sentiment_builtin(text, mode='single')
            return {
                "text": text,
                "sentiment": result["sentiment"],
                "confidence": result["confidence"],
                "sentiment_score": result["sentiment_score"],
                "detailed_emotion": result.get("detailed_emotion", "เฉย ๆ"),
                "emotion_group": result.get("emotion_group", "Neutral"),
                "context": result.get("context", {}),
                "fallback_used": True,
                "error": str(e)
            }
        except Exception as e2:
            # Final fallback
            return {
                "text": text,
                "sentiment": "neutral",
                "confidence": 0.0,
                "sentiment_score": 0.0,
                "detailed_emotion": "เฉย ๆ",
                "emotion_group": "Neutral",
                "context": {},
                "error": str(e2)
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
        # Original examples
        "โกรธจนขำอะ! ทำไมต้องมาแบบนี้ด้วย 555 😡😂",  # Mixed anger/laughter
        "ดีใจมากเลย รักเธอที่สุดเลย ❤️😍",  # Clear positive
        "ข้อมูลข่าวสารประจำวันครับ สถานการณ์ปกติดี",  # Neutral news
        "อ่อ... เยี่ยมจริงๆ เนอะ บริการดีมากเลย 🙄",  # Sarcastic positive
        "ตอนแรกก็คิดว่าดีนะ แต่พอใช้ไปใช้มาคือแบบ... ไม่ไหวอะ ห่วยแตกสิ้นดี",  # Negative with progression
        
        # New challenging additions from user feedback
        "งานนี้สุดยอดครับ... ถ้าชอบความล้มเหลว",  # Ironic praise
        "ประเทศไทยจะไม่เหมือนเดิม... แย่ลงทุกวัน",  # Negative with political nuance
        "ขอบคุณนะคะที่ทำให้วันนี้เป็นวันที่แย่ที่สุดในชีวิต 😊",  # Positive words, negative meaning
        "คิดถึงสมัยก่อนจัง... เมื่อประเทศยังมีอนาคต",  # Nostalgic + political critique
        "บริการระดับห้าดาว... ในโลกคู่ขนาน",  # Sarcastic comparison
        "ทำดีแล้วครับ... สำหรับคนที่มาตรฐานต่ำมาก",  # Backhanded compliment
        "ภูมิใจในตัวคุณ... ที่เป็นต้นเหตุของปัญหาทุกอย่าง",  # False praise
        "อนาคตสดใสแน่นอน... ถ้ายังทำแบบนี้ต่อไป",  # Negative prediction disguised as positive
        "นโยบายสร้างสรรค์มาก... สำหรับคนที่ไม่อยากให้ประเทศพัฒนา",  # Political sarcasm
        "สุดยอดประสบการณ์... ที่ไม่อยากให้ใครเจอ",  # Ironic experience
        "ดีใจด้วยนะ... ที่ได้เป็นส่วนหนึ่งของความล้มเหลวนี้",  # Mocking congratulations
        "เก่งมาก... เก่งจนทำให้แย่ลง",  # Paradoxical compliment
        "น่าประทับใจจริงๆ... ในความไร้ความสามารถ",  # Admiring incompetence
        "ขอชื่นชม... ความพยายามที่จะทำให้ล้มเหลว",  # Praising failure
        "ดีกว่าเพื่อน... ถ้าเพื่อนคนนั้นแย่สุดๆ",  # Relative negativity
        "ไม่น่าเชื่อว่าทำได้... แย่ขนาดนี้",  # Surprised disappointment
        "พัฒนาการที่ดี... ในการเดินถอยหลัง",  # Ironic progress

        # Sarcasm focused on "Praise -> Insult" structure
        "เป็นความคิดที่ดีมาก... สำหรับคนที่ไม่คิดอะไรเลย", # Sarcastic praise
        "ชุดนี้สวยจัง... ถ้าจะไปงานแฟนซี", # Backhanded compliment on appearance
        "เสียงเพราะมาก... จนอยากปิดหู", # Ironic compliment on sound
        "เขียนดีนะ... ถ้าไม่นับว่าอ่านไม่รู้เรื่อง", # Sarcastic feedback on writing
        "ฉลาดเป็นกรด... แต่กัดกร่อนทุกอย่าง", # Compliment with a destructive consequence

        # Sarcasm/Irony with English
        "The service is 'amazing'. Waited 20 minutes for a glass of water.",
        "Oh, great. Another meeting. Just what I needed.",
        "I love it when my code breaks for no reason. So fun.",
        "This is just perfect. I lost my keys.",

        # New Use Cases for Comprehensive Testing
        # -----------------------------------------

        # 1. Double Negatives (should be neutral or slightly positive)
        "ก็ไม่ได้ไม่ชอบนะ ก็โอเค",
        "ถามว่าเกลียดไหม ก็ไม่นะ แต่ก็ไม่ได้ชอบ",

        # 2. Reported Speech (sentiment should be from the speaker)
        "เพื่อนบอกว่าหนังสนุกมาก แต่ส่วนตัวเราเฉยๆ อะ",
        "ใครๆ ก็ชมว่าสวย แต่เราว่ามันดูธรรมดาไปหน่อย",
        "เห็นรีวิวบอกว่าร้านนี้เด็ดมาก พอลองแล้วก็งั้นๆ",

        # 3. Rhetorical Questions (often imply strong sentiment)
        "ทำกันได้ลงคอเนอะ?", # Negative
        "แล้วใครจะไปทนกับเรื่องแบบนี้ได้!?", # Negative
        "สวยขนาดนี้ ไม่ให้ชอบได้ไง", # Positive

        # 4. Balanced Mixed Opinions (not sarcastic)
        "อาหารอร่อยนะ แต่บริการช้าไปนิดนึง โดยรวมก็โอเค",
        "วิวสวยมาก แต่ทางขึ้นลำบากไปหน่อย",
        "ชอบดีไซน์นะ แต่ติดที่ราคาแรงไปนิด",

        # 5. Imperative Sentences (Commands/Requests - usually neutral)
        "ช่วยส่งเอกสารให้ด้วยค่ะ",
        "รบกวนช่วยเงียบๆ หน่อยครับ",
        "อย่าลืมปิดไฟนะ",

        # 6. Informal/Misspelled words
        "จิงๆ ก้อดีนะ ชอบมั่กๆ", # จริงๆ ก็ดีนะ ชอบมากๆ (Positive)
        "ทัมมัยทำแบบนี้", # ทำไมทำแบบนี้ (Negative/Question)
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
