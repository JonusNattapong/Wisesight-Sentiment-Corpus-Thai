# Wisesight-Sentiment-Corpus-Thai

## 🆕 Multiple URLs Support Added!

ระบบตอนนี้รองรับการดึงข้อมูลจากหลาย URLs/queries ในครั้งเดียวแล้ว!

```bash
# Pantip หลายกระทู้
python get_comments.py pantip "43494778" "TOPIC_ID2" "TOPIC_ID3" --include_advanced_sentiment

# YouTube หลายวิดีโอ  
python get_comments.py youtube "VIDEO_ID1" "VIDEO_ID2" --max_results 100

# Multiple files
python get_comments.py file "data1.jsonl" "data2.jsonl" --format csv
```

**Features:**
- ✅ Automatic deduplication (ลบข้อมูลซ้ำ)
- ✅ Source tracking (ติดตามที่มาของข้อมูล)
- ✅ Smart results distribution (แบ่งผลลัพธ์อัตโนมัติ)
- ✅ Advanced Thai sentiment analysis
- ✅ Enhanced statistics display

📖 **รายละเอียด:** [MULTIPLE_URLS_SUCCESS.md](MULTIPLE_URLS_SUCCESS.md)