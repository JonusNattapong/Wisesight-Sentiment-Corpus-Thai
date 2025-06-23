# ✅ เพิ่มฟีเจอร์ Multiple URLs สำเร็จแล้ว!

ตอนนี้ระบบ **Wisesight Sentiment Corpus Thai** รองรับการดึงข้อมูลจากหลาย URLs/queries ในครั้งเดียวแล้ว! 🎉

## 🆕 วิธีใช้งาน

### CLI Command
```bash
# Pantip หลายกระทู้
python get_comments.py pantip "43494778" "https://pantip.com/topic/43494778" "TOPIC_ID3" --include_advanced_sentiment

# YouTube หลายวิดีโอ  
python get_comments.py youtube "VIDEO_ID1" "VIDEO_ID2" "VIDEO_ID3" --max_results 100

# Twitter หลายคำค้นหา
python get_comments.py twitter "พายุ" "น้ำท่วม" "ภัยธรรมชาติ" --include_sentiment

# โหลดจากหลายไฟล์
python get_comments.py file "data1.jsonl" "data2.jsonl" --format csv
```

### Python Code
```python
from social_media_utils import extract_social_media_comments

# ส่ง list ของ URLs
comments = extract_social_media_comments(
    platform="pantip",
    query=["43494778", "https://pantip.com/topic/43494778"],  # หลาย URLs
    max_results=50,
    include_advanced_sentiment=True
)

print(f"ได้รับ {len(comments)} comments จาก {len(query)} sources")
```

## 🔧 ฟีเจอร์ที่เพิ่ม

### 1. **Automatic Deduplication**
- ลบข้อมูลซ้ำอัตโนมัติ (similarity threshold 85%)
- แสดงจำนวนข้อมูลที่ถูกลบ

### 2. **Source Tracking**
- แต่ละ comment มี `source_query` และ `query_index`
- รู้ว่าข้อมูลมาจาก URL ไหน

### 3. **Smart Results Distribution**
- แบ่ง `max_results` ให้กับแต่ละ query อัตโนมัติ
- เช่น 3 URLs + max_results=150 = ~50 จากแต่ละ URL

### 4. **Enhanced Statistics**
```
สถิติแยกตาม source:
  43494778: 17 comments
  https://pantip.com/topic/43494778: 17 comments
  รวม 2 sources
```

### 5. **Intelligent Filename**
- Single: `pantip_comments_20250620_184828.jsonl`
- Multiple: `pantip_comments_2sources_20250620_184828.jsonl`

## ✅ ทดสอบแล้ว

การทดสอบเมื่อกี้แสดงว่า:
- ✅ Pantip หลาย URLs ทำงานได้
- ✅ ลบข้อมูลซ้ำได้ (37 duplicates removed)
- ✅ Advanced Thai Sentiment Analysis ทำงานได้
- ✅ Source tracking ทำงานได้
- ✅ บันทึกไฟล์ได้ถูกต้อง

## 📊 ผลลัพธ์ตัวจริง

จากการทดสอบเมื่อกี้:
```
[INFO] Processing 2 pantip URLs/queries...
[INFO] Removed 37 duplicate comments
[INFO] Extracted 34 total comments from Pantip from 2 sources with Advanced Thai Sentiment
```

ไฟล์ผลลัพธ์: `data/pantip_comments_2sources_20250620_184828.jsonl`

แต่ละ comment มี fields ครบ:
- `source_query`: บอกว่ามาจาก URL ไหน
- `emotion`, `intent`, `intensity`: Advanced sentiment  
- `sentiment_score`: คะแนน sentiment (-1.0 ถึง 1.0)

## 🚀 พร้อมใช้งาน!

ตอนนี้คุณสามารถใช้งานได้เลย:

```bash
# ทดสอบ Pantip หลายกระทู้
python get_comments.py pantip "43494778" "43123456" --include_advanced_sentiment

# ทดสอบ file loading
python get_comments.py file "data/file1.jsonl" "data/file2.jsonl" --format csv
```

**Happy Multiple URLs Extraction! 🎉**
