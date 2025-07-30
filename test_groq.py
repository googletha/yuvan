#!/usr/bin/env python3
"""
Test script to verify Groq API integration with Yuvan
"""

from yuvan.ai_advisory_agent import AIAdvisoryAgent
import config

def test_groq_integration():
    """Test the Groq API integration"""
    print("Testing Groq API integration...")
    print(f"Using model: {config.GROQ_MODEL}")
    print(f"API Key: {config.GROQ_API_KEY[:10]}...")
    
    try:
        # Create the advisory agent
        agent = AIAdvisoryAgent()
        
        # Test with a simple question
        test_prompt = "Hello! Can you tell me a bit about yourself?"
        print(f"\nSending test prompt: '{test_prompt}'")
        
        response = agent.get_response(test_prompt)
        print(f"\nResponse received:")
        print(f"'{response}'")
        
        if response and len(response) > 10:
            print("\n✅ Groq API integration successful!")
            return True
        else:
            print("\n❌ Groq API integration failed - empty or too short response")
            return False
            
    except Exception as e:
        print(f"\n❌ Groq API integration failed with error: {e}")
        return False

if __name__ == "__main__":
    test_groq_integration() 