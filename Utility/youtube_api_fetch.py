import os
import requests
from dotenv import load_dotenv

def fetch_youtube_videos(channel_id, api_key, max_results=20):
    """
    ดึงลิงก์วิดีโอล่าสุดจากช่อง YouTube ด้วย YouTube Data API v3 (channelId เท่านั้น)
    """
    video_urls = []
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults={max_results}"
    resp = requests.get(url, timeout=10)
    data = resp.json()
    if 'error' in data:
        print(f"[API ERROR] {data['error'].get('message', data['error'])}")
        return []
    for item in data.get('items', []):
        if item['id']['kind'] == 'youtube#video':
            video_id = item['id']['videoId']
            video_urls.append(f"https://www.youtube.com/watch?v={video_id}")
    if not video_urls:
        print("[API] ไม่พบวิดีโอใน response หรือช่องนี้ไม่มีวิดีโอ")
    return video_urls

if __name__ == "__main__":
    load_dotenv()
    api_key = os.environ.get("YOUTUBE_API_KEY")
    # ตัวอย่าง: ช่อง TNN Online (channelId จริง)
    channel_id = "UCpHTAE2EOwWkWGnW2HY8gRw"
    print(f"ดึงวิดีโอล่าสุดจากช่อง {channel_id} ...")
    videos = fetch_youtube_videos(channel_id, api_key, max_results=10)
    for i, v in enumerate(videos, 1):
        print(f"{i}. {v}")
    if not videos:
        print("ไม่พบวิดีโอหรือเกิดข้อผิดพลาด")
