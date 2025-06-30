# Wisesight-Sentiment-Corpus-Thai

## 🚀 Quick Start

1. **ติดตั้ง dependencies** (Python 3.8+):
   ```bash
   pip install -r requirements.txt
   ```
2. **(แนะนำ) ตั้งค่า Google API Key** สำหรับ YouTube Data API v3 ใน `.env` หรือผ่าน environment variable

---

## 🛠️ Main Features
- ดึงคอมเมนต์จาก YouTube, Pantip, ฯลฯ แบบ batch
- วิเคราะห์ sentiment ภาษาไทย (ML/ensemble, auto review)
- รองรับ batch จากไฟล์ลิงก์ (txt)
- Export: JSONL, CSV, TXT (เลือกได้)
- Privacy: mask/remove PII, author anonymization, privacy_notice
- Robust error handling, deduplication, source tracking

---

## 📝 Example Workflow: YouTube Batch Extraction + Sentiment + Privacy

### 1. สร้างไฟล์ลิงก์วิดีโอ (YouTube)
```bash
python url_crack_youtube.py
# จะได้ไฟล์ youtube_real_links_1500.txt หรือ youtube_real_links_podcast.txt
```

### 2. ดึงคอมเมนต์ + วิเคราะห์ sentiment + export (JSONL)
```bash
python app.py --from_file youtube_real_links_1500.txt --sentiment ml --export_format jsonl
```

### 3. เปิดใช้งาน privacy (mask/remove PII, anonymize author)
```bash
# Mask PII + hash author
python app.py --from_file youtube_real_links_1500.txt --sentiment ml --privacy mask --export_format jsonl

# Remove author + mask PII
python app.py --from_file youtube_real_links_1500.txt --sentiment ml --privacy remove --export_format csv
```

### 4. ตัวอย่าง export (เลือกได้)
- `--export_format jsonl` (default)
- `--export_format csv`
- `--export_format txt`

### 5. ตัวอย่าง post-processing (เช่น รวมไฟล์, แปลง format)
```bash
# รวมหลายไฟล์ JSONL
cat youtube_comments_batch_*.jsonl > all_comments.jsonl

# แปลง JSONL เป็น CSV
python data_utils.py --input all_comments.jsonl --output all_comments.csv --format csv
```

---

## 🔒 Privacy Management
- `--privacy mask` : hash author, mask PII (ชื่อ, เบอร์, อีเมล, ฯลฯ)
- `--privacy remove` : remove author, mask PII
- ทุก record จะมี `privacy_notice` อธิบายมาตรการ privacy
- (แนะนำ) ใช้ privacy mode ทุกครั้งที่ export ข้อมูลจริง

---

## 🎯 Advanced Sentiment Analysis
- `--sentiment ml` : ใช้ ML/ensemble model (แนะนำ)
- `--sentiment auto` : auto review (default)
- รองรับ tokenizer-level truncation (max_length=512)

---

## 🧑‍💻 Batch Extraction: Pantip, YouTube, Files

### Pantip หลายกระทู้
```bash
python get_comments.py pantip "43494778" "TOPIC_ID2" "TOPIC_ID3" --include_advanced_sentiment
```

### YouTube หลายวิดีโอ
```bash
python get_comments.py youtube "VIDEO_ID1" "VIDEO_ID2" --max_results 100
```

### Batch จากไฟล์ลิงก์
```bash
python get_comments.py --from_file youtube_real_links_podcast.txt --advanced_sentiment --export_format jsonl
```

### Multiple files
```bash
python get_comments.py file "data1.jsonl" "data2.jsonl" --format csv
```

---

## 📦 Export Formats
- JSONL: เหมาะกับงาน ML, ข้อมูลขนาดใหญ่
- CSV: ใช้งานทั่วไป, เปิดใน Excel ได้
- TXT: ข้อความล้วน

---

## 🛡️ Troubleshooting & Tips
- หากเจอ error จาก transformer model ให้ตรวจสอบว่าใช้ `max_length=512, truncation=True` (ระบบตั้งไว้แล้ว)
- หาก YouTube API quota หมด ระบบจะ fallback เป็น scraper อัตโนมัติ
- ใช้ privacy mode ทุกครั้งที่ export ข้อมูลจริง
- ดูตัวอย่าง workflow และคำสั่งใน README นี้

---

## 📚 รายละเอียดเพิ่มเติม
- [MULTIPLE_URLS_SUCCESS.md](MULTIPLE_URLS_SUCCESS.md)
- ตัวอย่างไฟล์ลิงก์: `youtube_real_links_podcast.txt`, `youtube_real_links_1500.txt`
- Output ตัวอย่าง: `youtube_comments_batch_1.jsonl`

---

**สอบถาม/ปรับแต่ง workflow เพิ่มเติม แจ้งได้เลย!**