#!/usr/bin/env python3
"""
Debug script for Yuvan's voice system
"""

from yuvan.voice_system import YuvanVoice
import time

def debug_voice_system():
    """Debug the voice system step by step"""
    print("🔍 Debugging Yuvan Voice System")
    print("=" * 50)
    
    try:
        # Initialize voice system
        print("\n1. Initializing voice system...")
        voice = YuvanVoice()
        success = voice.initialize_client()
        
        if not success:
            print("❌ Failed to initialize voice system")
            return False
        
        print("✅ Voice system initialized successfully!")
        
        # Test template application
        print("\n2. Testing template application...")
        try:
            template_result = voice.client.predict(
                template_name=voice.template_name,
                api_name="/apply_template"
            )
            print(f"Template result: {template_result}")
            if template_result and len(template_result) >= 1:
                print(f"System prompt from template: {template_result[0]}")
            else:
                print("❌ No template result")
                return False
        except Exception as e:
            print(f"❌ Error applying template: {e}")
            return False
        
        # Test speech generation
        print("\n3. Testing speech generation...")
        test_text = "Hello! This is a test."
        
        try:
            # Call the generate_speech API directly
            result = voice.client.predict(
                text=test_text,
                voice_preset=voice.voice_preset,
                reference_audio=None,
                reference_text=None,
                max_completion_tokens=voice.max_completion_tokens,
                temperature=voice.temperature,
                top_p=voice.top_p,
                top_k=voice.top_k,
                system_prompt=voice.system_prompt,
                stop_strings={"headers":["stops"],"data":[["<|end_of_text|>"],["<|eot_id|>"]],"metadata":None},
                ras_win_len=voice.ras_win_len,
                ras_win_max_num_repeat=voice.ras_win_max_num_repeat,
                api_name="/generate_speech"
            )
            
            print(f"Speech generation result: {result}")
            print(f"Result type: {type(result)}")
            print(f"Result length: {len(result) if result else 'None'}")
            
            if result and len(result) >= 2:
                audio_file_path = result[1]
                print(f"Audio file path: {audio_file_path}")
                print(f"Audio file exists: {audio_file_path and os.path.exists(audio_file_path)}")
            else:
                print("❌ Unexpected result format")
                
        except Exception as e:
            print(f"❌ Error in speech generation: {e}")
            return False
        
        print("\n✅ Debug completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        return False

if __name__ == "__main__":
    import os
    debug_voice_system() 