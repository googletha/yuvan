import json
import re
import datetime
import psutil
import os
import requests
import math
import random
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from yuvan.ai_advisory_agent import AIAdvisoryAgent
import config_Version2 as config
import yuvan_config_Version2 as yuvan_config

class Tool(ABC):
    """Base class for all tools"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the tool name"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return the tool description"""
        pass
    
    @abstractmethod
    def get_patterns(self) -> List[str]:
        """Return regex patterns that match this tool"""
        pass
    
    @abstractmethod
    def execute(self, command: str) -> str:
        """Execute the tool with the given command"""
        pass

class WeatherTool(Tool):
    """Tool for getting weather information using SerpAPI"""
    
    def get_name(self) -> str:
        return "weather"
    
    def get_description(self) -> str:
        return "Get current weather information for a location"
    
    def get_patterns(self) -> List[str]:
        return [
            r"^weather$",  # Just "weather" - will ask for location
            r"weather\s+(?:in\s+)?(.+)",
            r"temperature\s+(?:in\s+)?(.+)",
            r"how\s+(?:is\s+)?the\s+weather\s+(?:in\s+)?(.+)",
            r"what's\s+the\s+weather\s+(?:like\s+)?(?:in\s+)?(.+)"
        ]
    
    def execute(self, command: str) -> str:
        try:
            # Check if it's just "weather" without location
            if command.lower().strip() == "weather":
                return "Please specify a location for weather information. For example: 'weather in London' or 'weather in New York'"
            
            # Extract location from command
            location = None
            for pattern in self.get_patterns():
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    # Skip the first pattern (just "weather") since we already handled it
                    if pattern == r"^weather$":
                        continue
                    location = match.group(1).strip()
                    break
            
            if not location:
                return "Please specify a location for weather information."
            
            # Use SerpAPI to get weather
            url = "https://serpapi.com/search"
            params = {
                "q": f"weather {location}",
                "api_key": config.SERPAPI_API_KEY,
                "engine": "google"
            }
            
            response = requests.get(url, params=params, timeout=5)  # Added timeout
            data = response.json()
            
            if "answer_box" in data and "weather" in data["answer_box"]:
                weather_data = data["answer_box"]["weather"]
                return f"Weather in {location}: {weather_data}"
            elif "organic_results" in data and data["organic_results"]:
                # Fallback to first result
                result = data["organic_results"][0]
                return f"Weather information for {location}: {result.get('snippet', 'Information not available')}"
            else:
                return f"Sorry, I couldn't find weather information for {location}."
                
        except Exception as e:
            return f"Error getting weather information: {str(e)}"

class GoogleSearchTool(Tool):
    """Tool for Google searches using SerpAPI"""
    
    def get_name(self) -> str:
        return "google_search"
    
    def get_description(self) -> str:
        return "Search Google for information"
    
    def get_patterns(self) -> List[str]:
        return [
            r"search\s+(?:for\s+)?(.+)",
            r"google\s+(.+)",
            r"find\s+(?:information\s+about\s+)?(.+)",
            r"what\s+is\s+(.+)",
            r"who\s+is\s+(.+)",
            r"how\s+to\s+(.+)"
        ]
    
    def execute(self, command: str) -> str:
        try:
            # Extract search query
            query = None
            for pattern in self.get_patterns():
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    query = match.group(1).strip()
                    break
            
            if not query:
                return "Please specify what you'd like to search for."
            
            # Use SerpAPI for Google search
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": config.SERPAPI_API_KEY,
                "engine": "google",
                "num": 3  # Get top 3 results
            }
            
            response = requests.get(url, params=params, timeout=5)  # Added timeout
            data = response.json()
            
            if "organic_results" in data and data["organic_results"]:
                results = data["organic_results"][:3]
                response_text = f"Search results for '{query}':\n\n"
                
                for i, result in enumerate(results, 1):
                    title = result.get("title", "No title")
                    snippet = result.get("snippet", "No description")
                    link = result.get("link", "")
                    response_text += f"{i}. {title}\n{snippet}\n{link}\n\n"
                
                return response_text
            else:
                return f"No search results found for '{query}'."
                
        except Exception as e:
            return f"Error performing search: {str(e)}"

class MapsTool(Tool):
    """Tool for Google Maps functionality using SerpAPI"""
    
    def get_name(self) -> str:
        return "maps"
    
    def get_description(self) -> str:
        return "Get location information, directions, and nearby places"
    
    def get_patterns(self) -> List[str]:
        return [
            r"directions?\s+(?:to\s+)?(.+)",
            r"how\s+to\s+get\s+to\s+(.+)",
            r"where\s+is\s+(.+)",
            r"nearby\s+(.+)",
            r"restaurants?\s+(?:near\s+)?(.+)",
            r"hotels?\s+(?:near\s+)?(.+)",
            r"gas\s+stations?\s+(?:near\s+)?(.+)"
        ]
    
    def execute(self, command: str) -> str:
        try:
            # Extract location/query
            query = None
            for pattern in self.get_patterns():
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    query = match.group(1).strip()
                    break
            
            if not query:
                return "Please specify a location or what you're looking for."
            
            # Use SerpAPI for maps search
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": config.SERPAPI_API_KEY,
                "engine": "google_maps"
            }
            
            response = requests.get(url, params=params, timeout=5)  # Added timeout
            data = response.json()
            
            if "local_results" in data and data["local_results"]:
                results = data["local_results"][:5]
                response_text = f"Results for '{query}':\n\n"
                
                for i, result in enumerate(results, 1):
                    title = result.get("title", "No title")
                    address = result.get("address", "No address")
                    rating = result.get("rating", "No rating")
                    response_text += f"{i}. {title}\nAddress: {address}\nRating: {rating}\n\n"
                
                return response_text
            else:
                return f"No location results found for '{query}'."
                
        except Exception as e:
            return f"Error getting location information: {str(e)}"

class SystemInfoTool(Tool):
    """Tool for system information"""
    
    def get_name(self) -> str:
        return "system_info"
    
    def get_description(self) -> str:
        return "Get system information like CPU, RAM, disk usage"
    
    def get_patterns(self) -> List[str]:
        return [
            r"^system\s+info$",  # Just "system info"
            r"^cpu$",  # Just "cpu"
            r"^ram$",  # Just "ram"
            r"^memory$",  # Just "memory"
            r"system\s+info",
            r"cpu\s+usage",
            r"ram\s+usage",
            r"memory\s+usage",
            r"disk\s+usage",
            r"computer\s+info"
        ]
    
    def execute(self, command: str) -> str:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)  # Reduced interval for faster response
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            info = f"System Information:\n"
            info += f"CPU Usage: {cpu_percent}%\n"
            info += f"RAM Usage: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)\n"
            info += f"Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)\n"
            
            return info
        except Exception as e:
            return f"Error getting system information: {str(e)}"

class MathTool(Tool):
    """Tool for mathematical calculations"""
    
    def get_name(self) -> str:
        return "math"
    
    def get_description(self) -> str:
        return "Perform mathematical calculations"
    
    def get_patterns(self) -> List[str]:
        return [
            r"calculate\s+(.+)",
            r"what\s+is\s+(\d+[\+\-\*\/\^\(\)\d\s]+)",
            r"(\d+[\+\-\*\/\^\(\)\d\s]+)\s*=\s*\?",
            r"math\s+(.+)"
        ]
    
    def execute(self, command: str) -> str:
        try:
            # Extract mathematical expression
            expression = None
            for pattern in self.get_patterns():
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    expression = match.group(1).strip()
                    break
            
            if not expression:
                return "Please provide a mathematical expression to calculate."
            
            # Clean and evaluate the expression
            expression = re.sub(r'[^\d\+\-\*\/\^\(\)\.\s]', '', expression)
            expression = expression.replace('^', '**')
            
            # Safe evaluation
            allowed_names = {
                'abs': abs, 'round': round, 'min': min, 'max': max,
                'sum': sum, 'pow': pow, 'sqrt': math.sqrt,
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'pi': math.pi, 'e': math.e
            }
            
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"Result: {expression} = {result}"
            
        except Exception as e:
            return f"Error calculating: {str(e)}"

class JokeTool(Tool):
    """Tool for telling jokes"""
    
    def get_name(self) -> str:
        return "joke"
    
    def get_description(self) -> str:
        return "Tell a random joke"
    
    def get_patterns(self) -> List[str]:
        return [
            r"^joke$",  # Just "joke"
            r"tell\s+(?:me\s+)?a\s+joke",
            r"funny",
            r"make\s+me\s+laugh"
        ]
    
    def execute(self, command: str) -> str:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What do you call a fish wearing a bowtie? So-fish-ticated!"
        ]
        return random.choice(jokes)

class FileTool(Tool):
    """Tool for file operations"""
    
    def get_name(self) -> str:
        return "file_operations"
    
    def get_description(self) -> str:
        return "List files, read files, and basic file operations"
    
    def get_patterns(self) -> List[str]:
        return [
            r"list\s+files?\s+(?:in\s+)?(.+)",
            r"read\s+file\s+(.+)",
            r"show\s+files?\s+(?:in\s+)?(.+)",
            r"what\s+files?\s+(?:are\s+)?(?:in\s+)?(.+)"
        ]
    
    def execute(self, command: str) -> str:
        try:
            # Extract directory/file path
            path = None
            for pattern in self.get_patterns():
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    path = match.group(1).strip()
                    break
            
            if not path:
                path = "."  # Current directory
            
            if "read file" in command.lower():
                # Read file content
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return f"File content of {path}:\n\n{content[:500]}..." if len(content) > 500 else content
                except Exception as e:
                    return f"Error reading file {path}: {str(e)}"
            else:
                # List files in directory
                try:
                    files = os.listdir(path)
                    if files:
                        file_list = "\n".join(files[:20])  # Limit to 20 files
                        return f"Files in {path}:\n{file_list}"
                    else:
                        return f"No files found in {path}"
                except Exception as e:
                    return f"Error listing files in {path}: {str(e)}"
                    
        except Exception as e:
            return f"Error with file operation: {str(e)}"

class TimeTool(Tool):
    """Tool for time and date information"""
    
    def get_name(self) -> str:
        return "time"
    
    def get_description(self) -> str:
        return "Get current time and date information"
    
    def get_patterns(self) -> List[str]:
        return [
            r"^time$",  # Just "time"
            r"^date$",  # Just "date"
            r"what\s+(?:is\s+)?(?:the\s+)?time",
            r"current\s+time",
            r"what\s+(?:is\s+)?(?:the\s+)?date",
            r"today's?\s+date"
        ]
    
    def execute(self, command: str) -> str:
        now = datetime.datetime.now()
        
        if "date" in command.lower():
            return f"Today's date is {now.strftime('%A, %B %d, %Y')}"
        else:
            return f"The current time is {now.strftime('%I:%M:%S %p')} on {now.strftime('%A, %B %d, %Y')}"

class ToolRegistry:
    """Registry for managing all available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all default tools"""
        default_tools = [
            WeatherTool(),
            GoogleSearchTool(),
            MapsTool(),
            SystemInfoTool(),
            MathTool(),
            JokeTool(),
            FileTool(),
            TimeTool()
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: Tool):
        """Register a new tool"""
        self.tools[tool.get_name()] = tool
        # Compile patterns for faster matching
        self.compiled_patterns[tool.get_name()] = [
            re.compile(pattern, re.IGNORECASE) for pattern in tool.get_patterns()
        ]
    
    def get_tool_for_command(self, command: str) -> Optional[Tool]:
        """Find the appropriate tool for a given command using compiled patterns"""
        for tool_name, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(command):
                    return self.tools[tool_name]
        return None
    
    def list_tools(self) -> str:
        """List all available tools"""
        tool_list = "Available tools:\n"
        for name, tool in self.tools.items():
            tool_list += f"- {name}: {tool.get_description()}\n"
        return tool_list

class TaskHandler:
    def __init__(self):
        self.advisory_agent = AIAdvisoryAgent(api_key=config.GROQ_API_KEY)
        self.tool_registry = ToolRegistry()
        
        # Load response guidelines from configuration
        self.response_guidelines = yuvan_config.get_response_guidelines()
        self.conversation_flow = yuvan_config.get_conversation_flow()
        
        # Simple rule-based responses (fallback before LLM)
        self.simple_responses = {
            "hello": random.choice(self.response_guidelines["greeting_responses"]),
            "hi": random.choice(self.response_guidelines["greeting_responses"]),
            "help": self.tool_registry.list_tools,
            "tools": self.tool_registry.list_tools,
            "bye": "Goodbye! Have a great day!",
            "thanks": "You're welcome! Is there anything else I can help you with?",
            "thank you": "You're welcome! Is there anything else I can help you with?",
            "what is your name": self.response_guidelines["personal_questions"]["name"],
            "who are you": self.response_guidelines["personal_questions"]["identity"],
            "tell me about yourself": self.response_guidelines["personal_questions"]["capabilities"]
        }
    
    def process_command(self, command: str) -> str:
        """Process a command through the tool system"""
        command = command.strip()
        
        # Check for personal questions first (before tool matching)
        personal_questions = [
            "what is your name", "what's your name", "who are you", 
            "tell me about yourself", "what can you do", "what are your capabilities"
        ]
        
        for question in personal_questions:
            if question in command.lower():
                if "name" in question:
                    return self.response_guidelines["personal_questions"]["name"]
                elif "who are you" in question:
                    return self.response_guidelines["personal_questions"]["identity"]
                elif "capabilities" in question or "what can you do" in question:
                    return self.response_guidelines["personal_questions"]["capabilities"]
                else:
                    return self.response_guidelines["personal_questions"]["capabilities"]
        
        # Check for simple responses
        for key, response in self.simple_responses.items():
            if key in command.lower():
                if callable(response):
                    return response()
                return response
        
        # Try to find and execute a tool
        tool = self.tool_registry.get_tool_for_command(command)
        if tool:
            try:
                result = tool.execute(command)
                return result
            except Exception as e:
                return f"Error executing {tool.get_name()}: {str(e)}"
        
        # If no tool matches, pass to the advisory agent
        return self.advisory_agent.get_response(command) 