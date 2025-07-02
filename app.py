import argparse
import os
import json
import subprocess
from glob import glob
from tqdm import tqdm
# เปลี่ยนจาก ml_sentiment_analysis เป็น sentiment_integration สำหรับระบบใหม่
try:
    from sentiment_integration import analyze_detailed_sentiment, enhanced_analyze_sentiment
    DETAILED_SENTIMENT_AVAILABLE = True
except ImportError:
    # Fallback ไปยังระบบเดิมถ้าโมดูลใหม่ไม่พร้อม
    try:
        from ml_sentiment_analysis import analyze_sentiment
        DETAILED_SENTIMENT_AVAILABLE = False
    except ImportError:
        def analyze_sentiment(text):
            return {"sentiment": "neutral", "confidence": 0.0, "sentiment_score": 0.0}
        DETAILED_SENTIMENT_AVAILABLE = False

import time
import random
import hashlib
import re

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

# === EMOTION PATTERNS ===
EMOTION_PATTERNS = {
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

# === COMPREHENSIVE CONTEXT PATTERNS ===
CONTEXT_PATTERNS = {
    # === ระดับความเป็นทางการ ===
    "formal": ["ครับ", "ค่ะ", "คะ", "ขอ", "กรุณา", "สวัสดี", "ขอบคุณ", "ท่าน", "คุณ", "พี่", "น้อง", "เรียน", "ด้วยความเคารพ"],
    "informal": ["นะ", "เนอะ", "อะ", "เอ้ย", "เออ", "ของ", "555", "ฮา", "จ้ะ", "จ๋า", "ว่ะ", "วะ", "เฮ้ย"],
    "slang": ["โคตร", "เฟี้ยว", "เทพ", "แม่ง", "ควย", "บิน", "เฟี้ยม", "ชิบ", "เด็ด", "ปัง", "ห่วย", "ซวย"],
    
    # === ความสัมพันธ์ส่วนตัว ===
    "personal": ["กู", "มึง", "เรา", "ฉัน", "คิด", "รู้สึก", "ใจ", "หัวใจ", "ตัวเอง", "ส่วนตัว"],
    "intimate": ["ที่รัก", "หวานใจ", "ดาร์ลิ่ง", "ฮันนี่", "เบบี้", "คนดี", "เสือ", "หนูเอง"],
    "friendly": ["เพื่อน", "เฟร้น", "พวกเรา", "แก๊ง", "กลุ่ม", "คนเก่า", "พี่น้อง"],
    
    # === บริบทสื่อสังคม ===
    "social_media": ["แชร์", "ไลค์", "คอมเมนต์", "โพสต์", "แท็ก", "เฟสบุ๊ค", "ไอจี", "ทวิตเตอร์", "ติ๊กต๊อก", "ยูทูป"],
    "news_media": ["ข่าว", "รายงาน", "แจ้งข่าว", "ข้อมูล", "อัปเดต", "ประกาศ", "แถลงการณ์", "สำคัญ", "ด่วน"],
    "review": ["รีวิว", "ทดลอง", "ใช้ดู", "ลอง", "ประสบการณ์", "คุณภาพ", "บริการ", "สินค้า", "ร้าน"],
    
    # === บริบทอารมณ์ ===
    "complaint": ["บ่น", "ร้องเรียน", "แจ้งปัญหา", "ไม่ได้", "เสีย", "ห่วย", "แย่", "ผิดพลาด", "ช้า"],
    "praise": ["ชม", "ยกย่อง", "ดี", "เยี่ยม", "ประทับใจ", "ชอบ", "รัก", "สุดยอด", "เจ๋ง", "เทพ"],
    "question": ["ครับ", "คะ", "มั้ย", "หรือ", "ไหม", "อะไร", "ทำไม", "ยังไง", "เมื่อไหร่", "ที่ไหน"],
    
    # === บริบทสถานการณ์ ===
    "emergency": ["ด่วน", "เร่งด่วน", "ฉุกเฉิน", "ช่วย", "ปัญหา", "เสีย", "พัง", "อันตราย", "วิกฤต"],
    "celebration": ["ยินดี", "แสดงความยินดี", "ขอแสดงความยินดี", "ดีใจ", "ปลื้มปีติ", "เฮง", "โชคดี"],
    "condolence": ["เสียใจ", "แสดงความเสียใจ", "ขอแสดงความเสียใจ", "เศร้า", "อาลัย", "คิดถึง"],
    
    # === บริบทวัฒนธรรม ===
    "religious": ["บุญ", "กรรม", "ธรรม", "พระ", "วัด", "นมัสการ", "ไหว้", "ศาสนา", "บาป", "กุศล"],
    "traditional": ["ประเพณี", "วัฒนธรรม", "ไทย", "โบราณ", "ดั้งเดิม", "ภูมิปัญญา", "ชาวบ้าน"],
    "modern": ["ทันสมัย", "โมเดิร์น", "ไฮเทค", "ดิจิทัล", "ออนไลน์", "แอป", "ไอที", "เทคโนโลยี"],
    
    # === บริบทภูมิศาสตร์ ===
    "central": ["กรุงเทพ", "กทม", "เมืองหลวง", "ภาคกลาง", "จังหวัดใกล้เคียง"],
    "northern": ["เชียงใหม่", "ภาคเหนือ", "ล้านนา", "คำเมือง", "นา", "ป่า"],
    "southern": ["ใต้", "ภาคใต้", "ทะเล", "ปลา", "ยางพารา", "ปาล์ม"],
    "northeastern": ["อีสาน", "ภาคอีสาน", "ส้มตำ", "ลาว", "ข้าวเหนียว", "แจ่ว"],
    
    # === บริบทอายุ/รุ่น ===
    "gen_z": ["ปัง", "เด็ด", "ฟิน", "ชิล", "เฟล็กซ์", "โบ", "ลิต", "ไวบ์", "คอนเทนต์"],
    "millennial": ["โอเค", "เฟส", "ไลน์", "อินสตา", "ซีรี่ย์", "ยูทูป", "กูเกิล"],
    "gen_x": ["จริงหรือเปล่า", "ไม่เชื่อ", "สมัยก่อน", "ตอนหนุ่ม", "ปัจจุบัน"],
    
    # === บริบทวิชาชีพ ===
    "business": ["ธุรกิจ", "การตลาด", "ขาย", "ลูกค้า", "กำไร", "ขาดทุน", "ลงทุน"],
    "education": ["เรียน", "สอน", "ครู", "นักเรียน", "นักศึกษา", "การศึกษา", "วิชา"],
    "healthcare": ["หมอ", "คลินิก", "โรงพยาบาล", "ยา", "รักษา", "สุขภาพ", "ป่วย"],
    "government": ["ราชการ", "รัฐบาล", "นโยบาย", "กฎหมาย", "ระเบียบ", "ข้าราชการ"],
    
    # === บริบทเทคโนโลยี ===
    "gaming": ["เกม", "เล่น", "แรงค์", "สกิล", "อัพ", "เลเวล", "PvP", "ไอเทม"],
    "tech": ["โค้ด", "โปรแกรม", "แอป", "เว็บ", "AI", "มือถือ", "คอม", "ซอฟต์แวร์"],
    "crypto": ["คริปโต", "บิทคอยน์", "เหรียญ", "เทรด", "ขุด", "วอลเล็ต", "NFT"],
    
    # === บริบทความบันเทิง ===
    "music": ["เพลง", "ศิลปิน", "คอนเสิร์ต", "อัลบั้ม", "เนื้อเพลง", "ดนตรี", "แร็ป"],
    "movie": ["หนัง", "ซีรี่ย์", "นักแสดง", "ผู้กำกับ", "โรงหนัง", "Netflix", "ดูหนัง"],
    "sports": ["กีฬา", "ทีม", "แข่ง", "ชนะ", "แพ้", "ฟุตบอล", "บาส", "วิ่ง"],
    
    # === บริบทความรัก ===
    "romance": ["คู่รัก", "แฟน", "หวาน", "โรแมนติก", "จีบ", "เดท", "คบ", "รัก"],
    "breakup": ["เลิกกัน", "ทิ้ง", "หลอก", "นอกใจ", "เศร้าใจ", "คิดถึง", "หมดรัก"],
    
    # === บริบทการเงิน ===
    "financial": ["เงิน", "ค่าใช้จ่าย", "เงินเดือน", "หนี้", "ออม", "ลงทุน", "ราคา", "แพง"],
    "shopping": ["ซื้อ", "ขาย", "ช้อป", "ลด", "โปร", "ฟรี", "ส่วนลด", "เซล"],
    
    # === บริบทสุขภาพ ===
    "fitness": ["ออกกำลัง", "ฟิต", "ยิม", "วิ่ง", "ลดน้ำหนัก", "กล้ามเนื้อ", "โยคะ"],
    "food": ["อาหาร", "กิน", "อร่อย", "ทำอาหาร", "ร้านอาหาร", "เมนู", "หิว"],
    
    # === บริบทการเดินทาง ===
    "travel": ["เที่ยว", "ท่องเที่ยว", "เดินทาง", "โรงแรม", "ตั้วเป็น", "ที่เที่ยว", "วิว"]
}

# === INTENSITY PATTERNS ===
INTENSITY_PATTERNS = {
    "high": ["มาก", "เลย", "สุด", "แรง", "หนัก", "โคตร", "แสน", "สาหัส", "เป็นบ้า", "จริงๆ"],
    "medium": ["พอ", "ค่อนข้าง", "ปานกลาง", "ใช้ได้", "โอเค"],
    "low": ["เล็กน้อย", "นิดหน่อย", "เบาๆ", "นิดเดียว", "ไม่มาก"]
}

# --- Helper: Run yt-dlp for a single link ---
def run_ytdlp(link, outtmpl=None):
    video_id = link.split('v=')[-1].split('&')[0]
    # Always save to data/ directory
    infojson = f"data/{video_id}.info.json"
    if os.path.exists(infojson):
        return infojson
    # Ensure data/ directory exists
    if not os.path.exists('data'):
        os.makedirs('data')
    # Always use outtmpl to force yt-dlp to save in data/
    outtmpl = outtmpl or 'data/%(id)s.%(ext)s'
    cmd = [
        'python', '-m', 'yt_dlp',
        '--write-comments',
        '--skip-download',
        link,
        '-o', outtmpl
    ]
    subprocess.run(cmd, check=True)
    # Find the .info.json file in data/
    files = glob(f"data/*{video_id}*.info.json")
    return files[0] if files else None

def mask_author(author):
    if not author:
        return None
    return hashlib.sha256(author.encode('utf-8')).hexdigest()[:12]

def clean_text_privacy(text):
    if not text:
        return text
    # Mask phone numbers
    text = re.sub(r'\b\d{8,}\b', '[MASKED_PHONE]', text)
    # Mask emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[MASKED_EMAIL]', text)
    # Mask URLs
    text = re.sub(r'https?://\S+', '[MASKED_URL]', text)
    text = re.sub(r'www\.\S+', '[MASKED_URL]', text)
    return text

# --- Helper: Recursively flatten comments and replies ---
def flatten_comments(comments, video_id, parent_id=None, privacy_mode='none', sentiment_mode='basic', detailed_mode='single'):
    rows = []
    for c in comments:
        comment_text = c.get('text', '')
        
        # Sentiment analysis based on mode
        if sentiment_mode == 'detailed' and DETAILED_SENTIMENT_AVAILABLE:
            # ใช้ระบบ ML (detailed sentiment analysis)
            sentiment_result = analyze_detailed_sentiment(
                comment_text, 
                mode=detailed_mode,  # 'single' หรือ 'multi'
                threshold=0.3,
                include_scores=True
            )
            # แปลงเป็น format ที่เข้ากับ schema เดิม
            sentiment_basic = sentiment_result.get('sentiment', 'neutral')
            # confidence: ถ้า ML คืน confidence ให้ใช้, ถ้าไม่มีให้ใช้ max score ของ detailed_emotions
            confidence = sentiment_result.get('confidence')
            if confidence is None:
                # ลองหา max score จาก all_scores ของ detailed_emotions
                all_scores = sentiment_result.get('all_scores', {})
                detailed_emotions = sentiment_result.get('detailed_emotions', [])
                if detailed_emotions and all_scores:
                    confs = [all_scores.get(em, 0.0) for em in detailed_emotions if all_scores.get(em, 0.0) > 0.0]
                    confidence = max(confs) if confs else 0.0
                else:
                    confidence = 0.0
            sentiment_score = _sentiment_to_score(sentiment_basic)

        elif sentiment_mode == 'enhanced' and DETAILED_SENTIMENT_AVAILABLE:
            # ใช้ enhanced analysis (backward compatible)
            sentiment_result = enhanced_analyze_sentiment(comment_text)
            sentiment_basic = sentiment_result.get('sentiment', 'neutral')
            confidence = sentiment_result.get('confidence', 0.0)
            sentiment_score = sentiment_result.get('sentiment_score', 0.0)

        else:
            # ใช้ระบบ built-in (pattern matching) เมื่อไม่มี external modules
            sentiment_result = analyze_sentiment_builtin(
                comment_text, 
                mode=detailed_mode if sentiment_mode == 'detailed' else 'single',
                threshold=0.3
            )
            sentiment_basic = sentiment_result.get('sentiment', 'neutral')
            confidence = sentiment_result.get('confidence', 0.0)
            sentiment_score = sentiment_result.get('sentiment_score', 0.0)
        
        # Privacy handling
        author = c.get('author')
        if privacy_mode == 'mask':
            author = mask_author(author)
        elif privacy_mode == 'remove':
            author = None
        text = c.get('text')
        if privacy_mode in ('mask', 'remove'):
            text = clean_text_privacy(text)
        
        # One-hot encoding for pos/neu/neg/other
        pos = 1 if sentiment_basic == 'positive' else 0
        neu = 1 if sentiment_basic == 'neutral' else 0
        neg = 1 if sentiment_basic == 'negative' else 0
        other = 1 if sentiment_basic not in ('positive', 'neutral', 'negative') else 0
        # Base row structure
        row = {
            'video_id': video_id,
            'comment_id': c.get('id'),
            'parent_id': parent_id,
            'author': author,
            'text': text,
            'like_count': c.get('like_count'),
            'published': c.get('published'),
            'is_reply': parent_id is not None,
            # --- มาตรฐาน sentiment schema ---
            'sentiment': sentiment_basic,
            'confidence': confidence,
            'sentiment_score': sentiment_score,
            'pos': pos,
            'neu': neu,
            'neg': neg,
            'other': other,
            'model_type': sentiment_result.get('model_type', 'unknown'),
            'privacy_notice': 'This dataset is for research only. Do not use for commercial or personal identification.'
        }
        
        # เพิ่มข้อมูล detailed sentiment ถ้าเปิดใช้งาน
        if sentiment_mode == 'detailed':
            if DETAILED_SENTIMENT_AVAILABLE:
                # ใช้ข้อมูลจาก external detailed sentiment module
                row.update({
                    'detailed_sentiment_analysis': sentiment_result,
                    'analysis_mode': detailed_mode,
                    'detailed_emotions': sentiment_result.get('detailed_emotions', []) if detailed_mode == 'multi' else [sentiment_result.get('detailed_emotion', '')],
                    'emotion_groups': sentiment_result.get('emotion_groups', []) if detailed_mode == 'multi' else [sentiment_result.get('emotion_group', '')],
                    'context': sentiment_result.get('context', 'unknown')
                })
            else:
                # ใช้ built-in patterns
                if detailed_mode == 'multi':
                    row.update({
                        'detailed_sentiment_analysis': sentiment_result,
                        'analysis_mode': detailed_mode,
                        'detailed_emotions': sentiment_result.get('detailed_emotions', []),
                        'emotion_groups': sentiment_result.get('emotion_groups', []),
                        'context': sentiment_result.get('context', 'unknown')
                    })
                else:
                    row.update({
                        'detailed_sentiment_analysis': sentiment_result,
                        'analysis_mode': detailed_mode,
                        'detailed_emotions': [sentiment_result.get('detailed_emotion', '')],
                        'emotion_groups': [sentiment_result.get('emotion_group', '')],
                        'context': sentiment_result.get('context', 'unknown')
                    })
        
        elif sentiment_mode == 'enhanced':
            if DETAILED_SENTIMENT_AVAILABLE:
                # ใช้ข้อมูลจาก external enhanced module
                row.update({
                    'detailed_emotion': sentiment_result.get('detailed_emotion', ''),
                    'emotion_group': sentiment_result.get('emotion_group', ''),
                    'context': sentiment_result.get('context', 'unknown')
                })
            else:
                # ใช้ built-in patterns สำหรับ enhanced mode
                row.update({
                    'detailed_emotion': sentiment_result.get('detailed_emotion', ''),
                    'emotion_group': sentiment_result.get('emotion_group', ''),
                    'context': sentiment_result.get('context', 'unknown')
                })
        
        rows.append(row)
        
        # Recursively add replies
        replies = c.get('replies', [])
        if replies:
            rows.extend(flatten_comments(replies, video_id, parent_id=c.get('id'), privacy_mode=privacy_mode, sentiment_mode=sentiment_mode, detailed_mode=detailed_mode))
    return rows

def _sentiment_to_score(sentiment: str) -> float:
    """แปลง sentiment เป็น score สำหรับ backward compatibility"""
    if sentiment == "positive":
        return 0.7
    elif sentiment == "negative":
        return -0.7
    else:
        return 0.0

# === BUILT-IN SENTIMENT ANALYSIS FUNCTIONS ===

def extract_emojis(text):
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

def calculate_emotion_scores(text):
    """คำนวณคะแนนสำหรับแต่ละอารมณ์"""
    if not text:
        return {}
    
    clean_text = text.lower()
    emojis = extract_emojis(text)
    emotion_scores = {}
    
    for emotion, config in EMOTION_PATTERNS.items():
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
        intensity_bonus = calculate_intensity_bonus(clean_text)
        score *= (1 + intensity_bonus)
        
        emotion_scores[emotion] = min(score, 5.0)  # จำกัดคะแนนสูงสุด
    
    return emotion_scores

def calculate_intensity_bonus(text):
    """คำนวณ bonus จากความเข้มข้นของการแสดงออก"""
    bonus = 0.0
    
    for intensity, words in INTENSITY_PATTERNS.items():
        for word in words:
            if word in text:
                if intensity == "high":
                    bonus += 0.5
                elif intensity == "medium":
                    bonus += 0.2
                elif intensity == "low":
                    bonus += 0.1
    
    return min(bonus, 1.0)  # จำกัด bonus สูงสุด

def normalize_scores(scores):
    """normalize คะแนนให้อยู่ในช่วง 0-1"""
    if not scores:
        return {}
    
    max_score = max(scores.values())
    if max_score == 0:
        return scores
    
    return {emotion: score / max_score for emotion, score in scores.items()}

def determine_context(text):
    """กำหนดบริบทการใช้ภาษาแบบครอบคลุม"""
    if not text:
        return {
            "primary_context": "neutral",
            "all_contexts": {},
            "formality_level": "neutral",
            "social_setting": "general",
            "emotional_tone": "neutral",
            "generation": "unknown",
            "profession": "general"
        }
    
    clean_text = text.lower()
    context_scores = {}
    
    # คำนวณคะแนนสำหรับแต่ละบริบท
    for context, words in CONTEXT_PATTERNS.items():
        score = 0
        for word in words:
            if word in clean_text:
                score += 1
        if score > 0:
            context_scores[context] = score
    
    if not context_scores:
        return {
            "primary_context": "neutral",
            "all_contexts": {},
            "formality_level": "neutral",
            "social_setting": "general",
            "emotional_tone": "neutral",
            "generation": "unknown",
            "profession": "general"
        }
    
    # หาบริบทหลัก
    primary_context = max(context_scores, key=context_scores.get)
    
    # วิเคราะห์ระดับความเป็นทางการ
    formality_score = {
        "formal": context_scores.get("formal", 0),
        "informal": context_scores.get("informal", 0),
        "slang": context_scores.get("slang", 0)
    }
    formality_level = max(formality_score, key=formality_score.get) if any(formality_score.values()) else "neutral"
    
    # วิเคราะห์การตั้งค่าทางสังคม
    social_contexts = ["social_media", "news_media", "review", "business", "education", "healthcare", "government"]
    social_scores = {ctx: context_scores.get(ctx, 0) for ctx in social_contexts}
    social_setting = max(social_scores, key=social_scores.get) if any(social_scores.values()) else "general"
    
    # วิเคราะห์โทนอารมณ์
    emotional_contexts = ["complaint", "praise", "emergency", "celebration", "condolence", "question"]
    emotional_scores = {ctx: context_scores.get(ctx, 0) for ctx in emotional_contexts}
    emotional_tone = max(emotional_scores, key=emotional_scores.get) if any(emotional_scores.values()) else "neutral"
    
    # วิเคราะห์รุ่น/อายุ
    generation_contexts = ["gen_z", "millennial", "gen_x"]
    generation_scores = {ctx: context_scores.get(ctx, 0) for ctx in generation_contexts}
    generation = max(generation_scores, key=generation_scores.get) if any(generation_scores.values()) else "unknown"
    
    # วิเคราะห์วิชาชีพ
    profession_contexts = ["business", "education", "healthcare", "government", "tech", "gaming"]
    profession_scores = {ctx: context_scores.get(ctx, 0) for ctx in profession_contexts}
    profession = max(profession_scores, key=profession_scores.get) if any(profession_scores.values()) else "general"
    
    return {
        "primary_context": primary_context,
        "all_contexts": context_scores,
        "formality_level": formality_level,
        "social_setting": social_setting,
        "emotional_tone": emotional_tone,
        "generation": generation,
        "profession": profession,
        "context_confidence": round(context_scores[primary_context] / len(clean_text.split()) if clean_text.split() else 0, 3)
    }

def analyze_sentiment_builtin(text, mode='single', threshold=0.3):
    """วิเคราะห์ sentiment แบบ built-in (ไม่ต้องพึ่งพาไฟล์อื่น)"""
    if not text or not text.strip():
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "sentiment_score": 0.0,
            "detailed_emotion": "เฉย ๆ",
            "emotion_group": "Neutral",
            "context": {
                "primary_context": "neutral",
                "formality_level": "neutral",
                "social_setting": "general",
                "emotional_tone": "neutral"
            },
            "model_type": "builtin_pattern_matching"
        }
    
    # คำนวณคะแนนสำหรับแต่ละอารมณ์
    raw_scores = calculate_emotion_scores(text)
    normalized_scores = normalize_scores(raw_scores)
    
    # วิเคราะห์บริบทแบบครอบคลุม
    context_data = determine_context(text)
    context_patterns = analyze_context_patterns(text)
    context_insights = get_context_insights(context_data)
    
    if mode == 'single':
        # Single label mode
        if not normalized_scores or max(normalized_scores.values(), default=0.0) == 0.0:
            predicted_label = "เฉย ๆ"
            confidence = 0.0
        else:
            predicted_label = max(normalized_scores, key=normalized_scores.get)
            # ถ้าคะแนนสูงสุดเป็น 0.0 ให้ถือว่าเป็น neutral
            if normalized_scores[predicted_label] == 0.0:
                predicted_label = "เฉย ๆ"
                confidence = 0.0
            else:
                confidence = normalized_scores[predicted_label]

        # กำหนดกลุ่มและ sentiment พื้นฐาน
        group = LABEL_TO_GROUP.get(predicted_label, "Neutral")
        basic_sentiment = "positive" if group == "Positive" else "negative" if group == "Negative" else "neutral"
        sentiment_score = _sentiment_to_score(basic_sentiment)

        result = {
            "sentiment": basic_sentiment,
            "confidence": round(confidence, 3),
            "sentiment_score": sentiment_score,
            "detailed_emotion": predicted_label,
            "emotion_group": group,
            "context": context_data,
            "context_patterns": context_patterns,
            "context_insights": context_insights,
            "scores": {k: round(v, 3) for k, v in normalized_scores.items()},
            "model_type": "builtin_pattern_matching"
        }

    else:  # multi label mode
        # Multi-label mode
        predicted_labels = []
        for emotion, score in normalized_scores.items():
            if score >= threshold:
                predicted_labels.append(emotion)

        # ถ้าไม่มี label ที่ผ่าน threshold หรือทุกค่าเป็น 0.0 ให้ default เป็น "เฉย ๆ"
        if (not predicted_labels) or all(normalized_scores.get(label, 0.0) == 0.0 for label in predicted_labels):
            predicted_labels = ["เฉย ๆ"]

        # กำหนดกลุ่มและ sentiment พื้นฐาน
        groups = list(set(LABEL_TO_GROUP.get(label, "Neutral") for label in predicted_labels))

        # กำหนด basic sentiment จากกลุ่มหลัก
        if "Positive" in groups:
            basic_sentiment = "positive"
        elif "Negative" in groups:
            basic_sentiment = "negative"
        else:
            basic_sentiment = "neutral"

        sentiment_score = _sentiment_to_score(basic_sentiment)
        # confidence = max ของ label ที่ไม่ใช่ 0.0 ถ้ามี
        nonzero_conf = [normalized_scores.get(label, 0.0) for label in predicted_labels if normalized_scores.get(label, 0.0) > 0.0]
        max_confidence = max(nonzero_conf) if nonzero_conf else 0.0

        result = {
            "sentiment": basic_sentiment,
            "confidence": round(max_confidence, 3),
            "sentiment_score": sentiment_score,
            "detailed_emotions": predicted_labels,
            "emotion_groups": groups,
            "context": context_data,
            "context_patterns": context_patterns,
            "context_insights": context_insights,
            "scores": {k: round(v, 3) for k, v in normalized_scores.items()},
            "threshold": threshold,
            "model_type": "builtin_pattern_matching"
        }

    return result

# --- Main ---

# --- Move show_sentiment_statistics above main() to avoid NameError ---
def show_sentiment_statistics(rows, detailed_mode):
    """Show summary statistics for sentiment analysis"""
    if not rows:
        return
    print(f"\n📊 Sentiment Analysis Statistics:")
    print(f"   Total comments analyzed: {len(rows)}")
    print(f"   Analysis mode: {detailed_mode}")
    # Basic sentiment counts
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    emotion_counts = {}
    group_counts = {}
    context_counts = {
        "primary_context": {},
        "formality_level": {},
        "social_setting": {},
        "emotional_tone": {},
        "generation": {},
        "profession": {}
    }
    for row in rows:
        # Basic sentiment
        sentiment = row.get('sentiment', 'neutral')
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
        # Detailed emotions (if available)
        if detailed_mode == 'single':
            emotions = row.get('detailed_emotions', [])
            if not emotions:
                emotion = row.get('detailed_emotion', '')
                emotions = [emotion] if emotion else ['']
            groups = row.get('emotion_groups', [])
            if not groups:
                group = row.get('emotion_group', '')
                groups = [group] if group else ['']
        else:  # multi
            emotions = row.get('detailed_emotions', [])
            groups = row.get('emotion_groups', [])
        for emotion in emotions:
            if emotion and emotion.strip():
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        for group in groups:
            if group and group.strip():
                group_counts[group] = group_counts.get(group, 0) + 1
        # Context analysis (รองรับทั้งแบบเก่าและใหม่)
        context = row.get('context', {})
        if isinstance(context, dict):
            for context_type in context_counts:
                if context_type in context:
                    value = context[context_type]
                    if value and str(value).strip():
                        context_counts[context_type][value] = context_counts[context_type].get(value, 0) + 1
        elif isinstance(context, str):
            if context and context.strip():
                context_counts["primary_context"][context] = context_counts["primary_context"].get(context, 0) + 1
    print(f"   Basic sentiment distribution:")
    for sentiment, count in sentiment_counts.items():
        percentage = (count / len(rows)) * 100
        print(f"     {sentiment}: {count} ({percentage:.1f}%)")
    if emotion_counts:
        print(f"   Top emotions detected:")
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        for emotion, count in sorted_emotions:
            percentage = (count / len(rows)) * 100
            print(f"     {emotion}: {count} ({percentage:.1f}%)")
    if group_counts:
        print(f"   Emotion group distribution:")
        for group, count in group_counts.items():
            percentage = (count / len(rows)) * 100
            print(f"     {group}: {count} ({percentage:.1f}%)")
    print(f"   📋 Context Analysis:")
    if context_counts["formality_level"]:
        print(f"     Formality levels:")
        for level, count in context_counts["formality_level"].items():
            percentage = (count / len(rows)) * 100
            print(f"       {level}: {count} ({percentage:.1f}%)")
    if context_counts["social_setting"]:
        print(f"     Social settings:")
        sorted_social = sorted(context_counts["social_setting"].items(), key=lambda x: x[1], reverse=True)[:5]
        for setting, count in sorted_social:
            percentage = (count / len(rows)) * 100
            print(f"       {setting}: {count} ({percentage:.1f}%)")
    if context_counts["emotional_tone"]:
        print(f"     Emotional tones:")
        sorted_tones = sorted(context_counts["emotional_tone"].items(), key=lambda x: x[1], reverse=True)[:5]
        for tone, count in sorted_tones:
            percentage = (count / len(rows)) * 100
            print(f"       {tone}: {count} ({percentage:.1f}%)")
    if context_counts["generation"]:
        print(f"     Generational markers:")
        for generation, count in context_counts["generation"].items():
            percentage = (count / len(rows)) * 100
            print(f"       {generation}: {count} ({percentage:.1f}%)")
    if context_counts["profession"]:
        print(f"     Professional contexts:")
        sorted_professions = sorted(context_counts["profession"].items(), key=lambda x: x[1], reverse=True)[:5]
        for profession, count in sorted_professions:
            percentage = (count / len(rows)) * 100
            print(f"       {profession}: {count} ({percentage:.1f}%)")
    if context_counts["primary_context"]:
        print(f"     Primary contexts:")
        sorted_contexts = sorted(context_counts["primary_context"].items(), key=lambda x: x[1], reverse=True)[:5]
        for context, count in sorted_contexts:
            percentage = (count / len(rows)) * 100
            print(f"       {context}: {count} ({percentage:.1f}%)")
    model_types = {}
    for row in rows:
        model_type = row.get('model_type', 'unknown')
        model_types[model_type] = model_types.get(model_type, 0) + 1
    if model_types:
        print(f"   Model types used:")
        for model, count in model_types.items():
            percentage = (count / len(rows)) * 100
            print(f"     {model}: {count} ({percentage:.1f}%)")
    print()

def main():
    parser = argparse.ArgumentParser(description='Extract YouTube comments using yt-dlp and export as JSONL with advanced Thai sentiment analysis.')
    parser.add_argument('--links', default='youtube_real_links_1500.txt', help='Text file with YouTube links (one per line)')
    parser.add_argument('--output', default='youtube_comments.jsonl', help='Output JSONL file')
    parser.add_argument('--privacy', default='none', choices=['none', 'mask', 'remove'], help='Privacy mode: mask (hash author, mask PII), remove (no author, mask PII), none (no privacy)')
    # Sentiment analysis options
    parser.add_argument('--sentiment-mode', default='basic', 
                       choices=['basic', 'enhanced', 'detailed'], 
                       help='Sentiment analysis mode: basic (old system), enhanced (new system, backward compatible), detailed (full multi-emotion analysis)')
    parser.add_argument('--detailed-mode', default='single', 
                       choices=['single', 'multi'],
                       help='For detailed sentiment: single (single-label classification) or multi (multi-label classification)')
    parser.add_argument('--no-sentiment', action='store_true', 
                       help='Disable sentiment analysis completely')
    import sys
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n[ERROR] กรุณาระบุ arguments ที่จำเป็น เช่น --links <ไฟล์ลิงก์ YouTube> หรือดูตัวอย่างการใช้งานด้านบน\n")
        sys.exit(1)
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse throws SystemExit on error, catch and print friendlier message
        if e.code != 0:
            print("\n[ERROR] พบ argument ที่ไม่ถูกต้อง หรือมี argument แปลกปลอม\nกรุณาตรวจสอบคำสั่งและดูตัวอย่างการใช้งานด้านบน\n")
        raise
    # --- Main processing logic ---
    # 1. Load YouTube links
    try:
        with open(args.links, encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[ERROR] ไม่สามารถเปิดไฟล์ลิงก์: {args.links} : {e}")
        return
    # --- เพิ่มโหมด: ใช้ไฟล์ .info.json ที่มีอยู่แล้ว หรือ process ใหม่ ---
    all_rows = []
    for link in tqdm(links, desc="Processing YouTube links"):
        try:
            # ดึง video_id จากลิงก์
            video_id = link.split('v=')[-1].split('&')[0]
            # หาไฟล์ .info.json ที่มีอยู่ใน data/ หรือโฟลเดอร์ปัจจุบัน
            infojson_candidates = [
                f"data/{video_id}.info.json",
                f"{video_id}.info.json"
            ]
            infojson = None
            for candidate in infojson_candidates:
                if os.path.exists(candidate):
                    infojson = candidate
                    break
            # ถ้าไม่เจอ ให้รัน yt-dlp เพื่อโหลดใหม่
            if not infojson:
                infojson = run_ytdlp(link)
                if not infojson or not os.path.exists(infojson):
                    print(f"[WARN] ไม่พบไฟล์ข้อมูลสำหรับ {link}")
                    continue
            with open(infojson, encoding='utf-8') as jf:
                info = json.load(jf)
            comments = info.get('comments', [])
            video_id = info.get('id', video_id)
            if args.no_sentiment:
                rows = flatten_comments_no_sentiment(comments, video_id, privacy_mode=args.privacy)
            else:
                rows = flatten_comments(
                    comments, video_id,
                    privacy_mode=args.privacy,
                    sentiment_mode=args.sentiment_mode,
                    detailed_mode=args.detailed_mode
                )
            all_rows.extend(rows)
        except Exception as e:
            print(f"[ERROR] ล้มเหลวที่ลิงก์ {link}: {e}")
    # 4. Write output
    try:
        with open(args.output, 'w', encoding='utf-8') as out:
            for row in all_rows:
                out.write(json.dumps(row, ensure_ascii=False) + '\n')
        print(f"\n[INFO] บันทึกผลลัพธ์ที่ {args.output} แล้ว จำนวน {len(all_rows)} records")
    except Exception as e:
        print(f"[ERROR] ไม่สามารถเขียนไฟล์ output: {args.output} : {e}")
        return
    # 5. Show statistics (optional)
    if not args.no_sentiment:
        show_sentiment_statistics(all_rows, args.detailed_mode)

# --- Main entry point ---
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[FATAL ERROR] ไม่สามารถรันโปรแกรมได้: ", e)
        import sys
        sys.exit(1)

def flatten_comments_no_sentiment(comments, video_id, parent_id=None, privacy_mode='none'):
    """Flatten comments without sentiment analysis (for performance/testing)"""
    rows = []
    for c in comments:
        # Privacy handling
        author = c.get('author')
        if privacy_mode == 'mask':
            author = mask_author(author)
        elif privacy_mode == 'remove':
            author = None
        text = c.get('text')
        if privacy_mode in ('mask', 'remove'):
            text = clean_text_privacy(text)
        
        # Default: all 0, only neu=1 (since no sentiment analysis)
        row = {
            'video_id': video_id,
            'comment_id': c.get('id'),
            'parent_id': parent_id,
            'author': author,
            'text': text,
            'like_count': c.get('like_count'),
            'published': c.get('published'),
            'is_reply': parent_id is not None,
            'pos': 0,
            'neu': 1,
            'neg': 0,
            'privacy_notice': 'This dataset is for research only. Do not use for commercial or personal identification.'
        }
        rows.append(row)
        
        # Recursively add replies
        replies = c.get('replies', [])
        if replies:
            rows.extend(flatten_comments_no_sentiment(replies, video_id, parent_id=c.get('id'), privacy_mode=privacy_mode))
    return rows

def show_sentiment_statistics(rows, detailed_mode):
    """Show summary statistics for sentiment analysis"""
    if not rows:
        return
    
    print(f"\n📊 Sentiment Analysis Statistics:")
    print(f"   Total comments analyzed: {len(rows)}")
    print(f"   Analysis mode: {detailed_mode}")
    
    # Basic sentiment counts
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    emotion_counts = {}
    group_counts = {}
    context_counts = {
        "primary_context": {},
        "formality_level": {},
        "social_setting": {},
        "emotional_tone": {},
        "generation": {},
        "profession": {}
    }
    
    for row in rows:
        # Basic sentiment
        sentiment = row.get('sentiment', 'neutral')
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
        
        # Detailed emotions (if available)
        if detailed_mode == 'single':
            # ดึงอารมณ์จาก detailed_emotions array หรือ detailed_emotion field
            emotions = row.get('detailed_emotions', [])
            if not emotions:
                emotion = row.get('detailed_emotion', '')
                emotions = [emotion] if emotion else ['']
            
            groups = row.get('emotion_groups', [])
            if not groups:
                group = row.get('emotion_group', '')
                groups = [group] if group else ['']
        else:  # multi
            emotions = row.get('detailed_emotions', [])
            groups = row.get('emotion_groups', [])
        
        for emotion in emotions:
            if emotion and emotion.strip():
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        for group in groups:
            if group and group.strip():
                group_counts[group] = group_counts.get(group, 0) + 1
        
        # Context analysis (รองรับทั้งแบบเก่าและใหม่)
        context = row.get('context', {})
        if isinstance(context, dict):
            # แบบใหม่ที่ละเอียด
            for context_type in context_counts:
                if context_type in context:
                    value = context[context_type]
                    if value and str(value).strip():
                        context_counts[context_type][value] = context_counts[context_type].get(value, 0) + 1
        elif isinstance(context, str):
            # แบบเก่า
            if context and context.strip():
                context_counts["primary_context"][context] = context_counts["primary_context"].get(context, 0) + 1
    
    print(f"   Basic sentiment distribution:")
    for sentiment, count in sentiment_counts.items():
        percentage = (count / len(rows)) * 100
        print(f"     {sentiment}: {count} ({percentage:.1f}%)")
    
    if emotion_counts:
        print(f"   Top emotions detected:")
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        for emotion, count in sorted_emotions:
            percentage = (count / len(rows)) * 100
            print(f"     {emotion}: {count} ({percentage:.1f}%)")
    
    if group_counts:
        print(f"   Emotion group distribution:")
        for group, count in group_counts.items():
            percentage = (count / len(rows)) * 100
            print(f"     {group}: {count} ({percentage:.1f}%)")
    
    # แสดงสถิติบริบทแบบละเอียด
    print(f"   📋 Context Analysis:")
    
    # ระดับความเป็นทางการ
    if context_counts["formality_level"]:
        print(f"     Formality levels:")
        for level, count in context_counts["formality_level"].items():
            percentage = (count / len(rows)) * 100
            print(f"       {level}: {count} ({percentage:.1f}%)")
    
    # การตั้งค่าทางสังคม
    if context_counts["social_setting"]:
        print(f"     Social settings:")
        sorted_social = sorted(context_counts["social_setting"].items(), key=lambda x: x[1], reverse=True)[:5]
        for setting, count in sorted_social:
            percentage = (count / len(rows)) * 100
            print(f"       {setting}: {count} ({percentage:.1f}%)")
    
    # โทนอารมณ์
    if context_counts["emotional_tone"]:
        print(f"     Emotional tones:")
        sorted_tones = sorted(context_counts["emotional_tone"].items(), key=lambda x: x[1], reverse=True)[:5]
        for tone, count in sorted_tones:
            percentage = (count / len(rows)) * 100
            print(f"       {tone}: {count} ({percentage:.1f}%)")
    
    # รุ่น/อายุ
    if context_counts["generation"]:
        print(f"     Generational markers:")
        for generation, count in context_counts["generation"].items():
            percentage = (count / len(rows)) * 100
            print(f"       {generation}: {count} ({percentage:.1f}%)")
    
    # วิชาชีพ
    if context_counts["profession"]:
        print(f"     Professional contexts:")
        sorted_professions = sorted(context_counts["profession"].items(), key=lambda x: x[1], reverse=True)[:5]
        for profession, count in sorted_professions:
            percentage = (count / len(rows)) * 100
            print(f"       {profession}: {count} ({percentage:.1f}%)")
    
    # บริบทหลัก (fallback สำหรับแบบเก่า)
    if context_counts["primary_context"]:
        print(f"     Primary contexts:")
        sorted_contexts = sorted(context_counts["primary_context"].items(), key=lambda x: x[1], reverse=True)[:5]
        for context, count in sorted_contexts:
            percentage = (count / len(rows)) * 100
            print(f"       {context}: {count} ({percentage:.1f}%)")
    
    # แสดงข้อมูลเกี่ยวกับ model ที่ใช้
    model_types = {}
    for row in rows:
        model_type = row.get('model_type', 'unknown')
        model_types[model_type] = model_types.get(model_type, 0) + 1
    
    if model_types:
        print(f"   Model types used:")
        for model, count in model_types.items():
            percentage = (count / len(rows)) * 100
            print(f"     {model}: {count} ({percentage:.1f}%)")
    
    print()

def analyze_context_patterns(text):
    """วิเคราะห์รูปแบบการใช้ภาษาเชิงลึก"""
    if not text:
        return {}
    
    clean_text = text.lower()
    patterns = {
        "communication_style": {},
        "relationship_level": {},
        "topic_category": {},
        "cultural_elements": {},
        "generational_markers": {},
        "emotional_indicators": {}
    }
    
    # วิเคราะห์รูปแบบการสื่อสาร
    comm_styles = {
        "formal": CONTEXT_PATTERNS["formal"],
        "informal": CONTEXT_PATTERNS["informal"], 
        "slang": CONTEXT_PATTERNS["slang"]
    }
    
    for style, words in comm_styles.items():
        count = sum(1 for word in words if word in clean_text)
        if count > 0:
            patterns["communication_style"][style] = count
    
    # วิเคราะห์ระดับความสัมพันธ์
    relationship_levels = {
        "intimate": CONTEXT_PATTERNS["intimate"],
        "friendly": CONTEXT_PATTERNS["friendly"],
        "personal": CONTEXT_PATTERNS["personal"]
    }
    
    for level, words in relationship_levels.items():
        count = sum(1 for word in words if word in clean_text)
        if count > 0:
            patterns["relationship_level"][level] = count
    
    # วิเคราะห์หมวดหมู่หัวข้อ
    topic_categories = {
        "technology": CONTEXT_PATTERNS.get("tech", []) + CONTEXT_PATTERNS.get("gaming", []),
        "entertainment": CONTEXT_PATTERNS.get("music", []) + CONTEXT_PATTERNS.get("movie", []),
        "lifestyle": CONTEXT_PATTERNS.get("food", []) + CONTEXT_PATTERNS.get("travel", []),
        "business": CONTEXT_PATTERNS.get("business", []) + CONTEXT_PATTERNS.get("financial", [])
    }
    
    for category, words in topic_categories.items():
        count = sum(1 for word in words if word in clean_text)
        if count > 0:
            patterns["topic_category"][category] = count
    
    # วิเคราะห์องค์ประกอบทางวัฒนธรรม
    cultural_elements = {
        "traditional": CONTEXT_PATTERNS["traditional"],
        "religious": CONTEXT_PATTERNS["religious"],
        "regional": CONTEXT_PATTERNS["northern"] + CONTEXT_PATTERNS["southern"] + CONTEXT_PATTERNS["northeastern"]
    }
    
    for element, words in cultural_elements.items():
        count = sum(1 for word in words if word in clean_text)
        if count > 0:
            patterns["cultural_elements"][element] = count
    
    # วิเคราะห์เครื่องหมายรุ่น
    generational_markers = {
        "gen_z": CONTEXT_PATTERNS["gen_z"],
        "millennial": CONTEXT_PATTERNS["millennial"],
        "gen_x": CONTEXT_PATTERNS["gen_x"]
    }
    
    for generation, words in generational_markers.items():
        count = sum(1 for word in words if word in clean_text)
        if count > 0:
            patterns["generational_markers"][generation] = count
    
    # วิเคราะห์ตัวบ่งชี้อารมณ์
    emotional_indicators = {
        "positive_tone": CONTEXT_PATTERNS["praise"] + CONTEXT_PATTERNS["celebration"],
        "negative_tone": CONTEXT_PATTERNS["complaint"] + CONTEXT_PATTERNS["emergency"],
        "questioning": CONTEXT_PATTERNS["question"]
    }
    
    for indicator, words in emotional_indicators.items():
        count = sum(1 for word in words if word in clean_text)
        if count > 0:
            patterns["emotional_indicators"][indicator] = count
    
    return patterns

def get_context_insights(context_data):
    """สร้าง insights จากข้อมูลบริบท"""
    if not isinstance(context_data, dict):
        return {}
    
    insights = {
        "communication_appropriateness": "",
        "audience_recommendation": "",
        "tone_analysis": "",
        "cultural_sensitivity": "",
        "generational_appeal": ""
    }
    
    formality = context_data.get("formality_level", "neutral")
    social_setting = context_data.get("social_setting", "general")
    emotional_tone = context_data.get("emotional_tone", "neutral")
    generation = context_data.get("generation", "unknown")
    profession = context_data.get("profession", "general")
    
    # วิเคราะห์ความเหมาะสมของการสื่อสาร
    if formality == "slang" and social_setting in ["business", "government", "education"]:
        insights["communication_appropriateness"] = "ไม่เหมาะสม: ใช้ภาษาสแลงในบริบททางการ"
    elif formality == "formal" and social_setting == "social_media":
        insights["communication_appropriateness"] = "อาจเป็นทางการเกินไป: ควรปรับเป็นภาษาที่เป็นกันเองมากขึ้น"
    else:
        insights["communication_appropriateness"] = "เหมาะสม: ระดับความเป็นทางการสอดคล้องกับบริบท"
    
    # คำแนะนำกลุ่มเป้าหมาย
    if generation != "unknown":
        insights["audience_recommendation"] = f"เหมาะสำหรับกลุ่ม {generation}"
    else:
        insights["audience_recommendation"] = "เหมาะสำหรับทุกกลุ่มอายุ"
    
    # วิเคราะห์โทน
    if emotional_tone in ["complaint", "emergency"]:
        insights["tone_analysis"] = "โทนเชิงลบ: ควรระวังการตอบสนองและแก้ไขปัญหา"
    elif emotional_tone in ["praise", "celebration"]:
        insights["tone_analysis"] = "โทนเชิงบวก: โอกาสสร้างความสัมพันธ์ที่ดี"
    else:
        insights["tone_analysis"] = "โทนเป็นกลาง: เหมาะสำหรับการสื่อสารทั่วไป"
    
    # ความไวทางวัฒนธรรม
    if profession in ["government", "education", "healthcare"]:
        insights["cultural_sensitivity"] = "ต้องใช้ภาษาที่เหมาะสมและไม่ล่วงเกิน"
    else:
        insights["cultural_sensitivity"] = "ไม่มีข้อกังวลทางวัฒนธรรมพิเศษ"
    
    # ความดึงดูดตามรุ่น
    if generation == "gen_z":
        insights["generational_appeal"] = "ใช้ภาษาที่ทันสมัยและเข้าถึงคนรุ่นใหม่"
    elif generation == "millennial":
        insights["generational_appeal"] = "ภาษาที่สมดุลระหว่างความเป็นทางการและความเป็นกันเอง"
    elif generation == "gen_x":
        insights["generational_appeal"] = "ภาษาที่มั่นคงและเป็นระบบ"
    else:
        insights["generational_appeal"] = "ภาษาที่เข้าใจได้ทุกกลุ่มอายุ"
    
    return insights
