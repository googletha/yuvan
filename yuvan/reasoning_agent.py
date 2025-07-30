"""
ReAct-style Reasoning Agent for Yuvan AI Assistant
Implements autonomous reasoning, planning, and decision making
Based on ReAct (Reasoning + Acting) paradigm with BabyAGI-style task decomposition
"""

import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import requests
from yuvan.memory_system import MemorySystem
import config_Version2 as config

class ActionType(Enum):
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    PLAN = "plan"
    REFLECT = "reflect"
    COMPLETE = "complete"

@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning process"""
    step_id: int
    action_type: ActionType
    content: str
    timestamp: datetime
    confidence: float
    context: Dict[str, Any]

@dataclass
class Task:
    """Represents a task to be executed"""
    id: str
    description: str
    priority: int
    status: str  # pending, in_progress, completed, failed
    subtasks: List['Task']
    dependencies: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None

class ReasoningAgent:
    """Advanced reasoning agent with autonomous decision making"""
    
    def __init__(self, memory_system: MemorySystem = None):
        self.memory_system = memory_system or MemorySystem()
        self.api_key = config.GROQ_API_KEY
        self.model = config.GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Reasoning state
        self.reasoning_steps: List[ReasoningStep] = []
        self.current_step = 0
        self.max_reasoning_steps = 20
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        
        # Available tools/actions
        self.available_tools = {
            "file_analysis": self._analyze_file,
            "folder_analysis": self._analyze_folder,
            "system_command": self._execute_system_command,
            "web_search": self._web_search,
            "memory_search": self._search_memory,
            "create_subtask": self._create_subtask,
            "file_operation": self._file_operation
        }
        
        # System prompts for different reasoning modes
        self.reasoning_prompts = {
            "analysis": """You are Yuvan, an advanced AI assistant with autonomous reasoning capabilities. 
            You are analyzing a file or folder. Break down the task systematically:
            1. First THINK about what needs to be analyzed
            2. Then ACT to gather information
            3. OBSERVE the results
            4. PLAN next steps if needed
            5. REFLECT on findings
            6. COMPLETE with summary and recommendations""",
            
            "problem_solving": """You are Yuvan, solving a complex problem autonomously.
            Use the ReAct framework:
            - THINK: Reason about the problem and approach
            - ACT: Take specific actions to gather info or make changes
            - OBSERVE: Analyze the results of your actions
            - Continue until the problem is solved or you need human input""",
            
            "task_execution": """You are Yuvan, executing a user's request autonomously.
            Break down complex tasks into manageable subtasks.
            Plan, execute, and verify each step systematically."""
        }
    
    def autonomous_reasoning(self, initial_prompt: str, mode: str = "problem_solving") -> str:
        """Main autonomous reasoning loop"""
        self.reasoning_steps = []
        self.current_step = 0
        
        # Add initial prompt to memory
        self.memory_system.add_memory(
            content=f"Starting autonomous reasoning: {initial_prompt}",
            memory_type="reasoning",
            importance=0.9,
            tags=["autonomous", "reasoning", mode]
        )
        
        # Start reasoning loop
        context = {
            "initial_prompt": initial_prompt,
            "mode": mode,
            "available_tools": list(self.available_tools.keys())
        }
        
        final_result = self._reasoning_loop(initial_prompt, mode, context)
        
        # Store reasoning session in memory
        self._store_reasoning_session()
        
        return final_result
    
    def _reasoning_loop(self, prompt: str, mode: str, context: Dict[str, Any]) -> str:
        """Core reasoning loop implementation"""
        system_prompt = self.reasoning_prompts.get(mode, self.reasoning_prompts["problem_solving"])
        
        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {prompt}\n\nAvailable tools: {list(self.available_tools.keys())}\n\nStart reasoning:"}
        ]
        
        while self.current_step < self.max_reasoning_steps:
            try:
                # Get AI response
                response = self._get_ai_response(conversation_history)
                
                # Parse the response for action type and content
                action_type, content, confidence = self._parse_reasoning_response(response)
                
                # Create reasoning step
                step = ReasoningStep(
                    step_id=self.current_step,
                    action_type=action_type,
                    content=content,
                    timestamp=datetime.now(),
                    confidence=confidence,
                    context=context.copy()
                )
                
                self.reasoning_steps.append(step)
                
                # Execute the reasoning step
                step_result = self._execute_reasoning_step(step)
                
                # Add step and result to conversation history
                conversation_history.append({"role": "assistant", "content": response})
                if step_result:
                    conversation_history.append({"role": "user", "content": f"Action result: {step_result}"})
                
                # Check if reasoning is complete
                if action_type == ActionType.COMPLETE:
                    return content
                
                self.current_step += 1
                
                # Prevent infinite loops
                if self.current_step >= self.max_reasoning_steps:
                    return self._generate_summary("Maximum reasoning steps reached")
                
            except Exception as e:
                error_msg = f"Error in reasoning step {self.current_step}: {str(e)}"
                print(error_msg)
                return error_msg
        
        return self._generate_summary("Reasoning loop completed")
    
    def _get_ai_response(self, conversation_history: List[Dict]) -> str:
        """Get response from AI model"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": conversation_history,
            "temperature": 0.7,
            "max_tokens": 1500,
            "stream": False
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API request failed: {response.status_code}")
    
    def _parse_reasoning_response(self, response: str) -> Tuple[ActionType, str, float]:
        """Parse AI response to extract action type and content"""
        response_lower = response.lower()
        
        # Define action patterns
        action_patterns = {
            ActionType.THINK: [r"think:", r"thinking:", r"i think", r"let me think"],
            ActionType.ACT: [r"act:", r"action:", r"i will", r"let me"],
            ActionType.OBSERVE: [r"observe:", r"observation:", r"i observe", r"i see"],
            ActionType.PLAN: [r"plan:", r"planning:", r"i plan", r"next steps"],
            ActionType.REFLECT: [r"reflect:", r"reflection:", r"i reflect", r"looking back"],
            ActionType.COMPLETE: [r"complete:", r"done:", r"finished:", r"conclusion:"]
        }
        
        # Default values
        action_type = ActionType.THINK
        confidence = 0.5
        
        # Check for explicit action indicators
        for act_type, patterns in action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_lower):
                    action_type = act_type
                    confidence = 0.8
                    break
            if confidence > 0.5:
                break
        
        # Extract content (remove action prefixes)
        content = response
        for patterns in action_patterns.values():
            for pattern in patterns:
                content = re.sub(pattern, "", content, flags=re.IGNORECASE).strip()
        
        return action_type, content, confidence
    
    def _execute_reasoning_step(self, step: ReasoningStep) -> Optional[str]:
        """Execute a reasoning step and return results"""
        if step.action_type == ActionType.ACT:
            return self._execute_action(step.content)
        elif step.action_type == ActionType.OBSERVE:
            return self._make_observation(step.content)
        elif step.action_type == ActionType.PLAN:
            return self._create_plan(step.content)
        else:
            # For THINK, REFLECT, COMPLETE - no action needed
            return None
    
    def _execute_action(self, action_description: str) -> str:
        """Execute an action based on description"""
        action_lower = action_description.lower()
        
        # Pattern matching for different actions
        if "analyze file" in action_lower or "check file" in action_lower:
            file_match = re.search(r"file[:\s]+([^\s]+)", action_description)
            if file_match:
                filename = file_match.group(1)
                return self._analyze_file(filename)
        
        elif "analyze folder" in action_lower or "check folder" in action_lower:
            folder_match = re.search(r"folder[:\s]+([^\s]+)", action_description)
            if folder_match:
                foldername = folder_match.group(1)
                return self._analyze_folder(foldername)
        
        elif "search memory" in action_lower:
            query_match = re.search(r"search[:\s]+(.+)", action_description)
            if query_match:
                query = query_match.group(1)
                return self._search_memory(query)
        
        elif "command" in action_lower or "execute" in action_lower:
            return "Command execution requires explicit user permission for security"
        
        else:
            return f"Action noted: {action_description}"
    
    def _make_observation(self, observation: str) -> str:
        """Process an observation"""
        # Store observation in memory
        self.memory_system.add_memory(
            content=f"Observation: {observation}",
            memory_type="reasoning",
            importance=0.6,
            tags=["observation", "reasoning"]
        )
        return f"Observation recorded: {observation}"
    
    def _create_plan(self, plan: str) -> str:
        """Create and store a plan"""
        # Store plan in memory
        self.memory_system.add_memory(
            content=f"Plan: {plan}",
            memory_type="planning",
            importance=0.8,
            tags=["plan", "reasoning"]
        )
        return f"Plan created: {plan}"
    
    # Tool implementations
    def _analyze_file(self, filename: str) -> str:
        """Analyze a file"""
        try:
            import os
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()[:1000]  # First 1000 chars
                
                file_stats = os.stat(filename)
                analysis = f"""File Analysis: {filename}
Size: {file_stats.st_size} bytes
Modified: {datetime.fromtimestamp(file_stats.st_mtime)}
Content preview: {content[:200]}...
File appears to be: {self._detect_file_type(filename)}"""
                
                return analysis
            else:
                return f"File not found: {filename}"
        except Exception as e:
            return f"Error analyzing file: {str(e)}"
    
    def _analyze_folder(self, foldername: str) -> str:
        """Analyze a folder"""
        try:
            import os
            if os.path.exists(foldername) and os.path.isdir(foldername):
                files = []
                total_size = 0
                
                for root, dirs, filenames in os.walk(foldername):
                    for filename in filenames[:10]:  # Limit to first 10 files
                        filepath = os.path.join(root, filename)
                        size = os.path.getsize(filepath)
                        total_size += size
                        files.append(f"{filename} ({size} bytes)")
                
                analysis = f"""Folder Analysis: {foldername}
Total files: {len(files)}
Total size: {total_size} bytes
Sample files: {', '.join(files[:5])}
Contains: {self._detect_folder_type(foldername)}"""
                
                return analysis
            else:
                return f"Folder not found: {foldername}"
        except Exception as e:
            return f"Error analyzing folder: {str(e)}"
    
    def _search_memory(self, query: str) -> str:
        """Search memory system"""
        memories = self.memory_system.search_memories(query, limit=5)
        if memories:
            results = []
            for memory in memories:
                results.append(f"[{memory.memory_type}] {memory.content[:100]}...")
            return f"Found {len(memories)} relevant memories:\n" + "\n".join(results)
        else:
            return "No relevant memories found"
    
    def _execute_system_command(self, command: str) -> str:
        """Execute system command (with safety checks)"""
        # For security, this should be restricted
        return "System command execution requires explicit user permission"
    
    def _web_search(self, query: str) -> str:
        """Perform web search"""
        return f"Web search for '{query}' - Feature requires API integration"
    
    def _create_subtask(self, description: str) -> str:
        """Create a subtask"""
        task = Task(
            id=f"task_{int(time.time())}",
            description=description,
            priority=1,
            status="pending",
            subtasks=[],
            dependencies=[],
            created_at=datetime.now()
        )
        self.task_queue.append(task)
        return f"Created subtask: {description}"
    
    def _file_operation(self, operation: str) -> str:
        """Perform file operations"""
        return f"File operation '{operation}' - Requires specific implementation"
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from extension"""
        ext = filename.split('.')[-1].lower()
        type_map = {
            'py': 'Python script',
            'js': 'JavaScript file',
            'html': 'HTML document',
            'css': 'CSS stylesheet',
            'txt': 'Text file',
            'json': 'JSON data',
            'md': 'Markdown document'
        }
        return type_map.get(ext, 'Unknown file type')
    
    def _detect_folder_type(self, foldername: str) -> str:
        """Detect folder type based on contents"""
        try:
            import os
            files = os.listdir(foldername)
            
            if any(f.endswith('.py') for f in files):
                return "Python project"
            elif any(f.endswith('.js') for f in files):
                return "JavaScript project"
            elif 'package.json' in files:
                return "Node.js project"
            elif 'requirements.txt' in files:
                return "Python project with dependencies"
            else:
                return "Generic folder"
        except Exception:
            return "Unknown folder type"
    
    def _generate_summary(self, reason: str) -> str:
        """Generate summary of reasoning session"""
        summary = f"Reasoning session completed: {reason}\n\n"
        summary += f"Total steps: {len(self.reasoning_steps)}\n"
        
        # Summarize step types
        step_counts = {}
        for step in self.reasoning_steps:
            step_counts[step.action_type.value] = step_counts.get(step.action_type.value, 0) + 1
        
        summary += f"Step breakdown: {step_counts}\n\n"
        
        # Add key insights
        summary += "Key reasoning steps:\n"
        for i, step in enumerate(self.reasoning_steps[-3:], 1):  # Last 3 steps
            summary += f"{i}. [{step.action_type.value.upper()}] {step.content[:100]}...\n"
        
        return summary
    
    def _store_reasoning_session(self):
        """Store the entire reasoning session in memory"""
        session_summary = self._generate_summary("Session completed")
        
        self.memory_system.add_memory(
            content=session_summary,
            memory_type="reasoning_session",
            importance=0.9,
            tags=["autonomous", "reasoning", "session"],
            context={
                "total_steps": len(self.reasoning_steps),
                "completed_at": datetime.now().isoformat()
            }
        )
    
    def get_reasoning_history(self) -> List[ReasoningStep]:
        """Get the history of reasoning steps"""
        return self.reasoning_steps.copy()
    
    def clear_reasoning_state(self):
        """Clear current reasoning state"""
        self.reasoning_steps = []
        self.current_step = 0
        self.task_queue = []