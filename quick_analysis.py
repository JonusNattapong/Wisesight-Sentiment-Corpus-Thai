#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from collections import Counter

def analyze_file(file_path):
    """Quick analysis of a JSONL sentiment file"""
    comments = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    comments.append(json.loads(line))
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    print(f"📄 Analysis of: {file_path}")
    print(f"📊 Total Comments: {len(comments)}")
    print(f"🤖 ML-Enhanced: {sum(1 for c in comments if c.get('ml_enhanced'))}")
    
    # Sentiment distribution
    sentiments = [c.get('sentiment', 'unknown') for c in comments]
    print(f"\n🎯 SENTIMENT DISTRIBUTION:")
    for sentiment, count in Counter(sentiments).most_common():
        pct = count/len(comments)*100
        print(f"  {sentiment.capitalize()}: {count} ({pct:.1f}%)")
    
    # Emotion distribution
    emotions = [c.get('emotion', 'unknown') for c in comments]
    print(f"\n😊 EMOTION DISTRIBUTION:")
    for emotion, count in Counter(emotions).most_common():
        pct = count/len(comments)*100
        print(f"  {emotion.capitalize()}: {count} ({pct:.1f}%)")
    
    # Source distribution
    sources = [c.get('source_query', 'unknown') for c in comments]
    print(f"\n📍 SOURCE DISTRIBUTION:")
    for source, count in Counter(sources).most_common():
        pct = count/len(comments)*100
        print(f"  {source}: {count} ({pct:.1f}%)")
    
    # ML confidence stats
    confidence_scores = [c.get('ml_confidence', 0) for c in comments if 'ml_confidence' in c]
    if confidence_scores:
        avg_conf = sum(confidence_scores) / len(confidence_scores)
        print(f"\n🎯 ML CONFIDENCE:")
        print(f"  Average: {avg_conf:.3f}")
        print(f"  Min: {min(confidence_scores):.3f}")
        print(f"  Max: {max(confidence_scores):.3f}")
    
    # Sample high-confidence comments
    high_conf_comments = [c for c in comments if c.get('ml_confidence', 0) >= 0.6]
    if high_conf_comments:
        print(f"\n⭐ HIGH-CONFIDENCE SAMPLES (>= 0.6):")
        for i, comment in enumerate(high_conf_comments[:3], 1):
            text = comment.get('text', '')[:100] + '...' if len(comment.get('text', '')) > 100 else comment.get('text', '')
            print(f"[{i}] {text}")
            print(f"    Sentiment: {comment.get('sentiment')} (confidence: {comment.get('ml_confidence'):.2f})")
            print(f"    Emotion: {comment.get('emotion')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_file(sys.argv[1])
    else:
        analyze_file("data/pantip_comments_unlimited_20250620_195002.jsonl")
