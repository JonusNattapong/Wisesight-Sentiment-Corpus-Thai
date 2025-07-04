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
    '9MCOT': 'https://www.youtube.com/@9MCOT',
    'nationtv22': 'https://www.youtube.com/@nationtvTH',
    'pptv36': 'https://www.youtube.com/@PPTVHD36',
    'springnews': 'https://www.youtube.com/@springnewsonline',
    'tnn16': 'https://www.youtube.com/@TNN.Online',
    'voicetv': 'https://www.youtube.com/@voicetv',
    'ch7hdnews': 'https://www.youtube.com/@ch7hdnews',
    '3PlusNews': 'https://www.youtube.com/@3PlusNews',
    'onenews31': 'https://www.youtube.com/@onenews31',
    'Luichonkhao': 'https://www.youtube.com/@Luichonkhao',
    'thaich8news': 'https://www.youtube.com/@thaich8news',
    'maleevsking': 'https://www.youtube.com/@maleevsking',
    'GUZAP': 'https://www.youtube.com/@GUZAP',
    'mheeMovie': 'https://www.youtube.com/@mheeMovie',
    'MajorGroup': 'https://www.youtube.com/@MajorGroup',
    'Longtunman': 'https://www.youtube.com/@Longtunman',
    'NetflixThailand': 'https://www.youtube.com/@NetflixThailand',
    'LUPAS_': 'https://www.youtube.com/@LUPAS_',
    'tobenumberonechannel': 'https://www.youtube.com/@tobenumberonechannel',
    'techoffside': 'https://www.youtube.com/@techoffside',
    'TheStandardNews': 'https://www.youtube.com/@TheStandardNews',
    'TheStandardWealth': 'https://www.youtube.com/@TheStandardWealth',
    '1 MILL': 'https://www.youtube.com/channel/UC9XnG68APlP7HaI6y5NU9TQ',
    'SharkTankThailandOfficial': 'https://www.youtube.com/@SharkTankThailandOfficial',
    'WoodyWorldChannel': 'https://www.youtube.com/@WoodyWorldChannel',
    'terodigital': 'https://www.youtube.com/terodigital',  # ช่องเทโรดิจิทัล

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
    'RedremasteRed': 'https://www.youtube.com/@RedremasteRed',
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
    'spin9arm': 'https://www.youtube.com/@spin9arm',
    'FastDrama': 'https://www.youtube.com/@FastDrama',
    'honekrasaeofficial': 'https://www.youtube.com/@honekrasaeofficial',
    'TheVoiceThailand': 'https://www.youtube.com/@TheVoiceThailand',
    'nuenglc': 'https://www.youtube.com/@nuenglc',
    'nickynachat': 'https://www.youtube.com/@nickynachat',
    'ohanaclip': 'https://www.youtube.com/@ohanaclip',
    'theWatcher_Documentary': 'https://www.youtube.com/@theWatcher_Documentary',
    'MissionToTheMoonMedia': 'https://www.youtube.com/@MissionToTheMoon',
    'GMM25Thailand': 'https://www.youtube.com/@GMM25Thailand',
    
}

def get_youtube_videos_from_channel(channel_url, max_videos=120):  # เพิ่มเป็น 120 เพื่อให้เลือกคลิปที่มีคอมเมนต์เยอะ
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


def get_youtube_videos_from_api(channel_id_or_username, api_key=None, max_results=10, channel_key=None):
    """
    ดึงลิงก์วิดีโอล่าสุดจากช่อง YouTube ด้วย web scraping เท่านั้น (ไม่ใช้ API)
    channel_id_or_username: channel id (UC...), @username, หรือ url (https://www.youtube.com/@username)
    return: list ของลิงก์วิดีโอ (url)
    """
    import re
    # แปลง input เป็น channel id หรือ url
    channel_id = None
    channel_url = None
    # ถ้าเป็น url
    if isinstance(channel_id_or_username, str) and channel_id_or_username.startswith('http'):
        m = re.search(r'youtube\.com/(?:channel/)?(UC[\w-]+)', channel_id_or_username)
        if m:
            channel_id = m.group(1)
        else:
            # เป็น @handle หรือ /user/xxx
            m = re.search(r'youtube\.com/@([\w\.-]+)', channel_id_or_username)
            if m:
                handle = m.group(1)
                channel_url = f"https://www.youtube.com/@{handle}"
    elif isinstance(channel_id_or_username, str) and channel_id_or_username.startswith('UC'):
        channel_id = channel_id_or_username
    elif isinstance(channel_id_or_username, str) and channel_id_or_username.startswith('@'):
        handle = channel_id_or_username[1:]
        channel_url = f"https://www.youtube.com/@{handle}"
    else:
        # ไม่รู้จักรูปแบบ
        print(f"[SCRAPER] ไม่รู้จักรูปแบบ channel: {channel_id_or_username}")
        return []
    if channel_id:
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
    if not channel_url:
        print(f"[SCRAPER] ไม่พบ url สำหรับ {channel_id_or_username}")
        return []
    return get_youtube_videos_from_channel(channel_url, max_videos=max_results)

def get_comment_count(video_url):
    """ดึงจำนวนคอมเมนต์จากหน้า YouTube video (scrape)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        resp = requests.get(video_url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
        # หา initialData JSON
        m = re.search(r'var ytInitialData = (\{.*?\});', html, re.DOTALL)
        if not m:
            m = re.search(r'window\["ytInitialData"\] = (\{.*?\});', html, re.DOTALL)
        if m:
            import json
            try:
                data = json.loads(m.group(1))
                # หา commentCount ใน JSON
                # อาจอยู่ใน videoPrimaryInfoRenderer หรือ elsewhere
                count = None
                # วิธี 1: หาใน videoPrimaryInfoRenderer
                try:
                    count = data['contents']['twoColumnWatchNextResults']['results']['results']['contents'][0]['videoPrimaryInfoRenderer']['videoActions']['menuRenderer']['topLevelButtons'][2]['toggleButtonRenderer']['defaultText']['simpleText']
                except Exception:
                    pass
                # วิธี 2: หาใน microformat
                if not count:
                    try:
                        count = data['microformat']['playerMicroformatRenderer']['commentCount']
                    except Exception:
                        pass
                # วิธี 3: หาใน "commentCount" regex
                if not count:
                    m2 = re.search(r'"commentCount":\s*"?(\d+)"?', html)
                    if m2:
                        count = m2.group(1)
                if count:
                    # แปลงเป็น int
                    count = int(count.replace(',', '').replace('ความคิดเห็น', '').strip())
                    return count
            except Exception:
                pass
        # fallback: หา "ความคิดเห็น" ใน HTML
        m = re.search(r'(\d+[\,\d]*)\s*ความคิดเห็น', html)
        if m:
            count = int(m.group(1).replace(',', ''))
            return count
    except Exception as e:
        print(f"[SCRAPER] Error fetching comment count for {video_url}: {e}")
    return 0

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

# Update the main video-fetching loop to use scraping only, no channelId resolving
num_per_channel = 10  # จำนวนลิงก์ล่าสุดต่อช่อง (ปรับได้)
per_channel_links = {}
all_links = []
successful_channels = 0
total_channels = len(channels)
for i, (channel_name, channel_url) in enumerate(channels.items(), 1):
    print(f"\n📺 Fetching videos for: {channel_name} ({i}/{total_channels})")
    import random
    videos = get_youtube_videos_from_api(channel_url, max_results=120, channel_key=channel_name)
    if len(videos) > num_per_channel:
        top_videos = random.sample(videos, num_per_channel)
    else:
        top_videos = videos
    if top_videos:
        per_channel_links[channel_name] = top_videos
        all_links.extend(top_videos)
        successful_channels += 1
    else:
        print(f"  ✗ [SCRAPER] No videos found or error for {channel_name}")
    if i % 5 == 0:
        print(f"\n📊 Status: Processed {i}/{total_channels} channels, successful {successful_channels}, links {len(all_links)}")

# รวมลิงก์ล่าสุดจากแต่ละช่อง
latest_links = []
for channel_name in per_channel_links:
    latest_links.extend(per_channel_links[channel_name])

output_file = f"youtube_latest_links_{num_per_channel}per_channel.txt"
with open(output_file, "w", encoding="utf-8") as f:
    for link in latest_links:
        f.write(link + "\n")

print(f"\n✅ ดึงลิงก์ล่าสุด {num_per_channel} ลิงก์ต่อช่อง รวม {len(latest_links)} รายการ เรียบร้อยแล้ว")
print(f"📁 บันทึกไฟล์: {output_file}")
print("\n🔍 ตัวอย่างลิงก์ที่ได้:")
for i, link in enumerate(latest_links[:5], 1):
    print(f"   {i}. {link}")
if len(latest_links) > 5:
    print(f"   ... และอีก {len(latest_links) - 5} รายการ")

print(f"\n💡 สามารถใช้ไฟล์นี้กับ get_comments.py โดยใช้ --from_file {output_file}")

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
