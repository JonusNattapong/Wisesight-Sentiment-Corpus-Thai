#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Minimal working test for core functionality
"""

def test_basic():
    print("🧪 Basic Functionality Test")
    print("=" * 30)
    
    try:
        # Test 1: Import basic functions
        from app import enhanced_analyze_sentiment, analyze_sarcasm
        print("✅ Core functions imported")
        
        # Test 2: Basic sentiment
        text1 = "ดีใจมาก ❤️"
        result1 = enhanced_analyze_sentiment(text1)
        print(f"✅ Positive: {result1['sentiment']} ({result1['confidence']:.2f})")
        
        # Test 3: Sarcasm detection
        text2 = "เยี่ยมจริงๆ เนอะ 🙄"
        sarcasm = analyze_sarcasm(text2)
        result2 = enhanced_analyze_sentiment(text2)
        print(f"✅ Sarcasm detected: {sarcasm['is_sarcastic']}")
        print(f"✅ Sentiment: {result2['sentiment']} ({result2['confidence']:.2f})")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic()
    print(f"\n🏁 Status: {'OPERATIONAL' if success else 'ERROR'}")
