#!/usr/bin/env python3
"""
Test script to verify Yuvan's configuration system
"""

import yuvan_config
from yuvan.ai_advisory_agent import AIAdvisoryAgent
from yuvan.task_handler import TaskHandler

def test_configuration():
    """Test the configuration system"""
    print("🧪 Testing Yuvan Configuration System")
    print("=" * 50)
    
    # Test 1: Character Configuration
    print("\n1. Testing Character Configuration:")
    char_config = yuvan_config.get_character_config()
    print(f"   Name: {char_config['name']}")
    print(f"   Accent: {char_config['accent']}")
    print(f"   Personality: {', '.join(char_config['personality_traits'][:3])}...")
    
    # Test 2: Tools Configuration
    print("\n2. Testing Tools Configuration:")
    tools_config = yuvan_config.get_tools_config()
    print(f"   Available tools: {len(tools_config)}")
    for tool_name, tool_config in tools_config.items():
        print(f"   - {tool_name}: {tool_config['name']}")
    
    # Test 3: Response Guidelines
    print("\n3. Testing Response Guidelines:")
    response_guidelines = yuvan_config.get_response_guidelines()
    print(f"   Greeting responses: {len(response_guidelines['greeting_responses'])}")
    print(f"   Personal questions: {len(response_guidelines['personal_questions'])}")
    print(f"   Error responses: {len(response_guidelines['error_responses'])}")
    
    # Test 4: System Prompt
    print("\n4. Testing System Prompt:")
    system_prompt = yuvan_config.get_system_prompt()
    print(f"   System prompt length: {len(system_prompt)} characters")
    print(f"   Contains character name: {'Yuvan' in system_prompt}")
    print(f"   Contains British expressions: {'old chap' in system_prompt}")
    
    # Test 5: AI Advisory Agent
    print("\n5. Testing AI Advisory Agent:")
    try:
        agent = AIAdvisoryAgent()
        char_info = agent.get_character_info()
        print(f"   Agent initialized successfully")
        print(f"   Character name: {char_info['name']}")
        print(f"   Available tools: {len(char_info['available_tools'])}")
    except Exception as e:
        print(f"   Error initializing agent: {e}")
    
    # Test 6: Task Handler
    print("\n6. Testing Task Handler:")
    try:
        handler = TaskHandler()
        print(f"   Task handler initialized successfully")
        print(f"   Response guidelines loaded: {len(handler.response_guidelines) > 0}")
    except Exception as e:
        print(f"   Error initializing task handler: {e}")
    
    # Test 7: Tool Suggestions
    print("\n7. Testing Tool Suggestions:")
    try:
        agent = AIAdvisoryAgent()
        test_inputs = [
            "what's the weather like",
            "search for information",
            "tell me a joke",
            "calculate something"
        ]
        
        for test_input in test_inputs:
            suggestions = agent.get_tool_suggestions(test_input)
            print(f"   '{test_input}': {len(suggestions)} suggestions")
    except Exception as e:
        print(f"   Error testing tool suggestions: {e}")
    
    print("\n✅ Configuration system test completed!")

def test_character_responses():
    """Test character-specific responses"""
    print("\n🎭 Testing Character Responses")
    print("=" * 50)
    
    try:
        handler = TaskHandler()
        
        test_questions = [
            "what is your name",
            "who are you", 
            "tell me about yourself",
            "hello",
            "hi"
        ]
        
        for question in test_questions:
            response = handler.process_command(question)
            print(f"\nQ: {question}")
            print(f"A: {response[:100]}...")
            
    except Exception as e:
        print(f"Error testing character responses: {e}")

if __name__ == "__main__":
    test_configuration()
    test_character_responses() 