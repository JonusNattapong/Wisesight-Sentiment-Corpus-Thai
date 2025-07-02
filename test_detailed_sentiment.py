#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Detailed Thai Sentiment Analysis System
ชุดทดสอบสำหรับระบบ sentiment analysis ภาษาไทยแบบละเอียด
"""

import json
import os
import sys
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from detailed_thai_sentiment import (
        DetailedThaiSentimentAnalyzer,
        EMOTION_LABELS,
        EMOTION_GROUPS,
        create_training_data_format,
        save_training_data
    )
    DETAILED_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing detailed_thai_sentiment: {e}")
    DETAILED_AVAILABLE = False

try:
    from sentiment_integration import (
        analyze_detailed_sentiment,
        analyze_social_media_batch,
        get_sentiment_statistics,
        enhanced_analyze_sentiment
    )
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing sentiment_integration: {e}")
    INTEGRATION_AVAILABLE = False

class DetailedSentimentTester:
    """ตัวทดสอบระบบ sentiment analysis แบบละเอียด"""
    
    def __init__(self):
        self.test_cases = self._create_test_cases()
        self.analyzer = None
        if DETAILED_AVAILABLE:
            self.analyzer = DetailedThaiSentimentAnalyzer()
    
    def _create_test_cases(self) -> List[Dict[str, Any]]:
        """สร้างชุดข้อมูลทดสอบ"""
        return [
            # === POSITIVE EMOTIONS ===
            {
                "text": "ดีใจมากเลย! รักมาก ❤️😍",
                "expected_single": "ดีใจ",
                "expected_multi": ["ดีใจ", "รัก"],
                "expected_group": "Positive",
                "expected_sentiment": "positive"
            },
            {
                "text": "ซึ้งใจมากเลย น้ำตาซึม ประทับใจจริงๆ 😭💞",
                "expected_single": "ซึ้งใจ",
                "expected_multi": ["ซึ้งใจ"],
                "expected_group": "Positive",
                "expected_sentiment": "positive"
            },
            {
                "text": "โอเค ใช้ได้ ปกติดี พอใจ",
                "expected_single": "พอใจ",
                "expected_multi": ["พอใจ"],
                "expected_group": "Positive",
                "expected_sentiment": "positive"
            },
            
            # === NEGATIVE EMOTIONS ===
            {
                "text": "โกรธมากเลย! ห่วยแตกแล้วจริงๆ 😡🤬",
                "expected_single": "โกรธ",
                "expected_multi": ["โกรธ"],
                "expected_group": "Negative",
                "expected_sentiment": "negative"
            },
            {
                "text": "เศร้าใจมาก เสียใจจริงๆ ผิดหวังมาก 😢💔",
                "expected_single": "เสียใจ",
                "expected_multi": ["เสียใจ", "ผิดหวัง"],
                "expected_group": "Negative",
                "expected_sentiment": "negative"
            },
            {
                "text": "กลัวมากเลย ตกใจจริงๆ หวาดเสียว 😱😨",
                "expected_single": "กลัว",
                "expected_multi": ["กลัว", "ตกใจ"],
                "expected_group": "Negative",
                "expected_sentiment": "negative"
            },
            
            # === NEUTRAL EMOTIONS ===
            {
                "text": "ข้อมูลข่าวสารประจำวัน สถานการณ์ปกติดี",
                "expected_single": "ข้อมูลข่าวสาร",
                "expected_multi": ["ข้อมูลข่าวสาร"],
                "expected_group": "Neutral",
                "expected_sentiment": "neutral"
            },
            {
                "text": "เฉยๆ ธรรมดา ไม่รู้สึกอะไร",
                "expected_single": "เฉย ๆ",
                "expected_multi": ["เฉย ๆ"],
                "expected_group": "Neutral",
                "expected_sentiment": "neutral"
            },
            
            # === OTHERS (COMPLEX EMOTIONS) ===
            {
                "text": "อ่อ... ดีจริงๆ เนอะ บริการเยี่ยมมาก 🙄",
                "expected_single": "ประชด",
                "expected_multi": ["ประชด"],
                "expected_group": "Others",
                "expected_sentiment": "negative"
            },
            {
                "text": "ขำมากเลย! ตลกดี 555 😂🤣",
                "expected_single": "ขำขัน",
                "expected_multi": ["ขำขัน"],
                "expected_group": "Others",
                "expected_sentiment": "positive"
            },
            {
                "text": "สับสนมาก งงเลย เข้าใจไม่ได้ 🤔😵‍💫",
                "expected_single": "สับสน",
                "expected_multi": ["สับสน"],
                "expected_group": "Others",
                "expected_sentiment": "neutral"
            },
            
            # === MIXED EMOTIONS ===
            {
                "text": "โกรธจนขำอะ! ทำไมต้องมาแบบนี้ด้วย 555 😡😂",
                "expected_single": "โกรธ",  # Primary emotion
                "expected_multi": ["โกรธ", "ขำขัน"],
                "expected_group": "Negative",  # Primary group
                "expected_sentiment": "negative"
            },
            {
                "text": "ประชดเก่งมาก เสียดสีจนเศร้า ใจร้าย",
                "expected_single": "ประชด",
                "expected_multi": ["ประชด", "เสียใจ"],
                "expected_group": "Others",
                "expected_sentiment": "negative"
            },
            {
                "text": "ชอบมาก แต่ก็ผิดหวังนิดหน่อย เอาแต่ใจ",
                "expected_single": "ชอบ",
                "expected_multi": ["ชอบ", "ผิดหวัง"],
                "expected_group": "Positive",
                "expected_sentiment": "positive"
            }
        ]
    
    def test_basic_functionality(self) -> Dict[str, Any]:
        """ทดสอบการทำงานพื้นฐาน"""
        print("🧪 Testing Basic Functionality...")
        
        if not DETAILED_AVAILABLE:
            return {"status": "failed", "error": "Detailed sentiment analysis not available"}
        
        results = {
            "total_tests": len(self.test_cases),
            "single_label_accuracy": 0,
            "multi_label_accuracy": 0,
            "sentiment_mapping_accuracy": 0,
            "failed_cases": [],
            "detailed_results": []
        }
        
        single_correct = 0
        multi_correct = 0
        sentiment_correct = 0
        
        for i, test_case in enumerate(self.test_cases):
            text = test_case["text"]
            
            try:
                # Test single label
                single_result = self.analyzer.analyze_single_label(text)
                single_predicted = single_result["label"]
                single_expected = test_case["expected_single"]
                single_match = single_predicted == single_expected
                
                if single_match:
                    single_correct += 1
                
                # Test multi label
                multi_result = self.analyzer.analyze_multi_label(text, threshold=0.25)
                multi_predicted = set(multi_result["labels"])
                multi_expected = set(test_case["expected_multi"])
                # Check if predicted contains at least one expected emotion
                multi_match = len(multi_predicted.intersection(multi_expected)) > 0
                
                if multi_match:
                    multi_correct += 1
                
                # Test sentiment mapping
                mapped_sentiment = self._map_emotion_to_sentiment(single_predicted)
                expected_sentiment = test_case["expected_sentiment"]
                sentiment_match = mapped_sentiment == expected_sentiment
                
                if sentiment_match:
                    sentiment_correct += 1
                
                # Store detailed result
                test_result = {
                    "case_id": i + 1,
                    "text": text,
                    "single_predicted": single_predicted,
                    "single_expected": single_expected,
                    "single_match": single_match,
                    "multi_predicted": list(multi_predicted),
                    "multi_expected": list(multi_expected),
                    "multi_match": multi_match,
                    "sentiment_predicted": mapped_sentiment,
                    "sentiment_expected": expected_sentiment,
                    "sentiment_match": sentiment_match,
                    "confidence": single_result["confidence"]
                }
                
                results["detailed_results"].append(test_result)
                
                if not (single_match and multi_match and sentiment_match):
                    results["failed_cases"].append(test_result)
            
            except Exception as e:
                error_result = {
                    "case_id": i + 1,
                    "text": text,
                    "error": str(e)
                }
                results["failed_cases"].append(error_result)
        
        # Calculate accuracies
        total = len(self.test_cases)
        results["single_label_accuracy"] = (single_correct / total) * 100
        results["multi_label_accuracy"] = (multi_correct / total) * 100
        results["sentiment_mapping_accuracy"] = (sentiment_correct / total) * 100
        
        return results
    
    def test_integration_module(self) -> Dict[str, Any]:
        """ทดสอบ integration module"""
        print("🔗 Testing Integration Module...")
        
        if not INTEGRATION_AVAILABLE:
            return {"status": "failed", "error": "Integration module not available"}
        
        results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
        
        test_texts = [
            "ดีใจมากเลย! รักมาก",
            "โกรธจนขำอะ! แปลกดี 555",
            "ข้อมูลข่าวสารประจำวัน"
        ]
        
        try:
            # Test single analysis
            for text in test_texts:
                result = analyze_detailed_sentiment(text, mode="single")
                assert "sentiment" in result
                assert "detailed_emotion" in result
                assert "confidence" in result
                results["tests_passed"] += 1
            
            # Test multi analysis
            for text in test_texts:
                result = analyze_detailed_sentiment(text, mode="multi", threshold=0.3)
                assert "sentiment" in result
                assert "detailed_emotions" in result
                assert isinstance(result["detailed_emotions"], list)
                results["tests_passed"] += 1
            
            # Test batch analysis
            sample_comments = [
                {"text": text, "author": f"user{i}", "platform": "test"}
                for i, text in enumerate(test_texts)
            ]
            
            analyzed = analyze_social_media_batch(sample_comments, mode="single", show_progress=False)
            assert len(analyzed) == len(sample_comments)
            for comment in analyzed:
                assert "sentiment_analysis" in comment
            results["tests_passed"] += 1
            
            # Test statistics
            stats = get_sentiment_statistics(analyzed)
            assert "total_comments" in stats
            assert "sentiment_counts" in stats
            results["tests_passed"] += 1
            
        except Exception as e:
            results["tests_failed"] += 1
            results["errors"].append(str(e))
        
        return results
    
    def test_training_data_creation(self) -> Dict[str, Any]:
        """ทดสอบการสร้างข้อมูล training"""
        print("🎓 Testing Training Data Creation...")
        
        if not DETAILED_AVAILABLE:
            return {"status": "failed", "error": "Detailed sentiment analysis not available"}
        
        results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
        
        try:
            # Test single label format
            single_format = create_training_data_format("ดีใจมาก", "ดีใจ", "classification")
            assert "text" in single_format
            assert "label" in single_format
            assert "label_id" in single_format
            results["tests_passed"] += 1
            
            # Test multi label format
            multi_format = create_training_data_format("โกรธจนขำ", ["โกรธ", "ขำขัน"], "classification")
            assert "text" in multi_format
            assert "labels" in multi_format
            assert "label_vector" in multi_format
            assert len(multi_format["label_vector"]) == len(EMOTION_LABELS)
            results["tests_passed"] += 1
            
            # Test instruction format
            instruction_format = create_training_data_format("ประชดเก่ง", "ประชด", "instruction")
            assert "instruction" in instruction_format
            assert "input" in instruction_format
            assert "output" in instruction_format
            results["tests_passed"] += 1
            
            # Test saving data
            test_data = [single_format, multi_format, instruction_format]
            output_path = "test_training_data.jsonl"
            save_training_data(test_data, output_path, "jsonl")
            
            # Check if file exists
            if os.path.exists(output_path):
                results["tests_passed"] += 1
                # Clean up
                os.remove(output_path)
            else:
                results["tests_failed"] += 1
                results["errors"].append("Training data file not created")
            
        except Exception as e:
            results["tests_failed"] += 1
            results["errors"].append(str(e))
        
        return results
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """ทดสอบกรณีพิเศษ"""
        print("🎭 Testing Edge Cases...")
        
        if not DETAILED_AVAILABLE:
            return {"status": "failed", "error": "Detailed sentiment analysis not available"}
        
        results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
        
        edge_cases = [
            "",  # Empty string
            "   ",  # Whitespace only
            "a",  # Single character
            "😊",  # Emoji only
            "Hello world",  # English text
            "123456",  # Numbers only
            "!@#$%^&*()",  # Special characters only
            "ไทย" * 100,  # Very long text
            "โกรธ" + " " * 100 + "ขำ",  # Text with lots of spaces
        ]
        
        for text in edge_cases:
            try:
                # Test single label (should not crash)
                single_result = self.analyzer.analyze_single_label(text)
                assert "label" in single_result
                assert "confidence" in single_result
                
                # Test multi label (should not crash)
                multi_result = self.analyzer.analyze_multi_label(text)
                assert "labels" in multi_result
                assert isinstance(multi_result["labels"], list)
                
                results["tests_passed"] += 1
                
            except Exception as e:
                results["tests_failed"] += 1
                results["errors"].append(f"Failed on '{text[:20]}...': {str(e)}")
        
        return results
    
    def _map_emotion_to_sentiment(self, emotion: str) -> str:
        """Helper: แปลงอารมณ์เป็น sentiment พื้นฐาน"""
        for group, emotions in EMOTION_GROUPS.items():
            if emotion in emotions:
                if group == "Positive":
                    return "positive"
                elif group == "Negative":
                    return "negative"
                elif group == "Neutral":
                    return "neutral"
                elif group == "Others":
                    if emotion in ["ขำขัน"]:
                        return "positive"
                    elif emotion in ["ประชด", "เสียดสี"]:
                        return "negative"
                    else:
                        return "neutral"
        return "neutral"
    
    def run_all_tests(self) -> Dict[str, Any]:
        """รันการทดสอบทั้งหมด"""
        print("🧪 Running Complete Test Suite for Detailed Thai Sentiment Analysis")
        print("=" * 80)
        
        all_results = {
            "system_info": {
                "detailed_available": DETAILED_AVAILABLE,
                "integration_available": INTEGRATION_AVAILABLE,
                "emotion_labels_count": len(EMOTION_LABELS) if DETAILED_AVAILABLE else 0,
                "emotion_groups_count": len(EMOTION_GROUPS) if DETAILED_AVAILABLE else 0
            },
            "tests": {}
        }
        
        if not DETAILED_AVAILABLE:
            print("❌ Detailed sentiment analysis not available. Cannot run tests.")
            return all_results
        
        # Run basic functionality test
        basic_results = self.test_basic_functionality()
        all_results["tests"]["basic_functionality"] = basic_results
        
        print(f"\n📊 Basic Functionality Results:")
        print(f"   Single Label Accuracy: {basic_results['single_label_accuracy']:.1f}%")
        print(f"   Multi Label Accuracy: {basic_results['multi_label_accuracy']:.1f}%")
        print(f"   Sentiment Mapping Accuracy: {basic_results['sentiment_mapping_accuracy']:.1f}%")
        print(f"   Failed Cases: {len(basic_results['failed_cases'])}")
        
        # Run integration test
        integration_results = self.test_integration_module()
        all_results["tests"]["integration"] = integration_results
        
        print(f"\n🔗 Integration Test Results:")
        print(f"   Tests Passed: {integration_results['tests_passed']}")
        print(f"   Tests Failed: {integration_results['tests_failed']}")
        if integration_results['errors']:
            print(f"   Errors: {integration_results['errors']}")
        
        # Run training data test
        training_results = self.test_training_data_creation()
        all_results["tests"]["training_data"] = training_results
        
        print(f"\n🎓 Training Data Test Results:")
        print(f"   Tests Passed: {training_results['tests_passed']}")
        print(f"   Tests Failed: {training_results['tests_failed']}")
        if training_results['errors']:
            print(f"   Errors: {training_results['errors']}")
        
        # Run edge cases test
        edge_results = self.test_edge_cases()
        all_results["tests"]["edge_cases"] = edge_results
        
        print(f"\n🎭 Edge Cases Test Results:")
        print(f"   Tests Passed: {edge_results['tests_passed']}")
        print(f"   Tests Failed: {edge_results['tests_failed']}")
        if edge_results['errors']:
            print(f"   Errors: {edge_results['errors'][:3]}...")  # Show first 3 errors
        
        # Overall summary
        total_passed = sum([
            basic_results.get('single_label_accuracy', 0) >= 70,  # At least 70% accuracy
            basic_results.get('multi_label_accuracy', 0) >= 60,   # At least 60% accuracy
            integration_results.get('tests_passed', 0) > integration_results.get('tests_failed', 0),
            training_results.get('tests_passed', 0) > training_results.get('tests_failed', 0),
            edge_results.get('tests_passed', 0) > edge_results.get('tests_failed', 0)
        ])
        
        print(f"\n🎯 Overall Test Summary:")
        print(f"   Major Components Passed: {total_passed}/5")
        print(f"   System Status: {'✅ PASSED' if total_passed >= 4 else '❌ FAILED'}")
        
        all_results["overall_status"] = "PASSED" if total_passed >= 4 else "FAILED"
        all_results["components_passed"] = total_passed
        
        return all_results

def main():
    """รันการทดสอบหลัก"""
    tester = DetailedSentimentTester()
    results = tester.run_all_tests()
    
    # Save results
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 Full test results saved to: test_results.json")
    
    # Show failed cases if any
    if "basic_functionality" in results["tests"]:
        failed_cases = results["tests"]["basic_functionality"].get("failed_cases", [])
        if failed_cases:
            print(f"\n❌ Failed Test Cases ({len(failed_cases)}):")
            for case in failed_cases[:3]:  # Show first 3 failed cases
                if "text" in case:
                    print(f"   Text: {case['text'][:50]}...")
                    if "single_predicted" in case:
                        print(f"   Expected: {case.get('single_expected')} | Got: {case.get('single_predicted')}")
    
    return results["overall_status"] == "PASSED"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
