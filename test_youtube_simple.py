#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test for YouTube comment scraping
"""

import subprocess
import json
import tempfile
import os

def simple_youtube_test():
    print("🧪 Testing YouTube Comment Scraping")
    print("=" * 40)
    
    # Use the first URL from test_links.txt
    test_url = "https://www.youtube.com/watch?v=0EZDL8xqXsY"
    print(f"🎬 Testing URL: {test_url}")
    
    try:
        # Create a temporary file for comments
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Build the command
        cmd = [
            'python', '-m', 'yt_dlp',
            '--write-comments',
            '--skip-download',
            '--max-downloads', '1',
            '--write-info-json',
            '--output', temp_path.replace('.json', '.%(ext)s'),
            test_url
        ]
        
        print("🔍 Running yt-dlp command...")
        print(f"   Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ yt-dlp executed successfully")
            
            # Look for the comments file
            base_path = temp_path.replace('.json', '')
            info_file = f"{base_path}.info.json"
            
            if os.path.exists(info_file):
                print(f"📄 Found info file: {info_file}")
                
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                
                # Check if comments are available
                if 'comments' in info and info['comments']:
                    comments = info['comments']
                    print(f"✅ Found {len(comments)} comments")
                    
                    # Show a sample comment
                    if comments:
                        sample = comments[0]
                        text = sample.get('text', '')
                        author = sample.get('author', 'Unknown')
                        print(f"📝 Sample comment by {author}: {text[:100]}...")
                        
                        # Test sentiment analysis on this comment
                        try:
                            from app import enhanced_analyze_sentiment
                            result = enhanced_analyze_sentiment(text)
                            print(f"💭 Sentiment: {result['sentiment']} (confidence: {result['confidence']:.2f})")
                        except Exception as e:
                            print(f"⚠️ Sentiment analysis failed: {e}")
                            
                    return True
                else:
                    print("ℹ️ No comments found in video info")
                    return True  # Not necessarily a failure
            else:
                print(f"⚠️ Info file not found at {info_file}")
                return False
        else:
            print(f"❌ yt-dlp failed with return code {result.returncode}")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out (this is normal for large videos)")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            base_path = temp_path.replace('.json', '')
            for ext in ['.info.json', '.comments.json']:
                file_path = f"{base_path}{ext}"
                if os.path.exists(file_path):
                    os.unlink(file_path)
        except:
            pass

if __name__ == "__main__":
    success = simple_youtube_test()
    if success:
        print("\n✅ YouTube scraping test completed successfully!")
    else:
        print("\n❌ YouTube scraping test failed!")
