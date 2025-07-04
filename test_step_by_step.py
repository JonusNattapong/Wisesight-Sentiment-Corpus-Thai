#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test individual functions step by step
"""

print("🧪 Testing individual functions...")

# Test 1: Import basic modules
print("1️⃣ Testing basic imports...")
try:
    import re
    import emoji
    print("✅ Basic imports work")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")

# Test 2: Test emotion patterns
print("2️⃣ Testing emotion patterns...")
try:
    from app import EMOTION_PATTERNS
    print(f"✅ EMOTION_PATTERNS loaded with {len(EMOTION_PATTERNS)} emotions")
    print(f"   Sample emotions: {list(EMOTION_PATTERNS.keys())[:5]}")
except Exception as e:
    print(f"❌ EMOTION_PATTERNS failed: {e}")

# Test 3: Test extract_emojis
print("3️⃣ Testing emoji extraction...")
try:
    from app import extract_emojis
    test_text = "ดีใจมาก 😊❤️"
    emojis = extract_emojis(test_text)
    print(f"✅ extract_emojis works: {emojis}")
except Exception as e:
    print(f"❌ extract_emojis failed: {e}")

# Test 4: Test sarcasm detection
print("4️⃣ Testing sarcasm detection...")
try:
    from app import analyze_sarcasm
    test_text = "ขอบคุณนะคะที่ทำให้วันนี้เป็นวันที่แย่ที่สุดในชีวิต 😊"
    result = analyze_sarcasm(test_text)
    print(f"✅ analyze_sarcasm works: {result}")
except Exception as e:
    print(f"❌ analyze_sarcasm failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test calculate_emotion_scores
print("5️⃣ Testing emotion score calculation...")
try:
    from app import calculate_emotion_scores
    test_text = "ดีใจมากเลย รักเธอที่สุดเลย ❤️😍"
    scores = calculate_emotion_scores(test_text)
    print(f"✅ calculate_emotion_scores works: {scores}")
except Exception as e:
    print(f"❌ calculate_emotion_scores failed: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Test complete!")
