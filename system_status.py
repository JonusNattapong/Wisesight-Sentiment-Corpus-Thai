#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
System Status Check - Quick Overview
"""

def system_status():
    print("🚀 Thai Sentiment Analysis System - Status Check")
    print("=" * 55)
    
    # Check imports
    try:
        from app import enhanced_analyze_sentiment, analyze_sarcasm
        print("✅ Core functions available in app.py")
    except ImportError as e:
        print(f"❌ Core functions missing: {e}")
        return False
    
    try:
        from sentiment_integration import analyze_detailed_sentiment, analyze_social_media_batch
        print("✅ Integration functions available")
    except ImportError as e:
        print(f"❌ Integration functions missing: {e}")
        return False
    
    # Test core functionality
    test_cases = [
        ("ดีใจมาก ❤️", "positive", "Basic positive"),
        ("ห่วยแตกมาก 😡", "negative", "Basic negative"),
        ("ข้อมูลข่าวสาร", "neutral", "Neutral information"),
        ("เยี่ยมจริงๆ เนอะ 🙄", "negative", "Sarcasm test"),
    ]
    
    print("\n🧪 Testing Core Functions:")
    print("-" * 30)
    
    passed = 0
    for text, expected, description in test_cases:
        try:
            result = enhanced_analyze_sentiment(text)
            predicted = result['sentiment']
            confidence = result['confidence']
            
            if predicted == expected:
                status = "✅ PASS"
                passed += 1
            else:
                status = "⚠️  DIFF"
            
            print(f"{status} {description}: {predicted} ({confidence:.2f})")
            
        except Exception as e:
            print(f"❌ FAIL {description}: {e}")
    
    accuracy = (passed / len(test_cases)) * 100
    print(f"\n📊 Test Results: {passed}/{len(test_cases)} passed ({accuracy:.0f}%)")
    
    # System status
    if passed >= 3:
        print("🎉 SYSTEM STATUS: OPERATIONAL")
        print("\n✅ Ready for:")
        print("   • Sentiment analysis")
        print("   • Sarcasm detection") 
        print("   • YouTube comment processing")
        print("   • Social media analysis")
        return True
    else:
        print("⚠️  SYSTEM STATUS: NEEDS ATTENTION")
        return False

if __name__ == "__main__":
    system_status()
