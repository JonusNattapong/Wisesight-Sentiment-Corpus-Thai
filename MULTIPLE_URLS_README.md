# 🔥 Multiple URLs/Queries Support - อัพเดตใหม่!

ตอนนี้ระบบรองรับการดึงข้อมูลจากหลาย URLs/queries ในครั้งเดียวแล้ว! 🎉

## 🆕 ฟีเจอร์ใหม่

### 1. Multiple URLs ใน CLI
```bash
# YouTube หลายวิดีโอ
python get_comments.py youtube "K150FJzooLM" "dQw4w9WgXcQ" "VIDEO_ID3" --include_advanced_sentiment

# Pantip หลายกระทู้
python get_comments.py pantip "43494778" "https://pantip.com/topic/43494778" "TOPIC_ID3" --max_results 100

# Twitter/X หลายคีย์เวิร์ด
python get_comments.py twitter "พายุ" "น้ำท่วม" "ภัยธรรมชาติ" --include_sentiment

# โหลดจากหลายไฟล์
python get_comments.py file "data1.jsonl" "data2.jsonl" "data3.jsonl" --format csv
```

### 2. Multiple URLs ใน Python Code
```python
from social_media_utils import extract_social_media_comments

# YouTube หลายวิดีโอ
youtube_urls = [
    "K150FJzooLM",  # หลวงพ่อแย้ม
    "dQw4w9WgXcQ",  # Rick Roll
    "https://www.youtube.com/watch?v=VIDEO_ID3"
]

comments = extract_social_media_comments(
    platform="youtube",
    query=youtube_urls,  # ส่ง list ของ URLs
    max_results=100,
    include_advanced_sentiment=True
)

print(f"ได้รับ {len(comments)} comments จาก {len(youtube_urls)} วิดีโอ")
```

### 3. Automatic Deduplication
- ระบบจะตรวจสอบและลบข้อมูลซ้ำซ้อนอัตโนมัติ
- ใช้ similarity threshold ในการตรวจสอบ
- แสดงจำนวนข้อมูลที่ถูกลบออก

### 4. Source Tracking
- แต่ละ comment จะมี `source_query` และ `query_index` 
- ช่วยให้ทราบว่าข้อมูลมาจาก URL/query ไหน
- แสดงสถิติแยกตาม source

### 5. Intelligent Results Distribution
- ระบบจะแบ่งจำนวน `max_results` ให้กับแต่ละ query อัตโนมัติ
- ถ้ามี 3 URLs และ max_results=150 จะดึง ~50 จากแต่ละ URL
- ลบข้อมูลซ้ำแล้วจึงตัดให้เหลือ max_results

## 📊 Output Features

### Enhanced Filename
- Single source: `youtube_comments_20241227_143022.jsonl`
- Multiple sources: `youtube_comments_3sources_20241227_143022.jsonl`

### Statistics Display
```
[INFO] Processing 3 youtube URLs/queries...
[INFO] Processing 1/3: K150FJzooLM...
[INFO] Processing 2/3: dQw4w9WgXcQ...
[INFO] Processing 3/3: https://www.youtube.com/watch?v=VIDEO_ID3...
[INFO] Removed 5 duplicate comments
[INFO] Extracted 87 total comments from Youtube from 3 sources with Advanced Thai Sentiment

สถิติแยกตาม source:
  K150FJzooLM: 32 comments
  dQw4w9WgXcQ: 28 comments  
  https://www.youtube.com/watch?v=VIDEO_ID3: 27 comments
  รวม 3 sources
```

## 🛠️ Technical Implementation

### 1. Updated Function Signature
```python
def extract_social_media_comments(
    platform: str,
    query: Union[str, List[str]],  # 🆕 รองรับ string หรือ list
    max_results: int = 100,
    include_sentiment: bool = False,
    filter_spam: bool = True,
    silent: bool = True,
    include_advanced_sentiment: bool = False,
    **kwargs
) -> List[Dict[str, Any]]:
```

### 2. Comment Structure Enhancement
```python
{
    "text": "ความคิดเห็น...",
    "platform": "youtube",
    "source_query": "K150FJzooLM",      # 🆕 URL/query ที่เป็นที่มา
    "query_index": 0,                   # 🆕 ลำดับที่ของ query
    "emotion": "positive",              # Advanced sentiment
    "intensity": "medium",
    # ... other fields
}
```

### 3. Deduplication Algorithm
```python
def deduplicate_comments(
    comments: List[Dict[str, Any]], 
    similarity_threshold: float = 0.85
) -> List[Dict[str, Any]]:
    # ตรวจสอบความคล้ายกันของข้อความ
    # ลบข้อมูลซ้ำที่มีความคล้ายกัน > 85%
```

## 🎯 Use Cases

### 1. Content Analysis Across Multiple Videos
```bash
# วิเคราะห์ความคิดเห็นเกี่ยวกับหัวข้อเดียวกันจากหลายวิดีโอ
python get_comments.py youtube "VIDEO1" "VIDEO2" "VIDEO3" --include_advanced_sentiment --max_results 300
```

### 2. Topic Monitoring
```bash
# ติดตามความคิดเห็นในหลายกระทู้ Pantip เกี่ยวกับหัวข้อเดียวกัน
python get_comments.py pantip "TOPIC1" "TOPIC2" "TOPIC3" --include_sentiment
```

### 3. Dataset Aggregation
```bash
# รวมไฟล์ข้อมูลหลายไฟล์เป็นชุดเดียว
python get_comments.py file "data1.jsonl" "data2.jsonl" "data3.jsonl" --format csv
```

### 4. Comparative Analysis
```python
# เปรียบเทียบความคิดเห็นจากหลาย sources
results = extract_social_media_comments(
    platform="youtube",
    query=["VIDEO_A", "VIDEO_B", "VIDEO_C"],
    include_advanced_sentiment=True
)

# วิเคราะห์ความแตกต่างระหว่าง sources
for source in set(c.get('source_query') for c in results):
    source_comments = [c for c in results if c.get('source_query') == source]
    emotions = [c.get('emotion') for c in source_comments if c.get('emotion')]
    print(f"{source}: {Counter(emotions)}")
```

## 🧪 Testing

รัน script ทดสอบ:
```bash
python example_multiple_urls.py
```

จะทดสอบ:
- ✅ YouTube หลายวิดีโอ
- ✅ Pantip หลายกระทู้  
- ✅ Multiple files loading
- ✅ Deduplication
- ✅ Source tracking
- ✅ Advanced sentiment analysis
- ✅ File saving

## 🔧 Backward Compatibility

ระบบยังคงรองรับการใช้งานแบบเดิม (single URL) ได้ปกติ:

```bash
# แบบเดิม - ยังใช้ได้
python get_comments.py youtube "K150FJzooLM" --include_advanced_sentiment

# แบบใหม่ - รองรับหลาย URLs
python get_comments.py youtube "K150FJzooLM" "dQw4w9WgXcQ" --include_advanced_sentiment
```

## 📝 Notes

1. **Performance**: การดึงจากหลาย sources อาจใช้เวลานานกว่า
2. **Rate Limiting**: บางแพลตฟอร์มอาจมีข้อจำกัดการเข้าถึง
3. **Memory Usage**: หลาย URLs อาจใช้ memory มากกว่า
4. **Deduplication**: ใช้เวลาเพิ่มเติมสำหรับการตรวจสอบความซ้ำซ้อน

## 🚀 Future Enhancements

- [ ] Parallel processing สำหรับหลาย URLs
- [ ] Custom similarity threshold
- [ ] Advanced source analytics
- [ ] URL validation และ normalization
- [ ] Resume capability สำหรับ batch processing ที่ถูกขัดจังหวะ

---

**Happy Multiple URLs Extraction! 🎉**
