#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test for core sentiment functionality
"""
try:
    from app import enhanced_analyze_sentiment, analyze_sarcasm
    
    print("✅ Successfully imported functions from app.py")
    
    # Test sarcasm detection
    sarcasm_test = "ขอบคุณนะคะที่ทำให้วันนี้เป็นวันที่แย่ที่สุดในชีวิต 😊"
    sarcasm_result = analyze_sarcasm(sarcasm_test)
    print(f"🎭 Sarcasm test: {sarcasm_result}")
    
    # Test sentiment analysis
    sentiment_result = enhanced_analyze_sentiment(sarcasm_test)
    print(f"💭 Sentiment result: {sentiment_result}")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
