# 🎯 Advanced Thai Sentiment Analysis Schema

Schema Sentiment ภาษาไทยที่ครอบคลุม **อารมณ์**, **เจตนา**, และ **บริบท** สำหรับงาน **Sentiment Analysis** ขั้นสูง

## 📋 Schema Overview

| Field Name        | Type          | Description                                                                             |
| ----------------- | ------------- | --------------------------------------------------------------------------------------- |
| `text`            | String        | ข้อความต้นฉบับ                                                                          |
| `emotion`         | String        | ประเภทอารมณ์: `joy`, `sadness`, `anger`, `fear`, `excited`, `neutral`, `complex`        |
| `intent`          | String        | เจตนาของผู้พูด: `inform`, `question`, `request`, `praise`, `complain`, `sarcasm`        |
| `intensity`       | String        | ระดับอารมณ์: `low`, `medium`, `high`                                                    |
| `context`         | String        | บริบทการใช้ภาษา: `formal`, `informal`, `slang`, `personal`                              |
| `target`          | String (opt.) | สิ่ง/บุคคล/กลุ่มที่ผู้พูดกล่าวถึง (ถ้ามี)                                               |
| `sentiment_score` | Float         | ค่าการให้คะแนนโดยโมเดล (-1.0 ถึง 1.0)                                                   |
| `analysis_notes`  | String (opt.) | หมายเหตุ/คำอธิบายผลการวิเคราะห์                                                         |

## 🚀 Quick Start

### การติดตั้ง Dependencies

```bash
# Optional dependencies for enhanced features
pip install pandas beautifulsoup4 playwright python-dotenv

# For Playwright browser automation
playwright install chromium
```

### การใช้งานเบื้องต้น

```python
from social_media_utils import advanced_thai_sentiment_analysis

# วิเคราะห์ข้อความเดี่ยว
text = "อ่อ... ดีจริง ๆ เนอะ"
result = advanced_thai_sentiment_analysis(text)

print(result)
# Output:
# {
#   "text": "อ่อ... ดีจริง ๆ เนอะ",
#   "emotion": "complex",
#   "intent": "sarcasm", 
#   "intensity": "medium",
#   "context": "informal",
#   "target": null,
#   "sentiment_score": -0.2,
#   "notes": "อารมณ์ซับซ้อน, มีความเหน็บแนม"
# }
```

### การวิเคราะห์แบบ Batch

```python
from social_media_utils import batch_advanced_sentiment_analysis

comments = [
    {"text": "ห่วยแตก! ร้านนี้ไม่ควรเปิดเลย", "author": "User1"},
    {"text": "อ่อ... ดีจริง ๆ เนอะ", "author": "User2"},
    {"text": "โคตรดีเลย! สุดยอดมาก", "author": "User3"}
]

analyzed = batch_advanced_sentiment_analysis(comments)
```

### การบันทึกผลลัพธ์

```python
from social_media_utils import save_advanced_sentiment_data

# บันทึกเป็น JSONL
save_advanced_sentiment_data(analyzed, "results.jsonl", "jsonl")

# บันทึกเป็น CSV (ต้องติดตั้ง pandas)
save_advanced_sentiment_data(analyzed, "results.csv", "csv")
```

## 📊 ตัวอย่างผลการวิเคราะห์

| Text                                             | Emotion | Intent   | Intensity | Context  | Score | Notes                         |
| ------------------------------------------------ | ------- | -------- | --------- | -------- | ----- | ----------------------------- |
| "ห่วยแตก! ร้านนี้ไม่ควรเปิดเลย"                  | anger   | complain | high      | informal | -1.0  | อารมณ์รุนแรง                  |
| "อ่อ... ดีจริง ๆ เนอะ"                           | complex | sarcasm  | medium    | informal | -0.2  | อารมณ์ซับซ้อน, มีความเหน็บแนม |
| "ช่วยหน่อยนะคะ งานต้องส่งพรุ่งนี้"               | neutral | request  | low       | formal   | 0.0   |                               |
| "โคตรดีเลย! สุดยอดมาก ชอบมาก 555"               | joy     | praise   | high      | slang    | 1.0   | อารมณ์รุนแรง                  |

## 🎯 ประเภทอารมณ์ (Emotions)

- **`joy`**: ความดีใจ, ความสุข, ความชื่นชอบ
- **`sadness`**: ความเศร้า, ความผิดหวัง
- **`anger`**: ความโกรธ, ความไม่พอใจ  
- **`fear`**: ความกลัว, ความกังวล, ความเครียด
- **`excited`**: ความตื่นเต้น, ความ energetic
- **`neutral`**: อารมณ์เป็นกลาง
- **`complex`**: อารมณ์ซับซ้อน, ผสมผสาน

## 💬 ประเภทเจตนา (Intents)

- **`inform`**: แจ้งข้อมูล, บอกเล่า
- **`question`**: ตั้งคำถาม, สอบถาม
- **`request`**: ขอร้อง, ขอความช่วยเหลือ
- **`praise`**: ชม, ยกย่อง, ให้กำลังใจ
- **`complain`**: บ่น, ร้องเรียน, วิจารณ์
- **`sarcasm`**: เหน็บแนม, ประชด, พูดตรงข้าม

## 🎚️ ระดับความเข้ม (Intensity)

- **`low`**: อารมณ์เบา ๆ, ไม่รุนแรง
- **`medium`**: อารมณ์ปานกลาง
- **`high`**: อารมณ์รุนแรง, เข้มข้น

## 🗣️ บริบทการใช้ภาษา (Context)

- **`formal`**: ภาษาทางการ, สุภาพ
- **`informal`**: ภาษาไม่เป็นทางการ, ธรรมดา
- **`slang`**: ภาษาแสลง, คำเล่น
- **`personal`**: ภาษาส่วนตัว, ใกล้ชิด

## 📈 Sentiment Score Scale

```
-1.0  ←→  -0.5  ←→   0.0   ←→  +0.5  ←→  +1.0
ลบมาก    ลบปาน    เป็นกลาง    บวกปาน   บวกมาก
```

## 🔧 การปรับแต่ง

### เพิ่มคำศัพท์ใหม่

```python
# แก้ไขใน emotion_patterns, intent_patterns
emotion_patterns["joy"]["keywords"].extend(["ปลื้ม", "เฮง", "เจ๋ง"])
```

### ปรับ Sentiment Score

```python
# แก้ไขใน sentiment_mapping
sentiment_mapping = {
    "joy": 0.9,      # เพิ่มจาก 0.8 เป็น 0.9
    "anger": -0.9,   # เพิ่มจาก -0.8 เป็น -0.9
    # ...
}
```

## 🎬 Demo และตัวอย่าง

```python
# รัน demo
from social_media_utils import demo_advanced_sentiment
demo_advanced_sentiment()

# หรือรันไฟล์ตัวอย่าง
python example_advanced_sentiment.py
```

## 📁 ไฟล์ Output

### JSONL Format
```json
{"text": "ห่วยแตก! ร้านนี้ไม่ควรเปิดเลย", "emotion": "anger", "intent": "complain", "intensity": "high", "context": "informal", "target": "ร้านน", "sentiment_score": -1.0, "analysis_notes": "อารมณ์รุนแรง"}
```

### CSV Format
```csv
text,emotion,intent,intensity,context,target,sentiment_score,analysis_notes
"ห่วยแตก! ร้านนี้ไม่ควรเปิดเลย",anger,complain,high,informal,"ร้านน",-1.0,อารมณ์รุนแรง
```

## 🚧 Limitations & Future Work

### ปัจจุบัน
- การตรวจจับ `target` ยังเป็นแบบ basic pattern matching
- รองรับเฉพาะภาษาไทยและอังกฤษ
- ยังไม่รองรับ emoji ทั้งหมด

### แผนอนาคต
- เพิ่ม NLP models สำหรับ Named Entity Recognition
- รองรับภาษาอื่น ๆ
- เพิ่ม deep learning models
- รองรับ multimodal analysis (text + image)

## 🤝 Contributing

1. Fork repository
2. สร้าง feature branch
3. เพิ่มคำศัพท์หรือปรับปรุง patterns
4. ทดสอบกับข้อมูลจริง
5. Submit Pull Request

## 📜 License

MIT License - ใช้งานได้อย่างอิสระ

## 📞 Support

- GitHub Issues: สำหรับ bug reports และ feature requests
- Email: สำหรับคำถามเฉพาะ

---
**สร้างโดย**: Advanced Thai NLP Team  
**อัปเดตล่าสุด**: June 2025
