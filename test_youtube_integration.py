#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for YouTube comment integration and sentiment analysis
"""
import json
import os
from app import fetch_youtube_comments, flatten_comments, enhanced_analyze_sentiment

def test_youtube_scraping():
    """Test YouTube comment scraping functionality"""
    print("🚀 Testing YouTube Comment Scraping & Sentiment Analysis")
    print("=" * 60)
    
    # Test URL - use a popular Thai YouTube video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll as safe test
    
    print(f"📺 Testing URL: {test_url}")
    
    try:
        # Test comment fetching
        print("🔍 Fetching comments...")
        comments = fetch_youtube_comments(test_url)
        
        if comments:
            print(f"✅ Successfully fetched {len(comments)} comments")
            
            # Test flattening
            print("📝 Flattening comments...")
            flattened = flatten_comments(comments)
            print(f"✅ Flattened to {len(flattened)} entries")
            
            # Test sentiment analysis on a few comments
            print("💭 Testing sentiment analysis...")
            for i, comment in enumerate(flattened[:3]):  # Test first 3
                text = comment.get('text', '')
                if text.strip():
                    result = enhanced_analyze_sentiment(text)
                    print(f"  {i+1}. Text: {text[:50]}...")
                    print(f"     Sentiment: {result['sentiment']} (confidence: {result['confidence']:.2f})")
                    print(f"     Details: {result.get('detailed_sentiment', 'N/A')}")
                    
        else:
            print("⚠️ No comments fetched - this might be expected for some videos")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print("This might be due to network issues or YouTube restrictions")

def test_local_sentiment():
    """Test sentiment analysis with predefined Thai texts"""
    print("\n🧠 Testing Local Sentiment Analysis")
    print("=" * 40)
    
    test_cases = [
        "ขอบคุณนะคะที่ทำให้วันนี้เป็นวันที่แย่ที่สุดในชีวิต 😊",  # Sarcastic
        "วิดีโอนี้ดีมากเลย รักเลย ❤️",  # Positive
        "ห่วยแตกมาก ไม่ชอบเลย 😡",  # Negative  
        "ข้อมูลข่าวสารประจำวัน",  # Neutral
        "งานนี้สุดยอดครับ... ถ้าชอบความล้มเหลว",  # Sarcastic
    ]
    
    for i, text in enumerate(test_cases, 1):
        try:
            result = enhanced_analyze_sentiment(text)
            print(f"{i}. Text: {text}")
            print(f"   Sentiment: {result['sentiment']} | Confidence: {result['confidence']:.2f}")
            print(f"   Details: {result.get('detailed_sentiment', 'N/A')}")
            print()
        except Exception as e:
            print(f"❌ Error analyzing '{text}': {e}")

if __name__ == "__main__":
    test_local_sentiment()
    test_youtube_scraping()
    print("\n✅ Testing completed!")
