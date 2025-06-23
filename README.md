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

## 🎥 YouTube Batch Extraction & Podcast Example

รองรับการดึงคอมเมนต์จากวิดีโอ YouTube จำนวนมาก (เช่น podcast, รายการ, ฯลฯ) ด้วยไฟล์ลิงก์อัตโนมัติ เช่น:

```bash
# สร้างไฟล์ลิงก์วิดีโอจากช่องจริง (API+scraper fallback)
python url_crack_youtube.py

# ดึงคอมเมนต์จากวิดีโอ podcast จำนวนมาก
python get_comments.py --from_file youtube_real_links_podcast.txt --advanced_sentiment --export_format jsonl
```

- ✅ รองรับไฟล์ลิงก์ที่สร้างอัตโนมัติ เช่น youtube_real_links_1500.txt, youtube_real_links_podcast.txt
- ✅ ระบบจะใช้ YouTube Data API v3 เป็นหลัก ถ้าไม่ได้จะ fallback เป็น scraper
- ✅ ได้เฉพาะวิดีโอจากช่องจริง (ไม่มี manual links)
- ✅ เหมาะกับ podcast, รายการ, หรือ batch extraction ขนาดใหญ่

**ตัวอย่างไฟล์ลิงก์:**
- `youtube_real_links_podcast.txt` (วิดีโอ podcast/สัมภาษณ์/รายการ)
- `youtube_real_links_1500.txt` (วิดีโอจากหลายหมวดหมู่)