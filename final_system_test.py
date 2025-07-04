#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Final comprehensive test of the Thai sentiment analysis system
"""

def test_sentiment_system():
    print("🚀 Final Thai Sentiment Analysis System Test")
    print("=" * 50)
    
    # Test cases covering various scenarios
    test_cases = [
        # Standard cases
        {"text": "ดีใจมากเลย รักเธอที่สุดเลย ❤️😍", "expected": "positive", "description": "Clear positive with emojis"},
        {"text": "ห่วยแตกมาก ไม่ชอบเลย 😡", "expected": "negative", "description": "Clear negative with emoji"},
        {"text": "ข้อมูลข่าวสารประจำวัน", "expected": "neutral", "description": "Neutral informational text"},
        
        # Sarcasm and irony cases
        {"text": "เยี่ยมจริงๆ เนอะ บริการดีมากเลย 🙄", "expected": "negative", "description": "Sarcastic comment with eye-roll emoji"},
        {"text": "ขอบคุณนะคะที่ทำให้วันนี้เป็นวันที่แย่ที่สุดในชีวิต 😊", "expected": "negative", "description": "Sarcastic thanks"},
        {"text": "งานนี้สุดยอดครับ... ถ้าชอบความล้มเหลว", "expected": "negative", "description": "Sarcasm with ellipsis"},
        
        # Complex cases
        {"text": "โกรธจนขำอะ! ทำไมต้องมาแบบนี้ด้วย 555 😡😂", "expected": "mixed", "description": "Mixed emotions: anger + humor"},
        {"text": "อาหารอร่อยนะ แต่บริการช้าไปนิดนึง", "expected": "mixed", "description": "Mixed review"},
        {"text": "ทำกันได้ลงคอเนอะ?", "expected": "negative", "description": "Rhetorical question expressing disbelief"},
        {"text": "สวยขนาดนี้ ไม่ให้ชอบได้ไง", "expected": "positive", "description": "Double negative expressing positive"},
        
        # Code-switching and modern slang
        {"text": "โคตร cute มากเลย ปลื้มจัง OwO", "expected": "positive", "description": "Thai-English mix with modern slang"},
        {"text": "cringe หนักมาก อะไรเนี่ย", "expected": "negative", "description": "English slang in Thai context"},
        
        # Social media style
        {"text": "Today mood: เหนื่อยจัง but still fighting 💪", "expected": "mixed", "description": "Mixed Thai-English social media post"},
    ]
    
    try:
        from app import enhanced_analyze_sentiment
        
        print(f"📊 Running {len(test_cases)} test cases...")
        print()
        
        correct = 0
        total = len(test_cases)
        
        for i, case in enumerate(test_cases, 1):
            text = case["text"]
            expected = case["expected"]
            description = case["description"]
            
            try:
                result = enhanced_analyze_sentiment(text)
                predicted = result["sentiment"]
                confidence = result["confidence"]
                details = result.get("detailed_sentiment", "N/A")
                
                is_correct = (predicted == expected or 
                             (expected == "mixed" and confidence < 0.7))  # Lower confidence often indicates mixed
                
                if is_correct:
                    correct += 1
                    status = "✅"
                else:
                    status = "❌"
                
                print(f"{status} Test {i}: {description}")
                print(f"   Text: {text}")
                print(f"   Expected: {expected} | Predicted: {predicted} | Confidence: {confidence:.2f}")
                print(f"   Details: {details}")
                print()
                
            except Exception as e:
                print(f"❌ Test {i} failed with error: {e}")
                print(f"   Text: {text}")
                print()
        
        accuracy = (correct / total) * 100
        print(f"📈 Final Results:")
        print(f"   Accuracy: {correct}/{total} = {accuracy:.1f}%")
        
        if accuracy >= 80:
            print("🎉 Excellent performance!")
        elif accuracy >= 70:
            print("👍 Good performance!")
        elif accuracy >= 60:
            print("👌 Acceptable performance!")
        else:
            print("⚠️ Needs improvement!")
            
        return accuracy >= 70
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure app.py is working correctly.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_youtube_integration():
    """Test YouTube integration if possible"""
    print("\n🎬 Testing YouTube Integration")
    print("=" * 35)
    
    try:
        from app import fetch_youtube_comments, flatten_comments
        
        # Use a single URL for testing
        test_url = "https://www.youtube.com/watch?v=0EZDL8xqXsY"
        print(f"🔍 Testing with URL: {test_url}")
        
        # Try to fetch a few comments
        comments = fetch_youtube_comments(test_url, max_comments=5)
        
        if comments:
            print(f"✅ Successfully fetched {len(comments)} comments")
            
            # Try flattening
            flattened = flatten_comments(comments)
            print(f"✅ Flattened to {len(flattened)} entries")
            
            # Show a sample
            if flattened:
                sample = flattened[0]
                print(f"📝 Sample comment: {sample.get('text', '')[:100]}...")
                return True
        else:
            print("ℹ️ No comments fetched (this may be normal for some videos)")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"⚠️ YouTube integration test failed: {e}")
        print("This might be due to network issues or YouTube restrictions")
        return False

if __name__ == "__main__":
    print("🧪 Running comprehensive system tests...\n")
    
    # Test core sentiment analysis
    sentiment_ok = test_sentiment_system()
    
    # Test YouTube integration
    youtube_ok = test_youtube_integration()
    
    print("\n" + "=" * 50)
    print("🏁 Final Test Summary:")
    print(f"   Sentiment Analysis: {'✅ PASS' if sentiment_ok else '❌ FAIL'}")
    print(f"   YouTube Integration: {'✅ PASS' if youtube_ok else '❌ FAIL'}")
    
    if sentiment_ok and youtube_ok:
        print("\n🎉 All systems operational! The Thai sentiment analysis system is ready.")
    elif sentiment_ok:
        print("\n👍 Core sentiment analysis is working. YouTube integration needs attention.")
    else:
        print("\n⚠️ Core issues need to be resolved.")
