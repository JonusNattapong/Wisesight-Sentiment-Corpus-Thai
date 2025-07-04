#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick validation test for the Thai sentiment analysis system
"""

def quick_validation():
    """Quick validation of core functionality"""
    print("🚀 Quick System Validation")
    print("=" * 30)
    
    test_cases = [
        ("ดีใจมากเลย ❤️", "positive"),
        ("ห่วยแตกมาก 😡", "negative"), 
        ("ข้อมูลข่าวสาร", "neutral"),
        ("เยี่ยมจริงๆ เนอะ 🙄", "negative"),  # Sarcasm
    ]
    
    try:
        from app import enhanced_analyze_sentiment
        
        success_count = 0
        for text, expected in test_cases:
            try:
                result = enhanced_analyze_sentiment(text)
                predicted = result["sentiment"]
                confidence = result["confidence"]
                
                is_correct = predicted == expected
                status = "✅" if is_correct else "❌"
                
                print(f"{status} '{text}' -> {predicted} ({confidence:.2f})")
                
                if is_correct:
                    success_count += 1
                    
            except Exception as e:
                print(f"❌ Error analyzing '{text}': {e}")
        
        accuracy = (success_count / len(test_cases)) * 100
        print(f"\n📊 Accuracy: {success_count}/{len(test_cases)} = {accuracy:.1f}%")
        
        if accuracy >= 75:
            print("🎉 System validation PASSED!")
            return True
        else:
            print("⚠️ System validation FAILED!")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = quick_validation()
    print(f"\n🏁 System Status: {'OPERATIONAL' if success else 'NEEDS ATTENTION'}")
