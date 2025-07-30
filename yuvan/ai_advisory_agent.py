import config_Version2 as config
import requests
import json
import yuvan_config_Version2 as yuvan_config

class AIAdvisoryAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or config.GROQ_API_KEY
        self.model = config.GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Load configuration from yuvan_config
        self.character_config = yuvan_config.get_character_config()
        self.capabilities = yuvan_config.get_capabilities()
        self.tools_config = yuvan_config.get_tools_config()
        self.response_guidelines = yuvan_config.get_response_guidelines()
        self.conversation_flow = yuvan_config.get_conversation_flow()
        
        # Get the comprehensive system prompt
        self.system_prompt = yuvan_config.get_system_prompt()

    def get_response(self, prompt):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Add tool information to the context
            tools_context = self._get_tools_context()
            enhanced_system_prompt = self.system_prompt + "\n\n" + tools_context
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                return self._handle_api_error(response)
                    
        except requests.exceptions.Timeout:
            return self.response_guidelines["error_responses"]["timeout"]
        except requests.exceptions.RequestException as e:
            return self.response_guidelines["error_responses"]["api_error"]
        except Exception as e:
            return self.response_guidelines["error_responses"]["unknown"]
    
    def _get_tools_context(self):
        """Generate detailed context about available tools"""
        tools_context = "DETAILED TOOL INFORMATION:\n\n"
        
        for tool_name, tool_config in self.tools_config.items():
            tools_context += f"Tool: {tool_config['name']}\n"
            tools_context += f"Description: {tool_config['description']}\n"
            tools_context += f"Capabilities: {', '.join(tool_config['capabilities'])}\n"
            tools_context += f"Usage Examples: {', '.join(tool_config['usage_examples'])}\n"
            tools_context += f"Trigger Words: {', '.join(tool_config['triggers'])}\n\n"
        
        return tools_context
    
    def _handle_api_error(self, response):
        """Handle different types of API errors with appropriate responses"""
        error_msg = f"API Error: {response.status_code}"
        if response.text:
            try:
                error_data = response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
        
        # Provide helpful fallback responses based on error type
        if response.status_code == 401:
            return self.response_guidelines["error_responses"]["api_error"]
        elif response.status_code == 402:
            return self.response_guidelines["error_responses"]["api_error"]
        elif response.status_code == 429:
            return self.response_guidelines["error_responses"]["timeout"]
        else:
            return self.response_guidelines["error_responses"]["api_error"]
    
    def get_character_info(self):
        """Get character information for debugging or display"""
        return {
            "name": self.character_config["name"],
            "accent": self.character_config["accent"],
            "personality": self.character_config["personality_traits"],
            "capabilities": self.capabilities,
            "available_tools": list(self.tools_config.keys())
        }
    
    def get_tool_suggestions(self, user_input):
        """Suggest relevant tools based on user input"""
        suggestions = []
        user_input_lower = user_input.lower()
        
        for tool_name, tool_config in self.tools_config.items():
            for trigger in tool_config['triggers']:
                if trigger.lower() in user_input_lower:
                    suggestions.append({
                        "tool": tool_name,
                        "name": tool_config['name'],
                        "description": tool_config['description'],
                        "examples": tool_config['usage_examples']
                    })
                    break
        
        return suggestions
