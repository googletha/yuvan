"""
Enhanced Task Handler for Yuvan AI Assistant
Integrates all advanced features: memory, reasoning, terminal, document processing, 
streaming TTS, file system crawling, and app management
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import threading

# Import all the new modules
from yuvan.memory_system import MemorySystem
from yuvan.reasoning_agent import ReasoningAgent
from yuvan.terminal_assistant import TerminalAssistant
from yuvan.document_processor import DocumentProcessor
from yuvan.streaming_tts import StreamingTTS, AsyncStreamingTTS
from yuvan.file_system_crawler import FileSystemCrawler
from yuvan.app_launcher import ApplicationLauncher

# Import existing modules
from yuvan.task_handler import TaskHandler, Tool
from yuvan.ai_advisory_agent import AIAdvisoryAgent
import config_Version2 as config
import yuvan_config_Version2 as yuvan_config

class AutonomousReasoningTool(Tool):
    """Tool for autonomous reasoning and problem solving"""
    
    def __init__(self, reasoning_agent: ReasoningAgent):
        self.reasoning_agent = reasoning_agent
    
    def get_name(self) -> str:
        return "autonomous_reasoning"
    
    def get_description(self) -> str:
        return "Autonomous reasoning and problem solving using ReAct framework"
    
    def get_patterns(self) -> List[str]:
        return [
            r"analyze this (.+)",
            r"yuvan,?\s+fix\s+(.+)",
            r"yuvan,?\s+analyze\s+(.+)",
            r"solve\s+(.+)",
            r"figure out\s+(.+)",
            r"autonomous\s+(.+)"
        ]
    
    def execute(self, command: str) -> str:
        # Extract the task from the command
        import re
        patterns = self.get_patterns()
        
        task = command
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                task = match.group(1)
                break
        
        # Determine reasoning mode
        mode = "problem_solving"
        if "analyze" in command.lower():
            mode = "analysis"
        elif "fix" in command.lower():
            mode = "problem_solving"
        
        try:
            result = self.reasoning_agent.autonomous_reasoning(task, mode)
            return f"Autonomous reasoning completed:\n\n{result}"
        except Exception as e:
            return f"Error in autonomous reasoning: {str(e)}"

class DocumentProcessingTool(Tool):
    """Tool for processing documents with OCR"""
    
    def __init__(self, doc_processor: DocumentProcessor):
        self.doc_processor = doc_processor
    
    def get_name(self) -> str:
        return "document_processing"
    
    def get_description(self) -> str:
        return "Process PDF, DOCX, TXT files with OCR support"
    
    def get_patterns(self) -> List[str]:
        return [
            r"process\s+document\s+(.+)",
            r"read\s+(.+\.(?:pdf|docx|txt|doc))",
            r"extract\s+text\s+from\s+(.+)",
            r"ocr\s+(.+)",
            r"summarize\s+(.+\.(?:pdf|docx|txt|doc))"
        ]
    
    def execute(self, command: str) -> str:
        import re
        patterns = self.get_patterns()
        
        file_path = None
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                file_path = match.group(1).strip()
                break
        
        if not file_path:
            return "Please specify a file path to process"
        
        try:
            # Process the document
            use_ocr = "ocr" in command.lower()
            processed_doc = self.doc_processor.process_document(file_path, use_ocr=use_ocr)
            
            result = f"Document processed successfully:\n"
            result += f"File: {processed_doc.file_path}\n"
            result += f"Type: {processed_doc.file_type}\n"
            result += f"Size: {processed_doc.file_size} bytes\n"
            result += f"Processing time: {processed_doc.processing_time:.2f}s\n"
            
            if processed_doc.ocr_used:
                result += "OCR was used for text extraction\n"
            
            if processed_doc.summary:
                result += f"\nSummary:\n{processed_doc.summary}\n"
            
            # Store in memory
            return result
            
        except Exception as e:
            return f"Error processing document: {str(e)}"

class TerminalTool(Tool):
    """Tool for terminal command execution"""
    
    def __init__(self, terminal_assistant: TerminalAssistant):
        self.terminal_assistant = terminal_assistant
    
    def get_name(self) -> str:
        return "terminal"
    
    def get_description(self) -> str:
        return "Execute terminal commands safely"
    
    def get_patterns(self) -> List[str]:
        return [
            r"run\s+(.+)",
            r"execute\s+(.+)",
            r"command\s+(.+)",
            r"terminal\s+(.+)",
            r"cmd\s+(.+)"
        ]
    
    def execute(self, command: str) -> str:
        import re
        patterns = self.get_patterns()
        
        cmd_to_run = command
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                cmd_to_run = match.group(1).strip()
                break
        
        try:
            result = self.terminal_assistant.execute_command_from_text(cmd_to_run)
            return self.terminal_assistant.format_command_result(result)
        except Exception as e:
            return f"Error executing command: {str(e)}"

class FileSystemTool(Tool):
    """Tool for file system operations"""
    
    def __init__(self, fs_crawler: FileSystemCrawler):
        self.fs_crawler = fs_crawler
    
    def get_name(self) -> str:
        return "file_system"
    
    def get_description(self) -> str:
        return "Analyze file system, find duplicates, suggest cleanups"
    
    def get_patterns(self) -> List[str]:
        return [
            r"scan\s+(.+)",
            r"find\s+duplicates\s+in\s+(.+)",
            r"analyze\s+folder\s+(.+)",
            r"cleanup\s+suggestions\s+(.+)",
            r"find\s+large\s+files\s+in\s+(.+)"
        ]
    
    def execute(self, command: str) -> str:
        import re
        patterns = self.get_patterns()
        
        path = "."
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                path = match.group(1).strip()
                break
        
        try:
            if "scan" in command.lower() or "analyze" in command.lower():
                results = self.fs_crawler.crawl_directory(path, calculate_hashes=True)
                
                response = f"File system scan completed:\n"
                response += f"Files found: {results['files_found']}\n"
                response += f"Duplicates found: {results['duplicates_found']}\n"
                response += f"Cleanup suggestions: {results['cleanup_suggestions']}\n"
                response += f"Scan time: {results['scan_time']:.2f}s\n"
                response += f"Total size: {self.fs_crawler._format_size(results['total_size'])}\n"
                
                if self.fs_crawler.duplicates:
                    response += "\nDuplicate groups found:\n"
                    for i, group in enumerate(self.fs_crawler.duplicates[:3], 1):
                        response += f"{i}. {len(group.files)} files, potential savings: {self.fs_crawler._format_size(group.potential_savings)}\n"
                
                if self.fs_crawler.cleanup_suggestions:
                    response += "\nCleanup suggestions:\n"
                    for i, suggestion in enumerate(self.fs_crawler.cleanup_suggestions[:3], 1):
                        response += f"{i}. {suggestion.suggestion_type}: {suggestion.reason}\n"
                
                return response
            
            elif "find" in command.lower() and "large" in command.lower():
                # Find large files
                large_files = self.fs_crawler.find_by_size(100 * 1024 * 1024)  # 100MB+
                
                response = f"Large files in {path}:\n"
                for i, file_info in enumerate(large_files[:10], 1):
                    response += f"{i}. {file_info.name} - {self.fs_crawler._format_size(file_info.size)}\n"
                
                return response
            
            else:
                return "Please specify what file system operation to perform"
                
        except Exception as e:
            return f"Error in file system operation: {str(e)}"

class AppLauncherTool(Tool):
    """Tool for launching and managing applications"""
    
    def __init__(self, app_launcher: ApplicationLauncher):
        self.app_launcher = app_launcher
    
    def get_name(self) -> str:
        return "app_launcher"
    
    def get_description(self) -> str:
        return "Launch, close, and manage applications"
    
    def get_patterns(self) -> List[str]:
        return [
            r"launch\s+(.+)",
            r"open\s+(.+)",
            r"start\s+(.+)",
            r"close\s+(.+)",
            r"kill\s+(.+)",
            r"list\s+apps",
            r"running\s+apps"
        ]
    
    def execute(self, command: str) -> str:
        import re
        patterns = self.get_patterns()
        
        if "list apps" in command.lower():
            apps = self.app_launcher.list_installed_applications()
            response = f"Installed applications ({len(apps)}):\n"
            for app in apps[:20]:  # Show first 20
                response += f"- {app['name']}\n"
            return response
        
        elif "running apps" in command.lower():
            running_apps = self.app_launcher.get_running_applications()
            response = f"Running applications ({len(running_apps)}):\n"
            for app in running_apps[:15]:  # Show first 15
                response += f"- {app.name} (PID: {app.pid})\n"
            return response
        
        else:
            app_name = None
            action = "launch"
            
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    app_name = match.group(1).strip()
                    if pattern.startswith(r"close") or pattern.startswith(r"kill"):
                        action = "close"
                    break
            
            if not app_name:
                return "Please specify an application name"
            
            try:
                if action == "launch":
                    result = self.app_launcher.launch_application(app_name)
                    if result['success']:
                        return f"Successfully launched {app_name}"
                    else:
                        response = f"Failed to launch {app_name}: {result['error']}"
                        if 'suggestions' in result and result['suggestions']:
                            response += f"\nSuggestions: {', '.join(result['suggestions'])}"
                        return response
                
                else:  # close
                    force = "kill" in command.lower()
                    result = self.app_launcher.close_application(app_name, force=force)
                    if result['success']:
                        return result['message']
                    else:
                        return f"Failed to close {app_name}: {result['error']}"
                        
            except Exception as e:
                return f"Error managing application: {str(e)}"

class EnhancedTaskHandler(TaskHandler):
    """Enhanced task handler with all advanced capabilities"""
    
    def __init__(self):
        # Initialize base task handler
        super().__init__()
        
        # Initialize advanced systems
        self.memory_system = MemorySystem()
        self.reasoning_agent = ReasoningAgent(self.memory_system)
        self.terminal_assistant = TerminalAssistant()
        self.document_processor = DocumentProcessor()
        self.fs_crawler = FileSystemCrawler()
        self.app_launcher = ApplicationLauncher()
        
        # Initialize streaming TTS
        self.streaming_tts = None
        self.tts_enabled = False
        
        # Add new tools to registry
        self._add_advanced_tools()
        
        # Statistics
        self.stats = {
            'commands_processed': 0,
            'autonomous_sessions': 0,
            'documents_processed': 0,
            'files_scanned': 0,
            'apps_launched': 0
        }
    
    def _add_advanced_tools(self):
        """Add all advanced tools to the tool registry"""
        # Add new tools
        self.tool_registry.tools.extend([
            AutonomousReasoningTool(self.reasoning_agent),
            DocumentProcessingTool(self.document_processor),
            TerminalTool(self.terminal_assistant),
            FileSystemTool(self.fs_crawler),
            AppLauncherTool(self.app_launcher)
        ])
    
    def initialize_streaming_tts(self, enable: bool = True):
        """Initialize streaming TTS system"""
        if enable and not self.streaming_tts:
            try:
                self.streaming_tts = StreamingTTS()
                self.streaming_tts.start_streaming()
                self.tts_enabled = True
                print("Streaming TTS initialized")
            except Exception as e:
                print(f"Warning: Could not initialize streaming TTS: {e}")
                self.tts_enabled = False
        
        elif not enable and self.streaming_tts:
            self.streaming_tts.stop_streaming()
            self.streaming_tts = None
            self.tts_enabled = False
    
    def process_command(self, command: str) -> str:
        """Enhanced command processing with memory and streaming TTS"""
        start_time = time.time()
        
        # Store command in memory
        self.memory_system.add_memory(
            content=f"User command: {command}",
            memory_type="conversation",
            importance=0.7,
            tags=["user", "command"]
        )
        
        # Get relevant context from memory
        context_memories = self.memory_system.get_recent_context(hours=2, limit=5)
        
        # Check if this is an autonomous reasoning request
        autonomous_triggers = [
            "yuvan, fix", "yuvan fix", "analyze this", "solve this",
            "figure out", "autonomous", "yuvan, analyze"
        ]
        
        if any(trigger in command.lower() for trigger in autonomous_triggers):
            self.stats['autonomous_sessions'] += 1
            
            # Use autonomous reasoning
            reasoning_tool = next(
                (tool for tool in self.tool_registry.tools if isinstance(tool, AutonomousReasoningTool)),
                None
            )
            
            if reasoning_tool:
                response = reasoning_tool.execute(command)
            else:
                response = "Autonomous reasoning not available"
        else:
            # Use standard processing with memory context
            enhanced_command = command
            
            # Add relevant context if available
            if context_memories:
                context_text = "\n".join([
                    f"Context: {mem.content[:100]}..." for mem in context_memories[-2:]
                ])
                enhanced_command = f"{command}\n\nRecent context:\n{context_text}"
            
            # Process with base handler
            response = super().process_command(enhanced_command)
        
        # Store response in memory
        self.memory_system.add_memory(
            content=f"Yuvan response: {response}",
            memory_type="conversation",
            importance=0.6,
            tags=["yuvan", "response"]
        )
        
        # Add to task memory
        processing_time = time.time() - start_time
        self.memory_system.add_task_memory(
            task=command,
            result=response,
            success=True,
            context={
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Stream to TTS if enabled
        if self.tts_enabled and self.streaming_tts:
            try:
                self.streaming_tts.add_text(response)
            except Exception as e:
                print(f"TTS error: {e}")
        
        # Update statistics
        self.stats['commands_processed'] += 1
        
        return response
    
    def get_memory_search(self, query: str, limit: int = 5) -> List[str]:
        """Search memory for relevant information"""
        memories = self.memory_system.search_memories(query, limit=limit)
        return [f"[{mem.memory_type}] {mem.content[:200]}..." for mem in memories]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        memory_stats = self.memory_system.get_memory_stats()
        
        tts_status = {}
        if self.streaming_tts:
            tts_status = self.streaming_tts.get_queue_status()
        
        return {
            "enhanced_features": {
                "memory_system": {
                    "total_memories": memory_stats.get("total_memories", 0),
                    "memory_types": memory_stats.get("memory_types", {}),
                    "storage_size": memory_stats.get("storage_size", "0 B")
                },
                "streaming_tts": {
                    "enabled": self.tts_enabled,
                    "status": tts_status
                },
                "reasoning_agent": {
                    "available": bool(self.reasoning_agent),
                    "sessions_completed": self.stats['autonomous_sessions']
                },
                "document_processor": {
                    "available": bool(self.document_processor),
                    "documents_processed": self.stats['documents_processed']
                },
                "file_system_crawler": {
                    "available": bool(self.fs_crawler),
                    "files_scanned": self.stats['files_scanned']
                },
                "app_launcher": {
                    "available": bool(self.app_launcher),
                    "apps_launched": self.stats['apps_launched']
                }
            },
            "statistics": self.stats,
            "base_system": super().get_simple_responses()  # Get base system info
        }
    
    def save_session(self, filename: str = None):
        """Save current session data"""
        if not filename:
            filename = f"yuvan_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.stats,
            "memory_stats": self.memory_system.get_memory_stats(),
            "system_status": self.get_system_status()
        }
        
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            return f"Session saved to {filename}"
        except Exception as e:
            return f"Error saving session: {str(e)}"
    
    def cleanup(self):
        """Cleanup all systems"""
        if self.streaming_tts:
            self.streaming_tts.stop_streaming()
        
        if hasattr(self, 'app_launcher') and self.app_launcher:
            self.app_launcher.stop_monitoring()
        
        print("Enhanced Yuvan systems cleaned up")

# Helper function to create enhanced task handler
def create_enhanced_yuvan(enable_tts: bool = True, scan_apps: bool = True) -> EnhancedTaskHandler:
    """Create and initialize enhanced Yuvan task handler"""
    print("Initializing Enhanced Yuvan AI Assistant...")
    
    handler = EnhancedTaskHandler()
    
    # Initialize TTS if requested
    if enable_tts:
        handler.initialize_streaming_tts(True)
    
    # Scan for applications if requested
    if scan_apps:
        print("Scanning for installed applications...")
        try:
            app_count = handler.app_launcher.scan_installed_applications()
            print(f"Found {app_count} applications")
        except Exception as e:
            print(f"Warning: Could not scan applications: {e}")
    
    print("Enhanced Yuvan initialized successfully!")
    return handler