#!/usr/bin/env python3
"""
Test script for Yuvan's voice system
"""

from yuvan.voice_system import YuvanVoice, speak_text, stop_voice, cleanup_voice
import time

def test_voice_system():
    """Test the voice system functionality"""
    print("🎤 Testing Yuvan Voice System")
    print("=" * 50)
    
    try:
        # Test 1: Initialize voice system
        print("\n1. Initializing voice system...")
        voice = YuvanVoice()
        success = voice.initialize_client()
        
        if success:
            print("✅ Voice system initialized successfully!")
        else:
            print("❌ Failed to initialize voice system")
            return False
        
        # Test 2: Test text-to-speech
        print("\n2. Testing text-to-speech...")
        test_text = "Hello! I'm Yuvan, your AI assistant. This is a test of my voice system."
        
        print(f"Converting text: '{test_text}'")
        print("This may take a moment as it uses the Higgs Audio v2 model...")
        audio_file = voice.text_to_speech(test_text)
        
        if audio_file:
            print(f"✅ Audio generated: {audio_file}")
        else:
            print("❌ Failed to generate audio")
            return False
        
        # Test 3: Test audio playback
        print("\n3. Testing audio playback...")
        print("Playing audio (this should take a few seconds)...")
        
        voice.play_audio(audio_file)
        print("✅ Audio playback completed!")
        
        # Test 4: Test async speaking
        print("\n4. Testing async speaking...")
        test_text2 = "This is an asynchronous test of my voice system."
        
        print(f"Speaking asynchronously: '{test_text2}'")
        voice.speak_async(test_text2)
        
        # Wait for async speech to complete
        time.sleep(5)
        print("✅ Async speaking completed!")
        
        # Test 5: Test convenience function
        print("\n5. Testing convenience function...")
        test_text3 = "This is a test of the convenience function."
        
        print(f"Using convenience function: '{test_text3}'")
        speak_text(test_text3, async_play=False)
        print("✅ Convenience function test completed!")
        
        print("\n🎉 All voice system tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during voice system test: {e}")
        return False
    
    finally:
        # Cleanup
        print("\nCleaning up voice system...")
        cleanup_voice()
        print("✅ Cleanup completed!")

def test_simple_speak():
    """Simple test for quick verification"""
    print("🎤 Simple Voice Test")
    print("=" * 30)
    
    try:
        test_text = "Hello! This is Yuvan speaking. How can I help you today?"
        print(f"Speaking: '{test_text}'")
        
        speak_text(test_text, async_play=False)
        print("✅ Simple voice test completed!")
        
    except Exception as e:
        print(f"❌ Error in simple voice test: {e}")
    finally:
        cleanup_voice()

if __name__ == "__main__":
    # Run comprehensive test
    print("Running comprehensive voice system test...")
    test_voice_system()
    
    # Run simple test
    print("\n" + "="*50)
    print("Running simple voice test...")
    test_simple_speak() 