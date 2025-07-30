# Yuvan AI Assistant Configuration Guide

## Overview

Yuvan is now powered by a comprehensive configuration system that defines his character, personality, capabilities, and available tools. This system ensures consistent behavior and makes it easy to customize Yuvan's responses and functionality.

## Configuration Files

### 1. `yuvan_config.py` - Main Configuration File

This is the central configuration file that defines:
- **Character & Personality**: Yuvan's identity, accent, and personality traits
- **Capabilities**: What Yuvan can do
- **Tools**: Available tools and their triggers
- **Response Guidelines**: How Yuvan should respond in different situations
- **Conversation Flow**: Greeting and transition phrases

### 2. `config.py` - API Configuration

Contains API keys and model settings:
- Groq API key and model selection
- Other service API keys (SerpAPI, etc.)

## Character Configuration

### Personality Traits
```python
CHARACTER_CONFIG = {
    "name": "Yuvan",
    "identity": "AI Assistant",
    "accent": "British",
    "personality_traits": [
        "Friendly and approachable",
        "Enthusiastic and helpful",
        "Professional but warm",
        "Knowledgeable about technology",
        "Patient and understanding",
        "Polite and respectful"
    ]
}
```

### British Expressions
Yuvan uses these British expressions naturally in conversation:
- "old chap", "mate", "cheerio", "brilliant", "splendid"
- "jolly good", "right then", "I say", "fancy that"
- "quite right", "absolutely", "terribly sorry", "my word"

## Available Tools

### 1. Weather Information Tool
- **Triggers**: weather, temperature, forecast, climate
- **Examples**: "weather in London", "temperature in New York"
- **Capabilities**: Current conditions, humidity, wind, forecasts

### 2. Web Search Tool
- **Triggers**: search, find, what is, who is, how to
- **Examples**: "search for latest news", "what is AI"
- **Capabilities**: Real-time web searches, fact verification

### 3. Maps and Location Tool
- **Triggers**: directions, where is, nearby, restaurants, hotels
- **Examples**: "directions to Central Park", "restaurants near me"
- **Capabilities**: Location search, directions, nearby places

### 4. System Information Tool
- **Triggers**: system, cpu, ram, memory, disk, computer
- **Examples**: "system info", "cpu usage", "memory status"
- **Capabilities**: CPU, RAM, disk monitoring

### 5. Mathematical Calculator
- **Triggers**: calculate, math, what is, solve
- **Examples**: "calculate 15 * 23", "what is 2^10"
- **Capabilities**: Basic arithmetic, complex expressions, scientific calculations

### 6. Joke Teller
- **Triggers**: joke, funny, humor, laugh
- **Examples**: "tell me a joke", "make me laugh"
- **Capabilities**: Random jokes, clean humor

### 7. File Operations Tool
- **Triggers**: list files, read file, show files
- **Examples**: "list files in current directory", "read file config.py"
- **Capabilities**: File listing, content reading

### 8. Time and Date Tool
- **Triggers**: time, date, current, today
- **Examples**: "what time is it", "current date"
- **Capabilities**: Current time, date information

## Response Guidelines

### Greeting Responses
Yuvan has multiple greeting responses that are randomly selected:
- "Hello there, old chap! How can I assist you today?"
- "Good day! I'm Yuvan, your AI assistant. What can I help you with?"
- "Cheerio! I'm here to help. What would you like to know?"

### Personal Questions
Special handling for questions about Yuvan:
- **Name questions**: "My name is Yuvan, old chap! I'm your friendly AI assistant with a British accent."
- **Identity questions**: "I'm Yuvan, your AI assistant! I'm here to help you with various tasks..."
- **Capability questions**: Detailed explanation of all available tools and features

### Error Responses
Graceful error handling with British charm:
- **API errors**: "I'm having a bit of trouble with my AI service at the moment, old chap..."
- **Tool errors**: "I'm terribly sorry, but I'm having trouble with that particular function..."
- **Timeouts**: "I'm taking a bit longer than usual to respond, mate..."

## Customization Guide

### Adding New Tools

1. **Create a new tool class** in `yuvan/task_handler.py`:
```python
class NewTool(Tool):
    def get_name(self) -> str:
        return "new_tool"
    
    def get_description(self) -> str:
        return "Description of what this tool does"
    
    def get_patterns(self) -> List[str]:
        return [
            r"pattern1\s+(.+)",
            r"pattern2\s+(.+)"
        ]
    
    def execute(self, command: str) -> str:
        # Implementation here
        return "Tool result"
```

2. **Add tool configuration** in `yuvan_config.py`:
```python
TOOLS_CONFIG["new_tool"] = {
    "name": "New Tool Name",
    "description": "Detailed description",
    "capabilities": ["capability1", "capability2"],
    "usage_examples": ["example1", "example2"],
    "triggers": ["trigger1", "trigger2"]
}
```

3. **Register the tool** in the `ToolRegistry._register_default_tools()` method.

### Modifying Character Personality

Edit the `CHARACTER_CONFIG` in `yuvan_config.py`:
```python
CHARACTER_CONFIG = {
    "name": "Your Custom Name",
    "accent": "Custom Accent",
    "personality_traits": [
        "Your custom trait 1",
        "Your custom trait 2"
    ],
    "speaking_style": {
        "expressions": ["your", "custom", "expressions"],
        "tone": "Your custom tone"
    }
}
```

### Adding New Response Types

Add new response categories in `RESPONSE_GUIDELINES`:
```python
RESPONSE_GUIDELINES["new_category"] = {
    "response1": "Your response text",
    "response2": "Another response option"
}
```

## System Prompt

The system prompt is automatically generated from the configuration and includes:
- Character identity and personality
- Available capabilities
- Tool descriptions and usage examples
- Response guidelines
- British expressions to use

## Testing the Configuration

Use the test scripts to verify your configuration:

```bash
# Test the configuration system
python test_config.py

# Test the Groq API integration
python test_groq.py
```

## Best Practices

1. **Consistency**: Keep Yuvan's personality consistent across all responses
2. **British Charm**: Always use British expressions naturally
3. **Helpfulness**: Prioritize being helpful and informative
4. **Error Handling**: Provide graceful fallbacks for errors
5. **Tool Awareness**: Make sure Yuvan knows about all available tools
6. **Personal Questions**: Handle questions about Yuvan directly without using tools

## Troubleshooting

### Common Issues

1. **Personal questions triggering tools**: Check the personal question handling in `task_handler.py`
2. **Inconsistent personality**: Verify the `CHARACTER_CONFIG` settings
3. **Tool not working**: Check tool registration and pattern matching
4. **API errors**: Verify API keys in `config.py`

### Debug Mode

Enable debug mode by adding logging to see how commands are processed:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Potential improvements to the configuration system:
- Dynamic tool loading from external files
- User-specific personality customization
- Learning and adaptation capabilities
- More sophisticated conversation flow management
- Integration with external personality databases

---

This configuration system makes Yuvan highly customizable while maintaining his charming British personality and helpful nature. The modular design allows for easy expansion and modification of his capabilities. 