#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed Thai Sentiment Analysis System
ระบบ sentiment analysis ภาษาไทยแบบละเอียด
รองรับ multi-class และ multi-label classification
"""

import json
import re
import random
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# === EMOTION LABEL SCHEMA ===
EMOTION_LABELS = [
    # Positive
    "ดีใจ", "ชอบ", "ซึ้งใจ", "พอใจ", "รัก",
    
    # Negative  
    "โกรธ", "เสียใจ", "ผิดหวัง", "รำคาญ", "เกลียด", "กลัว", "อึดอัด", "ตกใจ",
    
    # Neutral
    "เฉย ๆ", "ไม่รู้สึกอะไร", "ข้อมูลข่าวสาร",
    
    # Others (Complex emotions)
    "ประชด", "ขำขัน", "เสียดสี", "สับสน"
]

# Emotion grouping
EMOTION_GROUPS = {
    "Positive": ["ดีใจ", "ชอบ", "ซึ้งใจ", "พอใจ", "รัก"],
    "Negative": ["โกรธ", "เสียใจ", "ผิดหวัง", "รำคาญ", "เกลียด", "กลัว", "อึดอัด", "ตกใจ"],
    "Neutral": ["เฉย ๆ", "ไม่รู้สึกอะไร", "ข้อมูลข่าวสาร"],
    "Others": ["ประชด", "ขำขัน", "เสียดสี", "สับสน"]
}

# Reverse mapping for quick lookup
LABEL_TO_GROUP = {}
for group, labels in EMOTION_GROUPS.items():
    for label in labels:
        LABEL_TO_GROUP[label] = group

class ThaiEmotionPatterns:
    """คลาส pattern matching สำหรับการวิเคราะห์อารมณ์ภาษาไทย"""
    
    def __init__(self):
        self.emotion_patterns = self._build_emotion_patterns()
        self.intensity_patterns = self._build_intensity_patterns()
        self.context_patterns = self._build_context_patterns()
    
    def _build_emotion_patterns(self) -> Dict[str, Dict[str, Any]]:
        """สร้าง patterns สำหรับแต่ละอารมณ์"""
        return {
            # === POSITIVE EMOTIONS ===
            "ดีใจ": {
                "keywords": ["ดีใจ", "มีความสุข", "แฮปปี้", "ปลื้ม", "ยินดี", "เฮง", "เย้", "โย่", "เจ๋ง", "ดี่ใจ"],
                "patterns": [r"ดี\s*ใจ", r"ปลื้ม", r"เฮง\s*ซะ", r"แฮปปี้", r"เย้.*", r"โย่.*"],
                "emojis": ["😊", "😄", "🤗", "😍", "🥰", "😘", "😆", "🤩"],
                "score_range": (0.6, 1.0)
            },
            
            "ชอบ": {
                "keywords": ["ชอบ", "รัก", "ถูกใจ", "โปรด", "ปลื้ม", "สนใจ", "อิน", "เคลิ้ม"],
                "patterns": [r"ชอบ.*มาก", r"รัก.*เลย", r"ถูกใจ", r"โปรด.*", r"สนใจ.*มาก"],
                "emojis": ["❤️", "💕", "😍", "🥰", "😘", "💖", "💝"],
                "score_range": (0.5, 0.9)
            },
            
            "ซึ้งใจ": {
                "keywords": ["ซึ้ง", "ซึ้งใจ", "น้ำตาซึม", "ประทับใจ", "ซาบซึ้ง", "ตื้นตัน", "ซื่นใส"],
                "patterns": [r"ซึ้ง.*ใจ", r"ประทับใจ", r"น้ำตา.*ซึม", r"ซาบซึ้ง"],
                "emojis": ["😭", "🥺", "😢", "🤧", "💞"],
                "score_range": (0.4, 0.8)
            },
            
            "พอใจ": {
                "keywords": ["พอใจ", "โอเค", "ใช้ได้", "ปกติดี", "ไม่เป็นไร", "งาม", "เรียบร้อย"],
                "patterns": [r"พอใจ", r"โอเค.*", r"ใช้ได้", r"ปกติดี", r"เรียบร้อย"],
                "emojis": ["👍", "👌", "😌", "🙂"],
                "score_range": (0.2, 0.6)
            },
            
            "รัก": {
                "keywords": ["รัก", "หลงรัก", "แพง", "เลิฟ", "love", "ฮักๆ", "ฮัก", "รักมาก"],
                "patterns": [r"รัก.*มาก", r"หลงรัก", r"เลิฟ.*", r"love.*", r"ฮัก.*"],
                "emojis": ["❤️", "💕", "💖", "💝", "😍", "🥰", "😘"],
                "score_range": (0.7, 1.0)
            },
            
            # === NEGATIVE EMOTIONS ===
            "โกรธ": {
                "keywords": ["โกรธ", "ฉุน", "โมโห", "แค้น", "ขุ่นข้อง", "เดือด", "บ้า", "ห่วยแตก", "แย่", "งี่เง่า"],
                "patterns": [r"โกรธ.*มาก", r"ฉุน.*ขาด", r"โมโห", r"แค้น.*", r"ห่วย.*แตก", r"บ้า.*", r"แย่.*มาก"],
                "emojis": ["😠", "😡", "🤬", "👿", "💢", "😤"],
                "score_range": (-1.0, -0.6)
            },
            
            "เสียใจ": {
                "keywords": ["เสียใจ", "เศร้า", "ใจหาย", "ปวดใจ", "เศร้าโศก", "โศกเศร้า", "เสียดาย", "น่าเสียใจ"],
                "patterns": [r"เสียใจ", r"เศร้า.*มาก", r"ใจหาย", r"ปวดใจ", r"เศร้าโศก"],
                "emojis": ["😢", "😭", "😞", "☹️", "😔", "💔"],
                "score_range": (-0.8, -0.4)
            },
            
            "ผิดหวัง": {
                "keywords": ["ผิดหวัง", "หวังเกิน", "คาดหวัง", "ท้อ", "หมดหวัง", "ไม่ได้ดังใจ"],
                "patterns": [r"ผิดหวัง", r"หวัง.*เกิน", r"คาดหวัง.*มาก", r"ท้อ.*", r"หมดหวัง"],
                "emojis": ["😞", "😔", "😓", "😩", "😤"],
                "score_range": (-0.7, -0.3)
            },
            
            "รำคาญ": {
                "keywords": ["รำคาญ", "น่ารำคาญ", "เบื่อ", "หน่าย", "เซ็ง", "ง่วง", "เครียด", "เหนื่อย"],
                "patterns": [r"รำคาญ", r"เบื่อ.*มาก", r"หน่าย.*", r"เซ็ง.*", r"เครียด.*"],
                "emojis": ["😒", "🙄", "😤", "😑", "😫", "😩"],
                "score_range": (-0.6, -0.2)
            },
            
            "เกลียด": {
                "keywords": ["เกลียด", "ขยะแขยง", "แค้น", "แกล้ง", "ไม่ชอบ", "ต่อต้าน"],
                "patterns": [r"เกลียด.*มาก", r"ขยะแขยง", r"แค้น.*", r"ไม่ชอบ.*เลย"],
                "emojis": ["😡", "🤬", "👿", "😠", "💢"],
                "score_range": (-1.0, -0.7)
            },
            
            "กลัว": {
                "keywords": ["กลัว", "หวาดกลัว", "ตกใจ", "วิตก", "กังวล", "เครียด", "หวั่น", "ตื่นกลัว"],
                "patterns": [r"กลัว.*มาก", r"หวาดกลัว", r"ตกใจ.*", r"วิตก.*", r"กังวล.*"],
                "emojis": ["😨", "😰", "😱", "😧", "🫣", "😳"],
                "score_range": (-0.8, -0.3)
            },
            
            "อึดอัด": {
                "keywords": ["อึดอัด", "อับอาย", "เก้อ", "ไม่สบายใจ", "กดดัน", "ขัดใจ"],
                "patterns": [r"อึดอัด", r"อับอาย", r"ไม่สบายใจ", r"กดดัน", r"ขัดใจ"],
                "emojis": ["😣", "😖", "😫", "😤", "😰"],
                "score_range": (-0.6, -0.2)
            },
            
            "ตกใจ": {
                "keywords": ["ตกใจ", "สะดุ้ง", "โหยง", "ตกตะลึง", "ตะลึง", "หวาดเสียว"],
                "patterns": [r"ตกใจ.*มาก", r"สะดุ้ง", r"โหยง", r"ตกตะลึง", r"ตะลึง"],
                "emojis": ["😱", "😨", "😳", "🫨", "😧"],
                "score_range": (-0.5, 0.0)
            },
            
            # === NEUTRAL EMOTIONS ===
            "เฉย ๆ": {
                "keywords": ["เฉย", "ธรรมดา", "ปกติ", "โอเค", "ใช้ได้", "พอใช้", "ไม่เป็นไร"],
                "patterns": [r"เฉย.*ๆ", r"ธรรมดา", r"ปกติ.*", r"โอเค", r"ไม่เป็นไร"],
                "emojis": ["😐", "🙂", "😶", "😑"],
                "score_range": (-0.1, 0.1)
            },
            
            "ไม่รู้สึกอะไร": {
                "keywords": ["ไม่รู้สึก", "ชา", "เฉย", "ไม่สน", "ไม่แคร์", "ไม่เข้าใจ"],
                "patterns": [r"ไม่รู้สึก.*อะไร", r"ชา.*", r"ไม่สน.*", r"ไม่แคร์"],
                "emojis": ["😶", "😐", "🤷‍♀️", "🤷‍♂️"],
                "score_range": (-0.05, 0.05)
            },
            
            "ข้อมูลข่าวสาร": {
                "keywords": ["ข้อมูล", "ข่าว", "รายงาน", "แจ้ง", "บอก", "อัปเดต", "สำคัญ"],
                "patterns": [r"ข้อมูล.*", r"ข่าว.*", r"รายงาน.*", r"แจ้ง.*", r"อัปเดต.*"],
                "emojis": ["📰", "📊", "📈", "📢", "ℹ️"],
                "score_range": (0.0, 0.0)
            },
            
            # === OTHERS (COMPLEX EMOTIONS) ===
            "ประชด": {
                "keywords": ["ประชด", "เหน็บแนม", "เสียดสี", "แดกดัน", "จิกกัด", "อีดอก"],
                "patterns": [r"ประชด.*", r"เหน็บแนม", r"เสียดสี.*", r"แดกดัน", r"จิกกัด"],
                "emojis": ["😏", "🙄", "😒", "😤"],
                "score_range": (-0.4, -0.1)
            },
            
            "ขำขัน": {
                "keywords": ["ขำ", "ตลก", "555", "ฮา", "เฮฮา", "สนุก", "โลกแตก", "ครื่นเครง"],
                "patterns": [r"ขำ.*", r"ตลก.*", r"555+", r"ฮา+", r"เฮฮา", r"สนุก.*"],
                "emojis": ["😂", "🤣", "😆", "😄", "😁", "🤪", "😜"],
                "score_range": (0.3, 0.8)
            },
            
            "เสียดสี": {
                "keywords": ["เสียดสี", "ประชด", "เหน็บ", "แนม", "จิกกัด", "แกล้ง"],
                "patterns": [r"เสียดสี.*", r"ประชด.*", r"เหน็บ.*แนม", r"จิกกัด.*"],
                "emojis": ["😏", "🙄", "😒"],
                "score_range": (-0.5, -0.2)
            },
            
            "สับสน": {
                "keywords": ["สับสน", "งง", "เข้าใจไม่ได้", "แปลก", "ฉงน", "ฉงนสนเท่ห์"],
                "patterns": [r"สับสน", r"งง.*", r"เข้าใจไม่ได้", r"แปลก.*", r"ฉงน.*"],
                "emojis": ["😕", "🤔", "😵‍💫", "🫤", "😵"],
                "score_range": (-0.2, 0.2)
            }
        }
    
    def _build_intensity_patterns(self) -> Dict[str, List[str]]:
        """สร้าง patterns สำหรับความเข้มข้นของอารมณ์"""
        return {
            "high": ["มาก", "เลย", "สุด", "แรง", "หนัก", "โคตร", "แสน", "สาหัส", "เป็นบ้า", "จริงๆ"],
            "medium": ["พอ", "ค่อนข้าง", "ปานกลาง", "ใช้ได้", "โอเค"],
            "low": ["เล็กน้อย", "นิดหน่อย", "เบาๆ", "นิดเดียว", "ไม่มาก"]
        }
    
    def _build_context_patterns(self) -> Dict[str, List[str]]:
        """สร้าง patterns สำหรับบริบทการใช้ภาษา"""
        return {
            "formal": ["ครับ", "ค่ะ", "คะ", "ขอ", "กรุณา", "สวัสดี", "ขอบคุณ"],
            "informal": ["นะ", "เนอะ", "อะ", "เอ้ย", "เออ", "ของ", "555", "ฮา"],
            "slang": ["โคตร", "เฟี้ยว", "เทพ", "แม่ง", "ควย", "บิน", "เฟี้ยม"],
            "personal": ["กู", "มึง", "เรา", "ฉัน", "คิด", "รู้สึก"]
        }

class DetailedThaiSentimentAnalyzer:
    """ระบบวิเคราะห์ sentiment ภาษาไทยแบบละเอียด"""
    
    def __init__(self):
        self.patterns = ThaiEmotionPatterns()
        self.multi_label_threshold = 0.3  # threshold สำหรับการตัดสิน multi-label
        
    def _clean_text(self, text: str) -> str:
        """ทำความสะอาดข้อความ"""
        if not text:
            return ""
        
        # แปลงเป็นตัวพิมพ์เล็ก
        text = text.lower()
        
        # ลบ URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # ลบ mentions และ hashtags ใน social media
        text = re.sub(r'[@#]\w+', '', text)
        
        # ทำความสะอาดช่องว่างเกิน
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_emojis(self, text: str) -> List[str]:
        """ดึง emojis จากข้อความ"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.findall(text)
    
    def _calculate_emotion_scores(self, text: str) -> Dict[str, float]:
        """คำนวณคะแนนสำหรับแต่ละอารมณ์"""
        clean_text = self._clean_text(text)
        emojis = self._extract_emojis(text)
        emotion_scores = defaultdict(float)
        
        for emotion, config in self.patterns.emotion_patterns.items():
            score = 0.0
            
            # คะแนนจากคำสำคัญ
            for keyword in config["keywords"]:
                if keyword in clean_text:
                    score += 1.0
            
            # คะแนนจาก patterns (regex)
            for pattern in config.get("patterns", []):
                matches = re.findall(pattern, clean_text)
                score += len(matches) * 1.5
            
            # คะแนนจาก emojis
            for emoji in emojis:
                if emoji in config.get("emojis", []):
                    score += 2.0
            
            # ปรับคะแนนตามความเข้มข้น
            intensity_bonus = self._calculate_intensity_bonus(clean_text)
            score *= (1 + intensity_bonus)
            
            emotion_scores[emotion] = min(score, 5.0)  # จำกัดคะแนนสูงสุด
        
        return dict(emotion_scores)
    
    def _calculate_intensity_bonus(self, text: str) -> float:
        """คำนวณ bonus จากความเข้มข้นของการแสดงออก"""
        bonus = 0.0
        
        for intensity, words in self.patterns.intensity_patterns.items():
            for word in words:
                if word in text:
                    if intensity == "high":
                        bonus += 0.5
                    elif intensity == "medium":
                        bonus += 0.2
                    elif intensity == "low":
                        bonus += 0.1
        
        return min(bonus, 1.0)  # จำกัด bonus สูงสุด
    
    def _determine_context(self, text: str) -> str:
        """กำหนดบริบทการใช้ภาษา"""
        clean_text = self._clean_text(text)
        context_scores = defaultdict(int)
        
        for context, words in self.patterns.context_patterns.items():
            for word in words:
                if word in clean_text:
                    context_scores[context] += 1
        
        if not context_scores:
            return "neutral"
        
        return max(context_scores, key=context_scores.get)
    
    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """normalize คะแนนให้อยู่ในช่วง 0-1"""
        if not scores:
            return {}
        
        max_score = max(scores.values())
        if max_score == 0:
            return scores
        
        return {emotion: score / max_score for emotion, score in scores.items()}
    
    def analyze_single_label(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์ sentiment แบบ single label (multi-class classification)"""
        if not text or not text.strip():
            return {
                "text": text,
                "label": "เฉย ๆ",
                "group": "Neutral",
                "confidence": 0.0,
                "scores": {},
                "context": "neutral",
                "analysis_type": "single_label"
            }
        
        # คำนวณคะแนนสำหรับแต่ละอารมณ์
        raw_scores = self._calculate_emotion_scores(text)
        normalized_scores = self._normalize_scores(raw_scores)
        
        # เลือกอารมณ์ที่มีคะแนนสูงสุด
        if not normalized_scores:
            predicted_label = "เฉย ๆ"
            confidence = 0.0
        else:
            predicted_label = max(normalized_scores, key=normalized_scores.get)
            confidence = normalized_scores[predicted_label]
        
        # กำหนดกลุ่มอารมณ์
        group = LABEL_TO_GROUP.get(predicted_label, "Unknown")
        
        # กำหนดบริบท
        context = self._determine_context(text)
        
        return {
            "text": text,
            "label": predicted_label,
            "group": group,
            "confidence": round(confidence, 3),
            "scores": {k: round(v, 3) for k, v in normalized_scores.items()},
            "context": context,
            "analysis_type": "single_label",
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_multi_label(self, text: str, threshold: float = None) -> Dict[str, Any]:
        """วิเคราะห์ sentiment แบบ multi-label classification"""
        if threshold is None:
            threshold = self.multi_label_threshold
        
        if not text or not text.strip():
            return {
                "text": text,
                "labels": ["เฉย ๆ"],
                "groups": ["Neutral"],
                "scores": {},
                "context": "neutral",
                "analysis_type": "multi_label",
                "threshold": threshold
            }
        
        # คำนวณคะแนนสำหรับแต่ละอารมณ์
        raw_scores = self._calculate_emotion_scores(text)
        normalized_scores = self._normalize_scores(raw_scores)
        
        # เลือกอารมณ์ที่มีคะแนนเกิน threshold
        predicted_labels = []
        for emotion, score in normalized_scores.items():
            if score >= threshold:
                predicted_labels.append(emotion)
        
        # ถ้าไม่มีอารมณ์ใดเกิน threshold ให้เลือกตัวที่สูงสุด
        if not predicted_labels and normalized_scores:
            predicted_labels = [max(normalized_scores, key=normalized_scores.get)]
        elif not predicted_labels:
            predicted_labels = ["เฉย ๆ"]
        
        # กำหนดกลุ่มอารมณ์
        groups = list(set(LABEL_TO_GROUP.get(label, "Unknown") for label in predicted_labels))
        
        # กำหนดบริบท
        context = self._determine_context(text)
        
        return {
            "text": text,
            "labels": predicted_labels,
            "groups": groups,
            "scores": {k: round(v, 3) for k, v in normalized_scores.items()},
            "context": context,
            "analysis_type": "multi_label",
            "threshold": threshold,
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_batch(self, texts: List[str], multi_label: bool = False, threshold: float = None) -> List[Dict[str, Any]]:
        """วิเคราะห์ sentiment แบบ batch"""
        results = []
        
        for text in texts:
            if multi_label:
                result = self.analyze_multi_label(text, threshold)
            else:
                result = self.analyze_single_label(text)
            
            results.append(result)
        
        return results
    
    def get_emotion_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """คำนวณสถิติของอารมณ์จากผลการวิเคราะห์"""
        if not results:
            return {}
        
        stats = {
            "total_texts": len(results),
            "analysis_type": results[0].get("analysis_type", "unknown"),
            "emotion_counts": defaultdict(int),
            "group_counts": defaultdict(int),
            "context_counts": defaultdict(int),
            "avg_confidence": 0.0
        }
        
        total_confidence = 0.0
        
        for result in results:
            # นับอารมณ์
            if "label" in result:  # single label
                stats["emotion_counts"][result["label"]] += 1
                stats["group_counts"][result["group"]] += 1
                total_confidence += result.get("confidence", 0.0)
            elif "labels" in result:  # multi label
                for label in result["labels"]:
                    stats["emotion_counts"][label] += 1
                for group in result["groups"]:
                    stats["group_counts"][group] += 1
                # สำหรับ multi-label ใช้คะแนนสูงสุดเป็น confidence
                if result["scores"]:
                    total_confidence += max(result["scores"].values())
            
            # นับบริบท
            context = result.get("context", "unknown")
            stats["context_counts"][context] += 1
        
        # คำนวณ confidence เฉลี่ย
        if stats["total_texts"] > 0:
            stats["avg_confidence"] = round(total_confidence / stats["total_texts"], 3)
        
        # แปลงจาก defaultdict เป็น dict ธรรมดา
        stats["emotion_counts"] = dict(stats["emotion_counts"])
        stats["group_counts"] = dict(stats["group_counts"])
        stats["context_counts"] = dict(stats["context_counts"])
        
        return stats

# === UTILITY FUNCTIONS ===

def create_training_data_format(
    text: str, 
    labels: Union[str, List[str]], 
    format_type: str = "classification"
) -> Dict[str, Any]:
    """สร้างรูปแบบข้อมูลสำหรับการ train model"""
    
    if format_type == "classification":
        # สำหรับ traditional ML models (BERT, RoBERTa, etc.)
        if isinstance(labels, str):
            return {
                "text": text,
                "label": labels,
                "label_id": EMOTION_LABELS.index(labels) if labels in EMOTION_LABELS else 0
            }
        else:
            # Multi-label: สร้าง binary vector
            label_vector = [0] * len(EMOTION_LABELS)
            for label in labels:
                if label in EMOTION_LABELS:
                    label_vector[EMOTION_LABELS.index(label)] = 1
            
            return {
                "text": text,
                "labels": labels,
                "label_vector": label_vector
            }
    
    elif format_type == "instruction":
        # สำหรับ LLM fine-tuning
        if isinstance(labels, str):
            instruction = "วิเคราะห์อารมณ์ของข้อความนี้และเลือกอารมณ์ที่เหมาะสมที่สุด"
            output = labels
        else:
            instruction = "วิเคราะห์อารมณ์ของข้อความนี้และเลือกอารมณ์ที่เหมาะสม (สามารถเลือกได้หลายอารมณ์)"
            output = ", ".join(labels)
        
        return {
            "instruction": instruction,
            "input": text,
            "output": output
        }
    
    else:
        raise ValueError(f"Unsupported format_type: {format_type}")

def save_training_data(
    data: List[Dict[str, Any]], 
    output_path: str, 
    format_type: str = "jsonl"
) -> str:
    """บันทึกข้อมูลการ train"""
    
    if format_type == "jsonl":
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    elif format_type == "json":
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    else:
        raise ValueError(f"Unsupported format_type: {format_type}")
    
    return output_path

def demo_detailed_sentiment_analysis():
    """Demo การใช้งานระบบ sentiment analysis แบบละเอียด"""
    
    print("🎯 Demo: Detailed Thai Sentiment Analysis")
    print("=" * 60)
    
    # สร้าง analyzer
    analyzer = DetailedThaiSentimentAnalyzer()
    
    # ข้อมูลทดสอบ
    test_texts = [
        "โกรธจนขำอะชีวิต! ทำไมต้องมาแบบนี้ด้วย 555",
        "ประชดหนักมากจนรู้สึกแย่ เป็นแบบนี้ทุกทีเลย",
        "มันก็โอเค แต่ไม่สุด คาดหวังไว้มากกว่านี้",
        "ดีใจมากเลย! รักมากๆ ขอบคุณนะคะ 😍❤️",
        "ห่วยแตกแล้วจริงๆ โทรไปแจ้งก็ไม่แก้ไข ข้อมูลสำคัญนี้",
        "งงมากเลย สับสนจริงๆ เข้าใจไม่ได้ 🤔",
        "ข่าวสารอัปเดตประจำวัน สถานการณ์ปกติดี"
    ]
    
    print("\n📍 Single Label Analysis (Multi-class Classification)")
    print("-" * 50)
    
    single_results = []
    for text in test_texts:
        result = analyzer.analyze_single_label(text)
        single_results.append(result)
        
        print(f"ข้อความ: {text}")
        print(f"อารมณ์: {result['label']} (กลุ่ม: {result['group']})")
        print(f"ความมั่นใจ: {result['confidence']}")
        print(f"บริบท: {result['context']}")
        print(f"คะแนนอื่นๆ: {result['scores']}")
        print("-" * 30)
    
    print("\n📍 Multi-Label Analysis (Multi-label Classification)")
    print("-" * 50)
    
    multi_results = []
    for text in test_texts:
        result = analyzer.analyze_multi_label(text, threshold=0.3)
        multi_results.append(result)
        
        print(f"ข้อความ: {text}")
        print(f"อารมณ์: {result['labels']} (กลุ่ม: {result['groups']})")
        print(f"บริบท: {result['context']}")
        print(f"คะแนนทั้งหมด: {result['scores']}")
        print("-" * 30)
    
    # แสดงสถิติ
    print("\n📊 สถิติการวิเคราะห์")
    print("-" * 50)
    
    single_stats = analyzer.get_emotion_statistics(single_results)
    multi_stats = analyzer.get_emotion_statistics(multi_results)
    
    print("Single Label:")
    print(f"  - อารมณ์ที่พบ: {single_stats['emotion_counts']}")
    print(f"  - กลุ่มอารมณ์: {single_stats['group_counts']}")
    print(f"  - ความมั่นใจเฉลี่ย: {single_stats['avg_confidence']}")
    
    print("\nMulti Label:")
    print(f"  - อารมณ์ที่พบ: {multi_stats['emotion_counts']}")
    print(f"  - กลุ่มอารมณ์: {multi_stats['group_counts']}")
    print(f"  - ความมั่นใจเฉลี่ย: {multi_stats['avg_confidence']}")
    
    print("\n📝 ตัวอย่างการสร้างข้อมูล Training")
    print("-" * 50)
    
    # สร้างตัวอย่างข้อมูล training
    training_examples = []
    
    # Single label examples
    training_examples.append(
        create_training_data_format("โกรธจนขำอะชีวิต!", "โกรธ", "classification")
    )
    
    # Multi-label examples
    training_examples.append(
        create_training_data_format("โกรธจนขำอะชีวิต!", ["โกรธ", "ขำขัน"], "classification")
    )
    
    # Instruction format for LLM
    training_examples.append(
        create_training_data_format("ประชดหนักมากจนรู้สึกแย่", ["ประชด", "เสียใจ"], "instruction")
    )
    
    for i, example in enumerate(training_examples):
        print(f"ตัวอย่าง {i+1}:")
        print(json.dumps(example, ensure_ascii=False, indent=2))
        print()

if __name__ == "__main__":
    demo_detailed_sentiment_analysis()
