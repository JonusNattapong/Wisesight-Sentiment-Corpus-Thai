#!/usr/bin/env python3
"""
Test ML-Enhanced Sentiment Analysis
สคริปทดสอบ ML Sentiment Analysis สำหรับเปรียบเทียบความแม่นยำ
"""

import json
from pathlib import Path
from social_media_utils import advanced_thai_sentiment_analysis, ml_enhanced_sentiment_analysis

def test_sentiment_comparison():
    """Compare rule-based vs ML-enhanced sentiment analysis"""
    
    # Test cases with expected sentiment
    test_cases = [
        {
            "text": "เน็ต TRUE ช่วงนี้แย่มาก เน็ตล่มบ่อยมาก ใช้ไม่ได้เลย",
            "expected": "negative",
            "description": "Complaint about TRUE internet"
        },
        {
            "text": "ขอบคุณครับ แก้ปัญหาได้แล้ว เน็ตเร็วดีมาก",
            "expected": "positive", 
            "description": "Gratitude and satisfaction"
        },
        {
            "text": "พอดีเราใช้โปรแบบรายเดือน ตอนนี้ใช้ปกติครับ",
            "expected": "neutral",
            "description": "Factual statement"
        },
        {
            "text": "TRUE ห่วยแตกแล้วจริงๆ โทรไปแจ้งก็ไม่แก้ไข",
            "expected": "negative",
            "description": "Strong negative opinion"
        },
        {
            "text": "สุดยอดมากครับ ปัญหาที่แจ้งไว้ได้รับการแก้ไขแล้ว ประทับใจมาก",
            "expected": "positive",
            "description": "Very positive feedback"
        }
    ]
    
    print("=" * 80)
    print("🔥 ML-Enhanced Thai Sentiment Analysis Comparison")
    print("=" * 80)
    
    rule_correct = 0
    ml_correct = 0
    
    for i, case in enumerate(test_cases, 1):
        text = case["text"]
        expected = case["expected"]
        description = case["description"]
        
        print(f"\n[Test {i}] {description}")
        print(f"Text: {text}")
        print(f"Expected: {expected}")
        print("-" * 60)
        
        # Rule-based analysis
        rule_result = advanced_thai_sentiment_analysis(text)
        rule_sentiment = get_sentiment_from_score(rule_result["sentiment_score"])
        rule_match = rule_sentiment == expected
        if rule_match:
            rule_correct += 1
            
        print(f"📊 Rule-based:")
        print(f"   Sentiment: {rule_sentiment} {'✅' if rule_match else '❌'}")
        print(f"   Score: {rule_result['sentiment_score']}")
        print(f"   Emotion: {rule_result['emotion']}")
        
        # ML-enhanced analysis  
        try:
            ml_result = ml_enhanced_sentiment_analysis(text)
            ml_sentiment = ml_result.get("sentiment", "neutral")
            ml_match = ml_sentiment == expected
            if ml_match:
                ml_correct += 1
                
            print(f"🤖 ML-Enhanced:")
            print(f"   Sentiment: {ml_sentiment} {'✅' if ml_match else '❌'}")
            print(f"   Score: {ml_result['sentiment_score']}")
            print(f"   Confidence: {ml_result.get('confidence', 0):.2f}")
            print(f"   Emotion: {ml_result['emotion']}")
            if ml_result.get('ml_enhanced'):
                print(f"   Model: {ml_result.get('model_type', 'unknown')}")
            else:
                print(f"   Fallback: {ml_result.get('fallback_reason', 'unknown')}")
                
        except Exception as e:
            print(f"🤖 ML-Enhanced: ❌ Error - {e}")
            ml_sentiment = "error"
    
    # Summary
    print("\n" + "=" * 80)
    print("📈 ACCURACY COMPARISON")
    print("=" * 80)
    
    total_tests = len(test_cases)
    rule_accuracy = (rule_correct / total_tests) * 100
    ml_accuracy = (ml_correct / total_tests) * 100
    improvement = ml_accuracy - rule_accuracy
    
    print(f"Rule-based accuracy:  {rule_correct}/{total_tests} ({rule_accuracy:.1f}%)")
    print(f"ML-enhanced accuracy: {ml_correct}/{total_tests} ({ml_accuracy:.1f}%)")
    print(f"Improvement:          {improvement:+.1f}%")
    
    if improvement > 0:
        print(f"🎉 ML model shows {improvement:.1f}% improvement!")
    elif improvement == 0:
        print("🤝 Both methods perform equally well")
    else:
        print(f"📉 Rule-based is {abs(improvement):.1f}% better")
    
    print("\n💡 Benefits of ML-Enhanced Analysis:")
    print("   ✅ Better handling of complex Thai expressions")
    print("   ✅ Learning from context and training data") 
    print("   ✅ Confidence scores for reliability assessment")
    print("   ✅ Ensemble approach combines multiple models")
    print("   ✅ Continuous improvement with more data")

def get_sentiment_from_score(score):
    """Convert sentiment score to sentiment label"""
    if score > 0.2:
        return "positive"
    elif score < -0.2:
        return "negative"
    else:
        return "neutral"

def show_ml_features():
    """Show available ML sentiment analysis features"""
    print("\n" + "=" * 80)
    print("🛠️  ML SENTIMENT ANALYSIS FEATURES")
    print("=" * 80)
    
    print("📋 Available Models:")
    print("   • Logistic Regression (fast, interpretable)")
    print("   • Random Forest (robust, handles complex patterns)")
    print("   • SVM (good for text classification)")
    print("   • Ensemble (combines multiple models)")
    
    print("\n🎯 Advanced Features:")
    print("   • Thai text preprocessing with PyThaiNLP")
    print("   • TF-IDF vectorization with n-grams")
    print("   • Confidence scoring")
    print("   • Fallback to rule-based analysis")
    print("   • Training data augmentation")
    print("   • Cross-validation for model evaluation")
    
    print("\n🚀 CLI Usage:")
    print("   # Basic sentiment analysis")
    print("   python get_comments.py pantip 43494778 --include_sentiment")
    print()
    print("   # Advanced sentiment with emotion, intent, etc.")
    print("   python get_comments.py pantip 43494778 --include_advanced_sentiment")
    print()
    print("   # ML-enhanced sentiment (best accuracy)")
    print("   python get_comments.py pantip 43494778 --include_advanced_sentiment --use_ml_sentiment")
    print()
    print("   # Multiple sources with ML")
    print("   python get_comments.py pantip 43494778 43494779 --include_advanced_sentiment --use_ml_sentiment")
    
if __name__ == "__main__":
    test_sentiment_comparison()
    show_ml_features()
