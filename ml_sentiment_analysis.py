#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Thai Sentiment Analysis with Machine Learning Models
ระบบ sentiment analysis ภาษาไทยแบบขั้นสูงด้วย ML models
"""

import os
import re
import json
import pickle
import numpy as np
import warnings
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    import locale
    try:
        # Set UTF-8 for stdout/stderr
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        else:
            # Fallback for older Python versions
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
        
        # Set locale to UTF-8 if possible
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except:
                pass  # Use system default
    except Exception as e:
        print(f"Warning: Could not set UTF-8 encoding: {e}")

# Suppress warnings
warnings.filterwarnings('ignore')

# --- ML Libraries ---
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# --- Deep Learning Libraries ---
try:
    import torch
    import torch.nn as nn
    from transformers import (
        AutoTokenizer, AutoModelForSequenceClassification,
        pipeline, Trainer, TrainingArguments
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# --- Thai NLP Libraries ---
try:
    from pythainlp import word_tokenize
    from pythainlp.corpus import thai_stopwords
    PYTHAINLP_AVAILABLE = True
except ImportError:
    PYTHAINLP_AVAILABLE = False

def safe_print(text: str, encoding: str = 'utf-8', errors: str = 'replace'):
    """Safe printing function that handles encoding issues"""
    try:
        if isinstance(text, bytes):
            text = text.decode(encoding, errors=errors)
        elif isinstance(text, str):
            # Clean surrogate characters
            text = text.encode(encoding, errors=errors).decode(encoding, errors=errors)
        print(text)
    except Exception as e:
        # Fallback: print with ASCII only
        try:
            clean_text = text.encode('ascii', errors='ignore').decode('ascii')
            print(f"[ENCODING_ISSUE] {clean_text}")
        except:
            print("[ENCODING_ERROR] Unable to display text")

def clean_unicode_text(text: str) -> str:
    """Clean text from problematic Unicode characters"""
    if not isinstance(text, str):
        return str(text)
    
    try:
        # Remove surrogate characters
        text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        
        # Remove or replace problematic characters
        text = re.sub(r'[\udce6\udce7\udce8\udce9]', '', text)  # Remove common surrogates
        text = re.sub(r'[\u0000-\u001f\u007f-\u009f]', '', text)  # Remove control characters
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    except Exception:
        # Fallback: keep only ASCII
        return re.sub(r'[^\x00-\x7F]+', ' ', text).strip()

class ThaiTextPreprocessor:
    """ตัวประมวลผลข้อความภาษาไทยล่วงหน้า"""
    
    def __init__(self):
        self.stop_words = set()
        if PYTHAINLP_AVAILABLE:
            # Convert frozenset to set to allow updates
            stopwords_from_pythainlp = thai_stopwords()
            if isinstance(stopwords_from_pythainlp, frozenset):
                self.stop_words = set(stopwords_from_pythainlp)
            else:
                self.stop_words = set(stopwords_from_pythainlp) if stopwords_from_pythainlp else set()
        
        # เพิ่ม stopwords เพิ่มเติม
        additional_stops = {
            'ครับ', 'ค่ะ', 'คะ', 'จ้า', 'เลย', 'แล้ว', 'ที่', 'นะ', 'นี่',
            'นั่น', 'นั้น', 'อะ', 'เอ่อ', 'อืม', 'เอ', 'แหะ', 'โอ้', 'ว้าว'
        }
        self.stop_words.update(additional_stops)
    
    def clean_text(self, text: str) -> str:
        """ทำความสะอาดข้อความ"""
        if not text:
            return ""
        
        # Clean unicode first
        text = clean_unicode_text(text)
        
        # ลบ URLs
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        
        # ลบ HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # ลบอีโมจิและสัญลักษณ์พิเศษ (เก็บบางตัวที่สำคัญ)
        text = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s\.\!\?\,\:\;\-\(\)]', ' ', text)
        
        # ลบเลขที่ยาวเกินไป (เบอร์โทร, etc.)
        text = re.sub(r'\d{8,}', '', text)
        
        # ลบช่องว่างเกิน
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """แยกคำภาษาไทย"""
        text = self.clean_text(text)
        
        if PYTHAINLP_AVAILABLE:
            tokens = word_tokenize(text, engine='newmm')
        else:
            # Fallback: split by spaces
            tokens = text.split()
        
        # กรองคำที่ไม่ต้องการ
        filtered_tokens = []
        for token in tokens:
            token = token.strip()
            if (len(token) > 1 and 
                token not in self.stop_words and 
                not token.isdigit() and
                not re.match(r'^[^\u0E00-\u0E7Fa-zA-Z]+$', token)):
                filtered_tokens.append(token)
        
        return filtered_tokens
    
    def preprocess(self, text: str) -> str:
        """ประมวลผลข้อความให้พร้อมสำหรับ ML"""
        tokens = self.tokenize(text)
        return ' '.join(tokens)

class ThaiSentimentMLModel:
    """Thai Sentiment Analysis ML Model"""
    
    def __init__(self, model_type: str = "logistic"):
        self.model_type = model_type
        self.preprocessor = ThaiTextPreprocessor()
        self.pipeline = None
        self.model = None
        self.vectorizer = None
        self.label_mapping = {
            'negative': 0,
            'neutral': 1, 
            'positive': 2
        }
        self.reverse_label_mapping = {v: k for k, v in self.label_mapping.items()}
        
    def create_model(self):
        """สร้าง ML model"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("sklearn is required for ML models")
        
        # สร้าง vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        # เลือก model ตาม type
        if self.model_type == "logistic":
            self.model = LogisticRegression(
                random_state=42,
                max_iter=1000,
                class_weight='balanced'
            )
        elif self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            )
        elif self.model_type == "svm":
            self.model = SVC(
                kernel='rbf',
                random_state=42,
                class_weight='balanced',
                probability=True
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        # สร้าง pipeline
        self.pipeline = Pipeline([
            ('vectorizer', self.vectorizer),
            ('classifier', self.model)
        ])
    
    def prepare_training_data(self, comments: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """เตรียมข้อมูลสำหรับฝึกสอน"""
        texts = []
        labels = []
        
        for comment in comments:
            text = comment.get('text', '')
            if not text:
                continue
            
            # ใช้ rule-based sentiment เป็น label ชั่วคราว
            sentiment_score = comment.get('sentiment_score', 0)
            emotion = comment.get('emotion', 'neutral')
            
            # แปลง sentiment เป็น label
            if sentiment_score > 0.2:
                label = 'positive'
            elif sentiment_score < -0.2:
                label = 'negative'
            else:
                label = 'neutral'
            
            # ปรับ label ตาม emotion
            if emotion in ['anger', 'sadness', 'fear']:
                label = 'negative'
            elif emotion in ['joy', 'excited']:
                label = 'positive'
            
            # ปรับ label สำหรับ complaint/problem contexts
            text_lower = text.lower()
            complaint_indicators = ['ปัญหา', 'ล่ม', 'ไม่ได้', 'หาย', 'เดือดร้อน', 'ลำบาก', 'แย่']
            if any(indicator in text_lower for indicator in complaint_indicators):
                label = 'negative'
            
            processed_text = self.preprocessor.preprocess(text)
            if len(processed_text.strip()) > 5:  # มีความยาวพอสมควร
                texts.append(processed_text)
                labels.append(label)
        
        return texts, labels
    
    def train(self, comments: List[Dict[str, Any]], test_size: float = 0.2):
        """ฝึกสอน model"""
        if self.pipeline is None:
            self.create_model()
          # เตรียมข้อมูล
        texts, labels = self.prepare_training_data(comments)
        
        if len(texts) < 10:
            raise ValueError("ข้อมูลฝึกสอนไม่เพียงพอ (ต้องการอย่างน้อย 10 ตัวอย่าง)")
        
        safe_print(f"[INFO] เตรียมข้อมูลฝึกสอน: {len(texts)} ตัวอย่าง")
        
        # แบ่งข้อมูล train/test
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        safe_print(f"[INFO] Train: {len(X_train)}, Test: {len(X_test)}")
        
        # ฝึกสอน
        safe_print(f"[INFO] กำลังฝึกสอน {self.model_type} model...")
        self.pipeline.fit(X_train, y_train)
        
        # ประเมินผล
        train_score = self.pipeline.score(X_train, y_train)
        test_score = self.pipeline.score(X_test, y_test)
        
        safe_print(f"[INFO] Train Accuracy: {train_score:.3f}")
        safe_print(f"[INFO] Test Accuracy: {test_score:.3f}")
        
        # Detailed evaluation
        y_pred = self.pipeline.predict(X_test)
        safe_print("\n[INFO] Detailed Classification Report:")
        safe_print(classification_report(y_test, y_pred))
        
        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'model_type': self.model_type
        }
    
    def predict_sentiment(self, text: str) -> Dict[str, Any]:
        """ทำนาย sentiment"""
        if self.pipeline is None:
            raise ValueError("Model ยังไม่ได้ฝึกสอน")
        
        processed_text = self.preprocessor.preprocess(text)
        
        # ทำนาย
        prediction = self.pipeline.predict([processed_text])[0]
        probabilities = self.pipeline.predict_proba([processed_text])[0]
        
        # แปลงผลลัพธ์
        sentiment = prediction
        confidence = max(probabilities)
        
        # สร้าง score
        prob_dict = dict(zip(self.pipeline.classes_, probabilities))
        sentiment_score = (
            prob_dict.get('positive', 0) - prob_dict.get('negative', 0)
        )
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'sentiment_score': sentiment_score,
            'probabilities': {
                'positive': prob_dict.get('positive', 0),
                'neutral': prob_dict.get('neutral', 0), 
                'negative': prob_dict.get('negative', 0)
            },
            'model_type': 'ml_' + self.model_type
        }
    def save_model(self, filepath: str):
        """บันทึก model"""
        model_data = {
            'pipeline': self.pipeline,
            'model_type': self.model_type,
            'label_mapping': self.label_mapping
        }
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            safe_print(f"[INFO] บันทึก model ที่: {filepath}")
        except Exception as e:
            safe_print(f"[ERROR] ไม่สามารถบันทึก model: {e}")
    
    def load_model(self, filepath: str):
        """โหลด model"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.pipeline = model_data['pipeline']
            self.model_type = model_data['model_type']
            self.label_mapping = model_data['label_mapping']
            
            safe_print(f"[INFO] โหลด model จาก: {filepath}")
        except Exception as e:
            safe_print(f"[ERROR] ไม่สามารถโหลด model: {e}")

class ThaiTransformerModel:
    """Thai Sentiment Analysis with Transformer Models from Hugging Face"""
    
    def __init__(self, model_name: str = "twitter-roberta"):        # รายการโมเดลที่เป็น public และไม่ต้องการ authentication
        self.available_models = {
            # Multilingual sentiment models (public)
            "twitter-roberta": "cardiffnlp/twitter-roberta-base-sentiment-latest",
            "multilingual-bert": "nlptown/bert-base-multilingual-uncased-sentiment",
            "distilbert-sentiment": "distilbert-base-uncased-finetuned-sst-2-english",
            
            # Basic BERT models (public)
            "bert-base": "bert-base-uncased",
            "bert-multilingual": "bert-base-multilingual-uncased",
            "distilbert": "distilbert-base-uncased",
            
            # XLM models (public)
            "xlm-roberta-base": "xlm-roberta-base",
            "xlm-roberta-large": "xlm-roberta-large",
        }
        
        # เลือกโมเดลที่จะใช้
        self.model_name = self.available_models.get(model_name, model_name)
        self.model_key = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.preprocessor = ThaiTextPreprocessor()        
        self.fallback_models = [
            "cardiffnlp/twitter-roberta-base-sentiment-latest",  # Public Twitter sentiment model
            "nlptown/bert-base-multilingual-uncased-sentiment",  # Public multilingual sentiment
            "distilbert-base-uncased-finetuned-sst-2-english",  # Known working English model
        ]
    
    def initialize(self):
        """เริ่มต้น transformer model พร้อม fallback"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers library is required")
        
        success = False
        models_to_try = [self.model_name] + self.fallback_models
        
        for model_path in models_to_try:
            try:
                print(f"[INFO] กำลังโหลด {model_path}...")
                
                # โหลด tokenizer และ model
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True,
                    use_fast=False  # สำหรับภาษาไทย
                )
                
                # ลองโหลด sentiment classification model
                try:
                    self.model = AutoModelForSequenceClassification.from_pretrained(
                        model_path,
                        num_labels=3,  # negative, neutral, positive
                        trust_remote_code=True
                    )
                    
                    # สร้าง pipeline สำหรับ sentiment analysis
                    self.pipeline = pipeline(
                        "sentiment-analysis",
                        model=self.model,
                        tokenizer=self.tokenizer,
                        return_all_scores=True,
                        device=-1  # ใช้ CPU (เปลี่ยนเป็น 0 สำหรับ GPU)
                    )
                    
                except Exception:
                    # ถ้าไม่มี classification head ให้ใช้เป็น feature extractor + custom classifier
                    from transformers import AutoModel
                    self.model = AutoModel.from_pretrained(
                        model_path,
                        trust_remote_code=True
                    )
                    
                    # สร้าง custom pipeline
                    self.pipeline = self._create_custom_pipeline()
                
                print(f"[INFO] โหลด {model_path} สำเร็จ")
                self.model_name = model_path
                success = True
                break
                
            except Exception as e:
                print(f"[WARNING] ไม่สามารถโหลด {model_path}: {e}")
                continue
        
        if not success:
            print("[ERROR] ไม่สามารถโหลด Transformer model ใดๆ ได้")
            # ใช้ basic sentiment pipeline แทน
            try:
                self.pipeline = pipeline("sentiment-analysis", return_all_scores=True)
                print("[INFO] ใช้ basic sentiment pipeline")
                success = True
            except Exception as e:
                raise Exception(f"ไม่สามารถเริ่มต้น transformer model ได้: {e}")
    
    def _create_custom_pipeline(self):
        """สร้าง custom pipeline สำหรับโมเดลที่ไม่มี classification head"""
        import torch
        import torch.nn.functional as F
        
        class CustomSentimentPipeline:
            def __init__(self, model, tokenizer):
                self.model = model
                self.tokenizer = tokenizer
                self.device = torch.device('cpu')
                
                # Simple classification layer
                self.classifier = torch.nn.Linear(
                    self.model.config.hidden_size, 3
                ).to(self.device)
                
                # Initialize weights
                torch.nn.init.xavier_uniform_(self.classifier.weight)
            
            def __call__(self, text):
                inputs = self.tokenizer(
                    text, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=512,
                    padding=True
                ).to(self.device)
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # ใช้ [CLS] token หรือ pooled output
                    if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                        features = outputs.pooler_output
                    else:
                        features = outputs.last_hidden_state[:, 0, :]  # [CLS] token
                    
                    # ทำนาย sentiment
                    logits = self.classifier(features)
                    probs = F.softmax(logits, dim=-1)
                    
                    # แปลงเป็น format ที่ต้องการ
                    labels = ['NEGATIVE', 'NEUTRAL', 'POSITIVE']
                    results = []
                    for i, (label, prob) in enumerate(zip(labels, probs[0])):
                        results.append({
                            'label': label,
                            'score': float(prob)
                        })
                    
                    return results
        
        return CustomSentimentPipeline(self.model, self.tokenizer)
    
    def predict_sentiment(self, text: str) -> Dict[str, Any]:
        """ทำนาย sentiment ด้วย transformer"""
        if self.pipeline is None:
            self.initialize()
        
        # ประมวลผลข้อความ
        processed_text = self.preprocessor.clean_text(text)
        
        try:
            # ทำนาย
            results = self.pipeline(processed_text)
            
            # แปลงผลลัพธ์
            if isinstance(results[0], list):
                results = results[0]  # unwrap if nested
            
            # หา sentiment ที่มี confidence สูงสุด
            best_result = max(results, key=lambda x: x['score'])
            sentiment = best_result['label'].lower()
            confidence = best_result['score']
            
            # แปลง label ให้เป็นมาตรฐาน
            label_mapping = {
                'negative': 'negative', 'neg': 'negative', 'label_0': 'negative',
                'neutral': 'neutral', 'neu': 'neutral', 'label_1': 'neutral', 
                'positive': 'positive', 'pos': 'positive', 'label_2': 'positive'
            }
            sentiment = label_mapping.get(sentiment, 'neutral')
            
            # คำนวณ sentiment score
            sentiment_score = 0.0
            for result in results:
                label = label_mapping.get(result['label'].lower(), 'neutral')
                if label == 'positive':
                    sentiment_score += result['score']
                elif label == 'negative':
                    sentiment_score -= result['score']
            
            # สร้าง probabilities dict
            probabilities = {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
            for result in results:
                label = label_mapping.get(result['label'].lower(), 'neutral')
                probabilities[label] = result['score']
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'sentiment_score': sentiment_score,
                'probabilities': probabilities,
                'model_type': 'transformer'
            }
            
        except Exception as e:
            print(f"[ERROR] Transformer prediction failed: {e}")
            # Fallback to neutral
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'sentiment_score': 0.0,
                'probabilities': {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33},
                'model_type': 'transformer_fallback'
            }

class EnsembleSentimentModel:
    """รวม multiple models เพื่อความแม่นยำสูงสุด"""
    def __init__(self):
        self.models = {}
        self.weights = {}
        
    def add_model(self, name: str, model, weight: float = 1.0):
        """เพิ่ม model เข้า ensemble"""
        self.models[name] = model
        self.weights[name] = weight
        safe_print(f"[INFO] เพิ่ม {name} model เข้า ensemble (weight: {weight})")
    
    def predict_sentiment(self, text: str) -> Dict[str, Any]:
        """ทำนาย sentiment ด้วย ensemble"""
        if not self.models:
            raise ValueError("ไม่มี model ใน ensemble")
        
        predictions = {}
        total_weight = 0
        weighted_scores = {'positive': 0, 'neutral': 0, 'negative': 0}
        weighted_sentiment_score = 0
        
        # รวบรวมผลจากทุก model
        for name, model in self.models.items():
            try:
                result = model.predict_sentiment(text)
                predictions[name] = result
                
                weight = self.weights[name]
                total_weight += weight
                
                # รวม probabilities แบบถ่วงน้ำหนัก
                for sentiment, prob in result['probabilities'].items():
                    weighted_scores[sentiment] += prob * weight
                
                # รวม sentiment score
                weighted_sentiment_score += result['sentiment_score'] * weight
                
            except Exception as e:
                safe_print(f"[WARNING] {name} model failed: {e}")
                continue
        
        if total_weight == 0:
            raise ValueError("ไม่มี model ที่ทำงานได้")
        
        # normalize weights
        for sentiment in weighted_scores:
            weighted_scores[sentiment] /= total_weight
        weighted_sentiment_score /= total_weight
        
        # หา final sentiment
        final_sentiment = max(weighted_scores, key=weighted_scores.get)
        final_confidence = weighted_scores[final_sentiment]
        
        return {
            'sentiment': final_sentiment,
            'confidence': final_confidence,
            'sentiment_score': weighted_sentiment_score,
            'probabilities': weighted_scores,
            'model_type': 'ensemble',
            'individual_predictions': predictions
        }

def create_ml_enhanced_sentiment_analyzer(training_data: Optional[List[Dict[str, Any]]] = None) -> EnsembleSentimentModel:
    """สร้าง ML-enhanced sentiment analyzer ด้วยโมเดล HF ที่ดีที่สุด"""
    
    print("🚀 กำลังสร้าง Advanced Thai Sentiment Analyzer...")
    print("📱 รองรับ: Social Media, การเมือง, ความคิดเห็นทั่วไป")
    
    # เลือกวิธีการสร้าง ensemble
    use_multi_hf_models = True  # เปลี่ยนเป็น False หากต้องการใช้วิธีเดิม
    
    if use_multi_hf_models:
        print("🤖 ใช้ Multi-Model Hugging Face Ensemble")
        ensemble = create_multi_model_ensemble()
    else:
        print("🔧 ใช้ Traditional + Single HF Model")
        ensemble = EnsembleSentimentModel()
        
        # 1. Traditional ML Model (ถ้ามีข้อมูลฝึกสอน)
        if training_data and len(training_data) >= 20 and SKLEARN_AVAILABLE:
            print("[INFO] สร้าง Traditional ML model...")
            try:
                ml_model = ThaiSentimentMLModel(model_type="logistic")
                ml_results = ml_model.train(training_data)
                
                if ml_results['test_accuracy'] > 0.6:
                    ensemble.add_model("traditional_ml", ml_model, weight=0.3)
                else:
                    print("[WARNING] Traditional ML accuracy ต่ำ, ข้าม model นี้")
                    
            except Exception as e:
                print(f"[WARNING] Traditional ML model failed: {e}")
        
        # 2. Best Thai Transformer Model
        if TRANSFORMERS_AVAILABLE:
            print("[INFO] โหลดโมเดลไทยที่ดีที่สุดจาก Hugging Face...")
            try:
                # ใช้โมเดลที่แนะนำสำหรับ sentiment analysis
                transformer_model = ThaiTransformerModel("wisesight-sentiment")
                transformer_model.initialize()
                ensemble.add_model("hf_thai_sentiment", transformer_model, weight=0.5)
            except Exception as e:
                print(f"[WARNING] Thai HF model failed: {e}")
                
                # Fallback ไปโมเดลอื่น
                try:
                    transformer_model = ThaiTransformerModel("xlm-roberta-sentiment")
                    transformer_model.initialize() 
                    ensemble.add_model("hf_multilingual", transformer_model, weight=0.4)
                except Exception as e2:
                    print(f"[WARNING] Fallback HF model failed: {e2}")
        
        # 3. Enhanced Rule-based (จาก original code)
        print("[INFO] เพิ่ม Enhanced Rule-based model...")
        class RuleBasedModel:
            def predict_sentiment(self, text):
                from social_media_utils import advanced_thai_sentiment_analysis
                result = advanced_thai_sentiment_analysis(text)
                
                emotion_to_sentiment = {
                    'joy': 'positive', 'excited': 'positive',
                    'anger': 'negative', 'sadness': 'negative', 'fear': 'negative',
                    'neutral': 'neutral'
                }
                
                sentiment = emotion_to_sentiment.get(result['emotion'], 'neutral')
                confidence = 0.7 if result['intensity'] == 'high' else 0.5
                
                if sentiment == 'positive':
                    probs = {'positive': 0.7, 'neutral': 0.2, 'negative': 0.1}
                elif sentiment == 'negative':
                    probs = {'positive': 0.1, 'neutral': 0.2, 'negative': 0.7}
                else:
                    probs = {'positive': 0.25, 'neutral': 0.5, 'negative': 0.25}
                
                return {
                    'sentiment': sentiment,
                    'confidence': confidence,
                    'sentiment_score': result['sentiment_score'],
                    'probabilities': probs,
                    'model_type': 'rule_based'
                }
        
        rule_model = RuleBasedModel()
        weight = 0.2 if ensemble.models else 1.0
        ensemble.add_model("rule_based", rule_model, weight=weight)
    
    print(f"✅ Ensemble Sentiment Analyzer พร้อมใช้งาน ({len(ensemble.models)} models)")
    print("🎯 รองรับ: การวิเคราะห์อารมณ์ขั้นสูง, บริบทการเมือง, Auto Review")
    
    return ensemble

# --- Auto Review และ Quality Control ---

class SentimentQualityReviewer:
    """ระบบตรวจสอบและปรับปรุงคุณภาพ sentiment analysis อัตโนมัติ"""
    
    def __init__(self, confidence_threshold: float = 0.7, review_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.review_threshold = review_threshold
        
        # คำศัพท์สำหรับตรวจสอบบริบทการเมือง
        self.political_keywords = {
            'negative': [
                'โง่', 'หลอก', 'ทุจริต', 'ฉ้อโกง', 'ด่า', 'ตำหนิ', 'วิจารณ์', 'แย่', 'ผิด',
                'ลาออก', 'ไล่ออก', 'ยุบ', 'โกหก', 'หลอกลวง', 'คอรัปชั่น', 'ใช้ไม่ได้',
                'ปัญหา', 'ล้มเหลว', 'พัง', 'เสีย', 'ห่วย', 'แน่นอน', 'โกรธ', 'ฉิบหาย'
            ],
            'positive': [
                'ดี', 'เก่ง', 'ยอดเยี่ยม', 'สุดยอด', 'ชอบ', 'สนับสนุน', 'เห็นด้วย', 
                'ถูกต้อง', 'ชื่นชม', 'ประทับใจ', 'ดีใจ', 'ภูมิใจ', 'หวัง', 'เชิดชู'
            ],
            'criticism_words': [
                'ไม่เอา', 'อย่า', 'หยุด', 'เลิก', 'ปฏิเสธ', 'คัดค้าน', 'ไม่เห็นด้วย',
                'ผิดพลาด', 'ไม่ถูก', 'ไม่ควร', 'ไม่ดี', 'ไม่ใช่', 'ตำหนิ'
            ]
        }
        
        # รูปแบบการแสดงอารมณ์
        self.emotion_patterns = {
            'strong_negative': [
                r'[!]{2,}', r'[?]{2,}', r'หา{2,}ย', r'แย่{2,}', r'โง่{2,}',
                r'ฉิบ+หาย', r'ห่วย+', r'เฮ้ย+', r'เชี่ย+'
            ],
            'strong_positive': [
                r'ดี{2,}', r'เก่ง{2,}', r'สุดยอด+', r'ยอดเยี่ยม+', r'วาว+', r'เยี่ยม+'
            ],
            'sarcasm': [
                r'เก่งจัง', r'ดีจัง', r'เก่งมาก', r'ดีมาก.*ไม่', r'ถูกต้องแล้ว.*ไม่',
                r'ใช่.*ไม่', r'งั้นหรอ', r'จริงๆ.*เหรอ', r'อืม.*ใช่'
            ]
        }

    def analyze_political_context(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์บริบทการเมืองในข้อความ"""
        text_lower = text.lower()
        
        # นับคำศัพท์ negative/positive
        neg_count = sum(1 for word in self.political_keywords['negative'] if word in text_lower)
        pos_count = sum(1 for word in self.political_keywords['positive'] if word in text_lower)
        crit_count = sum(1 for word in self.political_keywords['criticism_words'] if word in text_lower)
        
        # ตรวจหาการวิพากษ์วิจารณ์
        is_criticism = crit_count > 0 or neg_count > pos_count
        
        # ตรวจหาการเสียดสี/ประชด
        sarcasm_detected = any(re.search(pattern, text_lower) for pattern in self.emotion_patterns['sarcasm'])
        
        # ตรวจหาอารมณ์รุนแรง
        strong_emotion = any(re.search(pattern, text_lower) for pattern in 
                           self.emotion_patterns['strong_negative'] + self.emotion_patterns['strong_positive'])
        
        return {
            'is_political': neg_count + pos_count + crit_count > 0,
            'neg_word_count': neg_count,
            'pos_word_count': pos_count,
            'criticism_count': crit_count,
            'is_criticism': is_criticism,
            'sarcasm_detected': sarcasm_detected,
            'strong_emotion': strong_emotion,
            'adjusted_sentiment': self._calculate_adjusted_sentiment(neg_count, pos_count, crit_count, sarcasm_detected)
        }

    def _calculate_adjusted_sentiment(self, neg_count: int, pos_count: int, crit_count: int, sarcasm: bool) -> str:
        """คำนวณ sentiment ที่ปรับแล้วตามบริบท"""
        total_negative = neg_count + crit_count
        
        if sarcasm:
            return 'negative'  # การเสียดสีมักเป็น negative
        
        if total_negative > pos_count * 2:  # ถ่วงน้ำหนัก negative มากกว่า
            return 'negative'
        elif pos_count > total_negative:
            return 'positive'
        else:
            return 'neutral'

    def review_prediction(self, text: str, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """ตรวจสอบและปรับแก้ prediction"""
        
        # วิเคราะห์บริบทการเมือง
        political_analysis = self.analyze_political_context(text)
        
        original_sentiment = prediction['sentiment']
        original_confidence = prediction['confidence']
        
        # สร้าง review result
        review_result = prediction.copy()
        review_result.update({
            'original_sentiment': original_sentiment,
            'original_confidence': original_confidence,
            'political_context': political_analysis,
            'review_applied': False,
            'review_reason': '',
            'confidence_adjusted': False
        })
        
        # กฎการปรับแก้
        adjustments_made = []
        
        # 1. ตรวจสอบ confidence ต่ำ
        if original_confidence < self.review_threshold:
            # ใช้ political context ช่วยตัดสินใจ
            if political_analysis['is_political']:
                adjusted_sentiment = political_analysis['adjusted_sentiment']
                if adjusted_sentiment != original_sentiment:
                    review_result['sentiment'] = adjusted_sentiment
                    review_result['confidence'] = min(0.75, original_confidence + 0.2)
                    adjustments_made.append(f"political_context_override: {original_sentiment} -> {adjusted_sentiment}")
        
        # 2. ตรวจสอบการเสียดสี/ประชด
        if political_analysis['sarcasm_detected'] and original_sentiment != 'negative':
            review_result['sentiment'] = 'negative'
            review_result['confidence'] = max(0.7, original_confidence)
            adjustments_made.append("sarcasm_detected: forced negative")
        
        # 3. ตรวจสอบคำวิจารณ์รุนแรง
        if (political_analysis['neg_word_count'] >= 2 and 
            original_sentiment == 'neutral'):
            review_result['sentiment'] = 'negative'
            review_result['confidence'] = max(0.65, original_confidence)
            adjustments_made.append("strong_criticism: neutral -> negative")
        
        # 4. ปรับ confidence สำหรับกรณีที่มีความมั่นใจต่ำแต่มี context ชัด
        if (original_confidence < 0.6 and 
            (political_analysis['strong_emotion'] or political_analysis['criticism_count'] > 0)):
            review_result['confidence'] = min(0.8, original_confidence + 0.15)
            review_result['confidence_adjusted'] = True
            adjustments_made.append("confidence_boost: strong_emotion/criticism detected")
        
        # 5. ตรวจสอบความขัดแย้งระหว่าง sentiment และ context
        if (original_sentiment == 'positive' and 
            political_analysis['neg_word_count'] > political_analysis['pos_word_count']):
            review_result['sentiment'] = 'negative'
            adjustments_made.append("contradiction_fix: positive with negative words -> negative")
        
        # บันทึกการปรับแก้
        if adjustments_made:
            review_result['review_applied'] = True
            review_result['review_reason'] = '; '.join(adjustments_made)
            
            # ปรับ probabilities ใหม่
            if review_result['sentiment'] == 'negative':
                review_result['probabilities'] = {'negative': 0.7, 'neutral': 0.2, 'positive': 0.1}
                review_result['sentiment_score'] = -0.6
            elif review_result['sentiment'] == 'positive':
                review_result['probabilities'] = {'positive': 0.7, 'neutral': 0.2, 'negative': 0.1}
                review_result['sentiment_score'] = 0.6
            else:
                review_result['probabilities'] = {'neutral': 0.6, 'positive': 0.2, 'negative': 0.2}
                review_result['sentiment_score'] = 0.0
        
        return review_result

    def batch_review(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ตรวจสอบ predictions แบบ batch"""
        reviewed_predictions = []
        
        stats = {
            'total': len(predictions),
            'reviewed': 0,
            'sentiment_changed': 0,
            'confidence_adjusted': 0,
            'low_confidence_count': 0
        }
        
        for pred in predictions:
            text = pred.get('text', '')
            
            # Count low confidence
            if pred.get('ml_confidence', 1.0) < self.review_threshold:
                stats['low_confidence_count'] += 1
            
            # Review prediction
            reviewed = self.review_prediction(text, {
                'sentiment': pred.get('sentiment', 'neutral'),
                'confidence': pred.get('ml_confidence', 0.5),
                'sentiment_score': pred.get('sentiment_score', 0.0),
                'probabilities': pred.get('ml_probabilities', {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33})
            })
            
            # Update original prediction with review results
            pred.update(reviewed)
            
            # Count changes
            if reviewed['review_applied']:
                stats['reviewed'] += 1
                if reviewed['sentiment'] != reviewed['original_sentiment']:
                    stats['sentiment_changed'] += 1
                if reviewed['confidence_adjusted']:
                    stats['confidence_adjusted'] += 1
            
            reviewed_predictions.append(pred)
          # Print review statistics
        safe_print(f"\n📊 Auto Review Statistics:")
        safe_print(f"  Total predictions: {stats['total']}")
        safe_print(f"  Low confidence (< {self.review_threshold}): {stats['low_confidence_count']}")
        safe_print(f"  Predictions reviewed: {stats['reviewed']}")
        safe_print(f"  Sentiment changed: {stats['sentiment_changed']}")
        safe_print(f"  Confidence adjusted: {stats['confidence_adjusted']}")
        
        return reviewed_predictions

class AdvancedThaiSentimentAnalyzer:
    """ระบบ sentiment analysis ขั้นสูงสำหรับภาษาไทยที่มี auto review"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.ensemble_model = None
        self.reviewer = SentimentQualityReviewer(confidence_threshold=confidence_threshold)
        self.training_data = []
        
    def initialize(self, training_data: Optional[List[Dict[str, Any]]] = None):
        """เริ่มต้นระบบ"""
        safe_print("🚀 กำลังเริ่มต้น Advanced Thai Sentiment Analyzer...")
        
        if training_data:
            self.training_data = training_data
            safe_print(f"📚 โหลดข้อมูลฝึกสอน: {len(training_data)} รายการ")
        
        # สร้าง ensemble model
        self.ensemble_model = create_ml_enhanced_sentiment_analyzer(training_data)
        safe_print("✅ ระบบพร้อมใช้งาน")
    
    def analyze_with_review(self, text: str) -> Dict[str, Any]:
        """วิเคราะห์ sentiment พร้อม auto review"""
        if not self.ensemble_model:
            raise ValueError("ระบบยังไม่ได้เริ่มต้น กรุณาเรียก initialize() ก่อน")
        
        # ทำนาย sentiment
        prediction = self.ensemble_model.predict_sentiment(text)
        
        # Auto review
        reviewed_prediction = self.reviewer.review_prediction(text, prediction)
        
        # เพิ่มข้อมูลเสริม
        reviewed_prediction.update({
            'text': text,
            'analysis_timestamp': datetime.now().isoformat(),
            'analyzer_version': 'advanced_v2.0'
        })
        
        return reviewed_prediction
    def batch_analyze_with_review(self, texts: List[str]) -> List[Dict[str, Any]]:
        """วิเคราะห์ batch พร้อม auto review"""
        safe_print(f"🔄 กำลังวิเคราะห์ {len(texts)} ข้อความ...")
        
        # วิเคราะห์แต่ละข้อความ
        predictions = []
        for i, text in enumerate(texts):
            if i % 50 == 0 and i > 0:
                safe_print(f"   ดำเนินการแล้ว: {i}/{len(texts)}")
            
            try:
                result = self.analyze_with_review(text)
                predictions.append(result)
            except Exception as e:
                safe_print(f"[WARNING] ข้อความที่ {i+1} ไม่สามารถวิเคราะห์ได้: {e}")
                continue
        
        safe_print(f"✅ วิเคราะห์เสร็จสิ้น: {len(predictions)} รายการ")
        return predictions
    def update_training_data(self, new_data: List[Dict[str, Any]]):
        """อัปเดตข้อมูลฝึกสอนและปรับปรุงโมเดล"""
        self.training_data.extend(new_data)
        safe_print(f"📈 อัปเดตข้อมูลฝึกสอน: +{len(new_data)} รายการ (รวม: {len(self.training_data)})")
        
        # ฝึกโมเดลใหม่ถ้ามีข้อมูลเพียงพอ
        if len(self.training_data) >= 50:
            safe_print("🔄 กำลังฝึกโมเดลใหม่...")
            self.ensemble_model = create_ml_enhanced_sentiment_analyzer(self.training_data)
            safe_print("✅ อัปเดตโมเดลเสร็จสิ้น")

# Example usage and testing
def test_ml_sentiment_analysis():
    """ทดสอบ ML sentiment analysis"""
    
    # สร้างข้อมูลทดสอบ
    test_texts = [
        "สุดยอดมากเลย ชอบมาก",  # positive
        "แย่มาก ไม่ชอบเลย",      # negative  
        "โอเค ปกติดี",           # neutral
        "ล่มทั้งวัน ใช้ไม่ได้เลย", # negative
        "ดีใจมากค่ะ ขอบคุณ"       # positive
    ]
    
    safe_print("=== ทดสอบ ML Sentiment Analysis ===")
    
    # สร้าง ensemble model
    ensemble = create_ml_enhanced_sentiment_analyzer()
    
    # ทดสอบแต่ละข้อความ
    for i, text in enumerate(test_texts):
        safe_print(f"\n{i+1}. \"{text}\"")
        try:
            result = ensemble.predict_sentiment(text)
            safe_print(f"   Sentiment: {result['sentiment']}")
            safe_print(f"   Confidence: {result['confidence']:.3f}")
            safe_print(f"   Score: {result['sentiment_score']:.3f}")
            safe_print(f"   Models: {len(result.get('individual_predictions', {}))}")
        except Exception as e:
            safe_print(f"   Error: {e}")

if __name__ == "__main__":
    test_ml_sentiment_analysis()

def get_best_thai_sentiment_model():
    """เลือกโมเดลไทยที่ดีที่สุดสำหรับ sentiment analysis"""
    
    # รายการโมเดลไทยเรียงตามลำดับความแนะนำ
    recommended_models = [
        {
            'name': 'wisesight-sentiment',
            'path': 'pythainlp/wangchanberta-base-att-spm-uncased-wisesight-sentiment',
            'description': 'WangchanBERTa fine-tuned บน Wisesight dataset',
            'strengths': ['ไทย', 'social media', 'sentiment'],
            'size': 'base'
        },
        {
            'name': 'thai-sentiment',
            'path': 'airesearch/wangchanberta-base-att-spm-uncased-thai-sentiment',
            'description': 'WangchanBERTa สำหรับ sentiment analysis ทั่วไป',
            'strengths': ['ไทย', 'general sentiment'],
            'size': 'base'
        },
        {
            'name': 'phayathai-sentiment',
            'path': 'clicknext/phayathai_sentiment',
            'description': 'PhayaThaiBERT สำหรับ sentiment classification',
            'strengths': ['ไทย', 'sentiment', 'classification'],
            'size': 'base'
        },
        {
            'name': 'wangchanberta-base',
            'path': 'airesearch/wangchanberta-base-att-spm-uncased',
            'description': 'WangchanBERTa โมเดลพื้นฐาน (ต้อง fine-tune)',
            'strengths': ['ไทย', 'general purpose'],
            'size': 'base'
        },
        {
            'name': 'xlm-roberta-sentiment',
            'path': 'cardiffnlp/twitter-xlm-roberta-base-sentiment',
            'description': 'XLM-RoBERTa สำหรับ Twitter sentiment (รองรับไทย)',
            'strengths': ['multilingual', 'twitter', 'sentiment'],
            'size': 'base'
        }
    ]
    
    return recommended_models

def create_multi_model_ensemble():
    """สร้าง ensemble จากหลายโมเดล HF ที่ดี"""
    ensemble = EnsembleSentimentModel()
    
    # รายการโมเดลที่จะรวมใน ensemble
    models_to_try = [
        ('wisesight', 'wisesight-sentiment', 0.4),  # น้ำหนักสูงสุด - เหมาะกับ social media
        ('phayathai', 'phayathai-sentiment', 0.3),  # โมเดลไทยเฉพาะ
        ('xlm-roberta', 'xlm-roberta-sentiment', 0.2),  # multilingual backup
        ('wangchanberta', 'wangchanberta-base', 0.1)  # โมเดลพื้นฐาน
    ]
    
    print("🤖 กำลังสร้าง Multi-Model Ensemble จาก Hugging Face...")
    
    successful_models = 0
    for model_name, model_key, weight in models_to_try:
        try:
            print(f"[INFO] กำลังโหลด {model_name}...")
            transformer_model = ThaiTransformerModel(model_key)
            transformer_model.initialize()
            ensemble.add_model(model_name, transformer_model, weight=weight)
            successful_models += 1
            print(f"✅ {model_name} โหลดสำเร็จ (weight: {weight})")
        except Exception as e:
            print(f"❌ {model_name} โหลดไม่สำเร็จ: {e}")
            continue
    
    if successful_models == 0:
        print("⚠️ ไม่สามารถโหลดโมเดล HF ได้ จะใช้ rule-based แทน")
        # Fallback to rule-based
        class RuleBasedModel:
            def predict_sentiment(self, text):
                from social_media_utils import advanced_thai_sentiment_analysis
                result = advanced_thai_sentiment_analysis(text)
                
                emotion_to_sentiment = {
                    'joy': 'positive', 'excited': 'positive',
                    'anger': 'negative', 'sadness': 'negative', 'fear': 'negative',
                    'neutral': 'neutral'
                }
                
                sentiment = emotion_to_sentiment.get(result['emotion'], 'neutral')
                confidence = 0.7 if result['intensity'] == 'high' else 0.5
                
                if sentiment == 'positive':
                    probs = {'positive': 0.7, 'neutral': 0.2, 'negative': 0.1}
                elif sentiment == 'negative':
                    probs = {'positive': 0.1, 'neutral': 0.2, 'negative': 0.7}
                else:
                    probs = {'positive': 0.25, 'neutral': 0.5, 'negative': 0.25}
                
                return {
                    'sentiment': sentiment,
                    'confidence': confidence,
                    'sentiment_score': result['sentiment_score'],
                    'probabilities': probs,
                    'model_type': 'rule_based_fallback'
                }
        
        ensemble.add_model("rule_based_fallback", RuleBasedModel(), weight=1.0)
    
    print(f"🎯 Ensemble พร้อมใช้งาน: {len(ensemble.models)} models")
    return ensemble

def test_huggingface_models():
    """ทดสอบและเปรียบเทียบโมเดล Hugging Face ต่างๆ"""
    
    test_texts = [
        # Thai political comments (from our dataset)
        "นายกโง่ไม่ทันเหลี่ยมของฮุนเซน ทุกเรื่องที่ทำมาเป็นคนอื่นคิดไม่ใช้นายก",  # negative
        "ถูกต้องค่ะทหารสามารถเข้าจับกลุ่มได้ทันทีเลยค่ะ",  # neutral/positive
        "อย่าเอาทหารมายุ่งดีละไม่เข็ดเหรอที่ผ่านมาใช้สภาเถอะ",  # negative/sarcasm
        
        # General sentiment
        "สุดยอดมากเลย ชอบมาก",  # positive
        "แย่มาก ไม่ชอบเลย",      # negative  
        "โอเค ปกติดี",           # neutral
        
        # Social media style
        "ว้าวววว เก่งมากจริงๆ 555",  # positive
        "เฮ้ย!! มันทำอะไรเนี่ย",     # negative
        "อืมม... ก็ได้นะ",          # neutral
    ]
    
    print("🧪 กำลังทดสอบโมเดล Hugging Face ต่างๆ...")
    print("=" * 80)
    
    # รายการโมเดลที่จะทดสอบ
    models_to_test = [
        ("wisesight-sentiment", "WangchanBERTa + Wisesight"),
        ("phayathai-sentiment", "PhayaThaiBERT Sentiment"),
        ("xlm-roberta-sentiment", "XLM-RoBERTa Multilingual"),
        ("wangchanberta-base", "WangchanBERTa Base"),
    ]
    
    results = {}
    
    for model_key, model_desc in models_to_test:
        print(f"\n🤖 ทดสอบ: {model_desc}")
        print("-" * 50)
        
        try:
            # สร้างและทดสอบโมเดล
            model = ThaiTransformerModel(model_key)
            model.initialize()
            
            model_results = []
            for i, text in enumerate(test_texts):
                try:
                    result = model.predict_sentiment(text)
                    model_results.append(result)
                    
                    print(f"{i+1:2d}. \"{text[:50]}...\"")
                    print(f"    → {result['sentiment']} ({result['confidence']:.3f})")
                    
                except Exception as e:
                    print(f"{i+1:2d}. Error: {e}")
                    model_results.append(None)
            
            results[model_key] = {
                'description': model_desc,
                'results': model_results,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ ไม่สามารถโหลด {model_desc}: {e}")
            results[model_key] = {
                'description': model_desc,
                'results': None,
                'success': False,
                'error': str(e)
            }
    
    # สรุปผลการทดสอบ
    print("\n" + "=" * 80)
    print("📊 สรุปผลการทดสอบ:")
    
    successful_models = [k for k, v in results.items() if v['success']]
    failed_models = [k for k, v in results.items() if not v['success']]
    
    print(f"✅ โมเดลที่ใช้งานได้: {len(successful_models)}/{len(models_to_test)}")
    for model in successful_models:
        print(f"   - {results[model]['description']}")
    
    if failed_models:
        print(f"❌ โมเดลที่ใช้ไม่ได้: {len(failed_models)}")
        for model in failed_models:
            print(f"   - {results[model]['description']}: {results[model]['error']}")
    
    # แนะนำโมเดลที่ดีที่สุด
    if successful_models:
        print(f"\n💡 แนะนำ: ใช้ {results[successful_models[0]]['description']} เป็นหลัก")
        if len(successful_models) > 1:
            print(f"🔄 Ensemble: รวมกับ {results[successful_models[1]]['description']} เพื่อความแม่นยำสูงขึ้น")
    
    return results

def benchmark_sentiment_models():
    """เปรียบเทียบประสิทธิภาพโมเดลต่างๆ"""
    
    print("⚡ กำลัง Benchmark โมเดล Sentiment Analysis...")
    
    # ข้อมูลทดสอบที่มี ground truth
    test_cases = [
        {"text": "สุดยอดมากเลย ชอบมาก", "expected": "positive"},
        {"text": "แย่มาก ไม่ชอบเลย", "expected": "negative"},
        {"text": "โอเค ปกติดี", "expected": "neutral"},
        {"text": "โง่จริงๆ ห่วยแตก", "expected": "negative"},
        {"text": "ดีใจมากค่ะ ขอบคุณ", "expected": "positive"},
        {"text": "ไม่รู้เหมือนกัน", "expected": "neutral"},
        {"text": "เก่งมากจริงๆ เลิฟ", "expected": "positive"},
        {"text": "ปัญหาเยอะมาก ใช้ไม่ได้", "expected": "negative"},
        # การเมือง
        {"text": "นายกเก่งมาก สนับสนุน", "expected": "positive"},
        {"text": "ลาออกไปเลย ไม่ไหว", "expected": "negative"},
    ]
    
    # ทดสอบ ensemble model
    try:
        print("🎯 ทดสอบ Advanced Ensemble Model...")
        ensemble = create_ml_enhanced_sentiment_analyzer()
        
        correct = 0
        total = len(test_cases)
        
        for case in test_cases:
            result = ensemble.predict_sentiment(case['text'])
            predicted = result['sentiment']
            expected = case['expected']
            
            is_correct = predicted == expected
            if is_correct:
                correct += 1
            
            print(f"✓" if is_correct else "✗", end=" ")
            print(f"\"{case['text'][:40]}...\" → {predicted} (expected: {expected})")
        
        accuracy = correct / total * 100
        print(f"\n📈 Accuracy: {accuracy:.1f}% ({correct}/{total})")
        
        if accuracy >= 80:
            print("🎉 ประสิทธิภาพดีเยี่ยม!")
        elif accuracy >= 60:
            print("👍 ประสิทธิภาพดี")
        else:
            print("⚠️ ควรปรับปรุงโมเดล")
            
    except Exception as e:
        print(f"❌ ไม่สามารถทดสอบ ensemble ได้: {e}")
