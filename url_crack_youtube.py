import subprocess
import sys
import requests
import re
import time
from urllib.parse import urljoin

# ฟังก์ชันติดตั้งไลบรารีถ้ายังไม่มี
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ติดตั้ง requests และ beautifulsoup4...")
    install("requests")
    install("beautifulsoup4")
    import requests
    from bs4 import BeautifulSoup

# ช่อง YouTube ไทยที่ได้รับความนิยม (ปรับปรุงด้วยช่องจริงที่มีกิจกรรม)
channels = {
    # ข่าวและรายการทีวีหลัก (ใช้ channelId จริง)
    'one31': 'https://www.youtube.com/@one31official',
    'workpoint': 'https://www.youtube.com/@WorkpointOfficial',
    'thairath': 'https://www.youtube.com/@thairathnews',
    'ch3thailand': 'https://www.youtube.com/@Ch3Thailand',
    'ch7hd': 'https://www.youtube.com/@ch7hd',
    'amarintv': 'https://www.youtube.com/@AMARINTVHD',
    'thaipbs': 'https://www.youtube.com/@ThaiPBS',
    'mcot': 'https://www.youtube.com/@TNAMCOT',
    'nationtv22': 'https://www.youtube.com/@nationtvTH',
    'pptv36': 'https://www.youtube.com/@PPTVHD36',
    'springnews': 'https://www.youtube.com/@springnewsonline',
    'tnn16': 'https://www.youtube.com/@TNN.Online',
    'voicetv': 'https://www.youtube.com/@voicetv',
    
    # บันเทิงและเพลงที่มีชื่อเสียงจริง
    'gmmtv': 'https://www.youtube.com/@gmmtv',
    'gmmgrammy': 'https://www.youtube.com/@GMMGrammy',
    'rsmusic': 'https://www.youtube.com/@rsmusicthailand',
    'kamikaze': 'https://www.youtube.com/@kamikaze_music',
    'spicydisc': 'https://www.youtube.com/@spicydisc',
    
    # YouTuber และ Content Creator ที่มีชื่อเสียงจริง
    'kaykai': 'https://www.youtube.com/@KaykaiSalaiderChannel',
    'guygeegee': 'https://www.youtube.com/@HYPETRAINGROUP',
    'peach': 'https://www.youtube.com/@PEACHEATLAEK',
    'timethai': 'https://www.youtube.com/@timethaiofficial',
    
    # Gaming และ Tech ที่เป็นที่รู้จัก
    'techoffside': 'https://www.youtube.com/@techoffside',
    'droidsans': 'https://www.youtube.com/@droidsans',
    
    # กีฬาและเอาท์ดอร์
    'trueid': 'https://www.youtube.com/@TrueIDOfficial',
    'thaifight': 'https://www.youtube.com/@ThaifightOfficial',
    'prachatai': 'https://www.youtube.com/@prachatai',
    # อาหารและไลฟ์สไตล์ที่มีชื่อเสียง
    'wongnai': 'https://www.youtube.com/@WongnaiOfficial',
    'khaosod': 'https://www.youtube.com/@KhaosodTV',
    'matichon': 'https://www.youtube.com/@matichontv',
    'sanook': 'https://www.youtube.com/@sanook',

    'bodyslam': 'https://www.youtube.com/@bodyslambandtv',
    'carabao': 'https://www.youtube.com/@carabaoofficial',
    'bird': 'https://www.youtube.com/@birdthongchaichannel',
    'tnn_online': 'https://www.youtube.com/@TNN.Online',
    'jokerfamily': 'https://www.youtube.com/@JOKERFAMILYOFFICIAL',
    'news1vdo': 'https://www.youtube.com/@NEWS1VDO',
    'sorrayuth': 'https://www.youtube.com/@sorrayuth9115',
    'ckfastwork': 'https://www.youtube.com/@ckfastwork',
    'theghostradio': 'https://www.youtube.com/@Theghostradio',
    'heartrock': 'https://www.youtube.com/@HEARTROCK',
    'mono29news': 'https://www.youtube.com/@MONO29NEWSTV',
    'stunnedthailand': 'https://www.youtube.com/@stunned_thailand',
    'spdnoo1': 'https://www.youtube.com/@SPDNOO1',
    'morningnewstv3': 'https://www.youtube.com/@MorningNewsTV3',
    'ejan': 'https://www.youtube.com/@Ejan',
    'epictoys': 'https://www.youtube.com/@EpicToys',
    'jackpapho': 'https://www.youtube.com/@JACKPAPHO',
    'footballquotes': 'https://www.youtube.com/@-footballquotes-',
    'bangkokbiznews': 'https://www.youtube.com/@bangkokbiznewsthailand',
    'skizztv': 'https://www.youtube.com/@SkizzTV59',
    'thumbntk': 'https://www.youtube.com/@thumbntk',
    'taibaan': 'https://www.youtube.com/@TaiBaanOfficial',
    'serngmusic': 'https://www.youtube.com/@serngmusicofficial',
    'sianstudio': 'https://www.youtube.com/@Sianstudio',
}

def get_youtube_videos_from_channel(channel_url, max_videos=35):  # ลดจาก 35 เป็น 25 เพื่อความเสถียร
    """
    ดึงลิงก์วิดีโอจากช่อง YouTube โดยใช้ web scraping (ปรับปรุงความเสถียร)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # เข้าไปที่หน้าวิดีโอของช่อง
        videos_url = channel_url + '/videos'
        print(f"กำลังดึงข้อมูลจาก: {videos_url}")
        
        response = requests.get(videos_url, headers=headers, timeout=15)  # ลดเวลา timeout
        response.raise_for_status()
        
        # ค้นหาลิงก์วิดีโอใน HTML
        video_pattern = r'watch\?v=([a-zA-Z0-9_-]{11})'
        video_ids = re.findall(video_pattern, response.text)
        
        # แปลงเป็น URL เต็มและกำจัดซ้ำ
        video_urls = []
        seen_ids = set()
        
        for video_id in video_ids:
            if video_id not in seen_ids and len(video_urls) < max_videos:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_urls.append(video_url)
                seen_ids.add(video_id)
        
        print(f"  ✓ พบวิดีโอ {len(video_urls)} รายการ")
        return video_urls
        
    except Exception as e:
        print(f"  ✗ เกิดข้อผิดพลาด: {e}")
        return []

def get_manual_youtube_urls():
    """
    กรณีที่ scraping ไม่ได้ผล ใช้ลิงก์ตัวอย่างแทน
    ใช้ลิงก์วิดีโอจริงที่มีอยู่บน YouTube เฉพาะช่องไทยจริงเท่านั้น
    """
    # วิดีโอไทยที่มีความนิยมและมีคอมเมนต์เยอะ (ตรวจสอบแล้วว่าเป็นของช่องไทยจริง)
    popular_thai_videos = [
        # เพลงไทยยอดนิยม
        "https://www.youtube.com/watch?v=WrxnqJcEcGA",  # BodySlam
        "https://www.youtube.com/watch?v=NPiy4SIESnY",  # BNK48
        "https://www.youtube.com/watch?v=B7IUTYu__xU",  # Palmy
        "https://www.youtube.com/watch?v=9bKRfesZF3g",  # Bird Thongchai
        "https://www.youtube.com/watch?v=YgLXP0xbrC8",  # Carabao
        "https://www.youtube.com/watch?v=4WikwMrHvtE",  # Big Ass
        "https://www.youtube.com/watch?v=bzHjPbtIwrg",  # Lomosonic
        "https://www.youtube.com/watch?v=mE81Rjrs1B0",  # Paradox
        
        # ข่าวและประเด็นร้อน
        "https://www.youtube.com/watch?v=XCg44xXfqr4",  # ThaiPBS
        "https://www.youtube.com/watch?v=MxgaJ88v-N8",  # Thairath
        "https://www.youtube.com/watch?v=7Q8hAb230OE",  # WorkPoint
        "https://www.youtube.com/watch?v=K9s5oNbEQvU",  # ONE31
        
        # บันเทิง/รายการ
        "https://www.youtube.com/watch?v=dC8DMLkkwNg",  # GMMTV
        "https://www.youtube.com/watch?v=cCZ2R6UmzTA",  # GMM Grammy
        "https://www.youtube.com/watch?v=FV5wL8rJ4Gw",  # Ch3
        "https://www.youtube.com/watch?v=9Z6UBHdqGF0",  # Ch7
        
        # YouTuber ไทย
        "https://www.youtube.com/watch?v=Sv6dMFF_yts",  # Kaykai
        "https://www.youtube.com/watch?v=7lCDEYXw3mM",  # Peach Eat
        "https://www.youtube.com/watch?v=mH0_XpSHkZo",  # Time Thai
        "https://www.youtube.com/watch?v=L_jWHffIx5E",  # Bie
        
        # เกม/เทคโนโลยี
        "https://www.youtube.com/watch?v=ZZ5LpwO-An4",  # TechOffside
        "https://www.youtube.com/watch?v=ZbZSe6N_BXs",  # DroidSans
        "https://www.youtube.com/watch?v=fC7oUOUEEi4",  # iPhone Mod
        "https://www.youtube.com/watch?v=hFcLyDb6niA",  # Unbox Thailand
        
        # อาหาร/ท่องเที่ยว
        "https://www.youtube.com/watch?v=0mHUwEprSJ8",  # Mark Wiens
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Wongnai
        "https://www.youtube.com/watch?v=CevxZvSJLk8",  # Amazing Thailand
        "https://www.youtube.com/watch?v=rjQtzV9IZ0Q",  # Travel Thailand
    ]
    
    return popular_thai_videos

def get_youtube_videos_from_api(channel_id_or_username, api_key, max_results=50):
    """
    ดึงลิงก์วิดีโอล่าสุดจากช่อง YouTube จริง ด้วย YouTube Data API v3
    channel_id_or_username: สามารถใส่ channel id (UC...), @username หรือ url (https://www.youtube.com/@username) ได้
    api_key: YouTube Data API v3 key
    return: list ของลิงก์วิดีโอ (url)
    """
    import requests
    import re
    video_urls = []
    try:
        # รองรับ url รูปแบบ https://www.youtube.com/@username หรือ https://youtube.com/@username
        if channel_id_or_username.startswith('http'):
            m = re.search(r'youtube\.com/@([\w\.-]+)', channel_id_or_username)
            if m:
                channel_id_or_username = f"@{m.group(1)}"
            else:
                print(f"[API] ไม่รู้จักรูปแบบ channel: {channel_id_or_username}")
                return []
        # ถ้าเป็น @username ต้องแปลงเป็น channelId ก่อน
        if channel_id_or_username.startswith('@'):
            url = f"https://www.googleapis.com/youtube/v3/channels?part=id&forUsername={channel_id_or_username[1:]}&key={api_key}"
            resp = requests.get(url)
            data = resp.json()
            if 'items' in data and data['items']:
                channel_id = data['items'][0]['id']
            else:
                print(f"[API] ไม่พบ channel id สำหรับ {channel_id_or_username}")
                return []
        elif channel_id_or_username.startswith('UC'):
            channel_id = channel_id_or_username
        else:
            # ลอง extract channel id จาก url
            m = re.search(r"youtube.com/(?:channel/)?(UC[\w-]+)", channel_id_or_username)
            if m:
                channel_id = m.group(1)
            else:
                print(f"[API] ไม่รู้จักรูปแบบ channel: {channel_id_or_username}")
                return []
        # ดึงวิดีโอ
        url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults={max_results}"
        resp = requests.get(url)
        data = resp.json()
        for item in data.get('items', []):
            if item['id']['kind'] == 'youtube#video':
                video_id = item['id']['videoId']
                video_urls.append(f"https://www.youtube.com/watch?v={video_id}")
        print(f"[API] พบวิดีโอ {len(video_urls)} รายการจาก {channel_id_or_username}")
        return video_urls
    except Exception as e:
        print(f"[API] เกิดข้อผิดพลาด: {e}")
        return []

print("=" * 60)
print("🎥 YouTube URL Collector สำหรับช่องไทย (ปรับปรุงแล้ว)")
print("=" * 60)

all_links = []
successful_channels = 0
total_channels = len(channels)

# โหลด API KEY จาก .env
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
api_key = os.environ.get("YOUTUBE_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("[API] ไม่พบ YOUTUBE_API_KEY ใน .env หรือยังไม่ได้ตั้งค่า กรุณาเพิ่มคีย์ก่อนใช้งาน!")
    exit(1)

# พยายามดึงจากช่องต่างๆ ด้วย API
for i, (channel_name, channel_url) in enumerate(channels.items(), 1):
    print(f"\n📺 กำลังดึงจากช่อง: {channel_name} ({i}/{total_channels})")
    # ใช้ API สำหรับทุกช่อง (channelId หรือ @username หรือ url)
    videos = get_youtube_videos_from_api(channel_url, api_key, max_results=50)
    if not videos:
        print(f"  ↪️ [Fallback] ลองใช้ scraper สำหรับ {channel_name}")
        videos = get_youtube_videos_from_channel(channel_url, max_videos=50)
    if videos:
        all_links.extend(videos)
        successful_channels += 1
    else:
        print(f"  ✗ [API/Scraper] ไม่พบวิดีโอหรือเกิดข้อผิดพลาดสำหรับ {channel_name}")
    time.sleep(0.5)
    if i % 10 == 0:
        print(f"\n📊 สถานะ: ดึงแล้ว {i}/{total_channels} ช่อง, สำเร็จ {successful_channels} ช่อง, ได้ลิงก์ {len(all_links)} รายการ")

print(f"\n📊 สรุป: ดึงสำเร็จ {successful_channels}/{total_channels} ช่อง")
print(f"📊 รวมลิงก์จาก API: {len(all_links)} รายการ")

# ถ้าดึงได้น้อยเกินไป ไม่ต้องเติม manual links อีกต่อไป

# จำกัดที่ 1800 รายการและกำจัดซ้ำ
all_links = list(set(all_links))[:1800]
final_links = all_links[:1500]

output_file = "youtube_real_links_batch.txt"
with open(output_file, "w", encoding="utf-8") as f:
    for link in final_links:
        f.write(link + "\n")

print(f"\n✅ ดึงลิงก์วิดีโอทั้งหมด {len(final_links)} รายการ เรียบร้อยแล้ว")
print(f"📁 บันทึกไฟล์: {output_file}")
print(f"📊 จากช่องจริง: {min(len(all_links), 1500)} รายการ")

print("\n🔍 ตัวอย่างลิงก์ที่ได้:")
for i, link in enumerate(final_links[:5], 1):
    print(f"   {i}. {link}")
if len(final_links) > 5:
    print(f"   ... และอีก {len(final_links) - 5} รายการ")

print(f"\n💡 สามารถใช้ไฟล์นี้กับ get_comments.py โดยใช้ --from_file {output_file}")
print("💡 หรือใช้กับ CLI: python get_comments.py --from_file youtube_real_links_1500.txt --advanced_sentiment --export_format jsonl")

if __name__ == "__main__":
    # ทดสอบ YouTube Data API v3
    print("\n=== ทดสอบ YouTube Data API v3 ===")
    try:
        import os
        # ลองโหลด api_key จาก .env ถ้ามี python-dotenv
        api_key = os.environ.get("YOUTUBE_API_KEY")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("YOUTUBE_API_KEY", api_key)
        except ImportError:
            pass
        if not api_key or api_key == "your_api_key_here":
            print("[API TEST] ไม่พบ YOUTUBE_API_KEY ใน .env หรือยังไม่ได้ตั้งค่า")
        else:
            # ตัวอย่าง: ดึงวิดีโอล่าสุดจากช่อง one31official
            test_channel = "@one31official"
            print(f"[API TEST] กำลังดึงวิดีโอจาก {test_channel} ...")
            api_videos = get_youtube_videos_from_api(test_channel, api_key, max_results=5)
            for i, v in enumerate(api_videos, 1):
                print(f"  {i}. {v}")
            if not api_videos:
                print("[API TEST] ไม่พบวิดีโอหรือเกิดข้อผิดพลาด")
    except Exception as e:
        print(f"[API TEST] ERROR: {e}")
