"""
Terminal Assistant for Yuvan AI Assistant
Provides safe command parsing, execution, and system interaction capabilities
"""

import subprocess
import shlex
import os
import platform
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import psutil
import threading
import time

@dataclass
class CommandResult:
    """Represents the result of a command execution"""
    command: str
    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time: float
    timestamp: datetime

class TerminalAssistant:
    """Advanced terminal assistant with safe command execution"""
    
    def __init__(self):
        self.command_history: List[CommandResult] = []
        self.allowed_commands = self._get_safe_commands()
        self.restricted_commands = self._get_restricted_commands()
        self.current_directory = os.getcwd()
        self.environment_vars = os.environ.copy()
        
        # Command aliases for common operations
        self.aliases = {
            "ll": "ls -la",
            "la": "ls -a",
            "dir": "ls",
            "cls": "clear",
            "grep": "grep --color=auto"
        }
        
        # Platform-specific configurations
        self.platform = platform.system().lower()
        self._setup_platform_specific()
    
    def _get_safe_commands(self) -> Dict[str, Dict[str, Any]]:
        """Define safe commands that can be executed"""
        safe_commands = {
            # File operations
            "ls": {"description": "List directory contents", "risk": "low"},
            "pwd": {"description": "Print working directory", "risk": "low"},
            "cat": {"description": "Display file contents", "risk": "low"},
            "head": {"description": "Display first lines of file", "risk": "low"},
            "tail": {"description": "Display last lines of file", "risk": "low"},
            "find": {"description": "Search for files", "risk": "low"},
            "grep": {"description": "Search text patterns", "risk": "low"},
            "wc": {"description": "Count lines, words, characters", "risk": "low"},
            "sort": {"description": "Sort lines in text", "risk": "low"},
            "uniq": {"description": "Remove duplicate lines", "risk": "low"},
            
            # System information
            "ps": {"description": "Show running processes", "risk": "low"},
            "top": {"description": "Show system processes", "risk": "low"},
            "df": {"description": "Show disk usage", "risk": "low"},
            "du": {"description": "Show directory usage", "risk": "low"},
            "free": {"description": "Show memory usage", "risk": "low"},
            "uptime": {"description": "Show system uptime", "risk": "low"},
            "whoami": {"description": "Show current user", "risk": "low"},
            "id": {"description": "Show user and group IDs", "risk": "low"},
            
            # Text processing
            "echo": {"description": "Display text", "risk": "low"},
            "printf": {"description": "Format and print text", "risk": "low"},
            "cut": {"description": "Extract columns from text", "risk": "low"},
            "awk": {"description": "Text processing tool", "risk": "medium"},
            "sed": {"description": "Stream editor", "risk": "medium"},
            
            # Network (safe operations)
            "ping": {"description": "Test network connectivity", "risk": "low"},
            "wget": {"description": "Download files", "risk": "medium"},
            "curl": {"description": "Transfer data", "risk": "medium"},
            
            # Development tools
            "git": {"description": "Git version control", "risk": "medium"},
            "python": {"description": "Python interpreter", "risk": "medium"},
            "pip": {"description": "Python package manager", "risk": "medium"},
            "node": {"description": "Node.js runtime", "risk": "medium"},
            "npm": {"description": "Node package manager", "risk": "medium"},
        }
        
        # Add platform-specific commands
        if self.platform == "windows":
            safe_commands.update({
                "dir": {"description": "List directory contents", "risk": "low"},
                "type": {"description": "Display file contents", "risk": "low"},
                "systeminfo": {"description": "System information", "risk": "low"},
                "tasklist": {"description": "List running tasks", "risk": "low"},
            })
        
        return safe_commands
    
    def _get_restricted_commands(self) -> List[str]:
        """Define commands that are restricted for security"""
        return [
            # System modification
            "rm", "del", "rmdir", "rd",
            "mv", "move", "cp", "copy",
            "chmod", "chown", "attrib",
            "sudo", "su", "runas",
            
            # Network security risks
            "ssh", "scp", "ftp", "telnet",
            "nc", "netcat", "nmap",
            
            # System control
            "shutdown", "reboot", "halt",
            "service", "systemctl", "sc",
            "kill", "killall", "taskkill",
            
            # Package managers (system-wide)
            "apt", "yum", "dnf", "pacman",
            "brew", "choco",
            
            # Disk operations
            "fdisk", "mkfs", "format",
            "mount", "umount",
            
            # Process manipulation
            "nohup", "disown", "jobs",
            "bg", "fg",
        ]
    
    def _setup_platform_specific(self):
        """Setup platform-specific configurations"""
        if self.platform == "windows":
            self.shell = True
            self.command_prefix = "cmd /c"
        else:
            self.shell = False
            self.command_prefix = ""
    
    def parse_command(self, user_input: str) -> Tuple[str, List[str], Dict[str, Any]]:
        """Parse user input into command, arguments, and metadata"""
        # Clean the input
        user_input = user_input.strip()
        
        # Handle aliases
        for alias, actual_command in self.aliases.items():
            if user_input.startswith(alias + " ") or user_input == alias:
                user_input = user_input.replace(alias, actual_command, 1)
        
        # Parse the command
        try:
            parts = shlex.split(user_input)
            command = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []
        except ValueError:
            # Handle unmatched quotes
            parts = user_input.split()
            command = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []
        
        # Extract metadata
        metadata = {
            "original_input": user_input,
            "is_piped": "|" in user_input,
            "has_redirection": ">" in user_input or "<" in user_input,
            "is_background": user_input.endswith("&"),
            "estimated_risk": self._assess_command_risk(command, args)
        }
        
        return command, args, metadata
    
    def _assess_command_risk(self, command: str, args: List[str]) -> str:
        """Assess the risk level of a command"""
        if command in self.restricted_commands:
            return "high"
        elif command in self.allowed_commands:
            return self.allowed_commands[command].get("risk", "medium")
        else:
            return "unknown"
    
    def can_execute_command(self, command: str, args: List[str] = None) -> Tuple[bool, str]:
        """Check if a command can be executed safely"""
        args = args or []
        
        # Check if command is restricted
        if command in self.restricted_commands:
            return False, f"Command '{command}' is restricted for security reasons"
        
        # Check for dangerous argument patterns
        dangerous_patterns = [
            r"--exec",
            r"-e\s+",
            r"eval",
            r"system\s*\(",
            r"exec\s*\(",
            r"\$\(",
            r"`.*`",
        ]
        
        full_command = f"{command} {' '.join(args)}"
        for pattern in dangerous_patterns:
            if re.search(pattern, full_command, re.IGNORECASE):
                return False, f"Command contains potentially dangerous pattern: {pattern}"
        
        # Check for file system operations outside allowed directories
        if command in ["rm", "del", "mv", "move", "cp", "copy"]:
            return False, "File modification commands are restricted"
        
        # Additional checks for specific commands
        if command == "python" or command == "python3":
            # Check for dangerous Python operations
            if any("-c" in arg or "exec" in arg or "eval" in arg for arg in args):
                return False, "Python code execution is restricted"
        
        return True, "Command is safe to execute"
    
    def execute_command(self, command: str, args: List[str] = None, 
                       timeout: int = 30, capture_output: bool = True) -> CommandResult:
        """Execute a command safely with proper error handling"""
        args = args or []
        full_command = f"{command} {' '.join(args)}"
        
        # Check if command can be executed
        can_execute, reason = self.can_execute_command(command, args)
        if not can_execute:
            return CommandResult(
                command=full_command,
                success=False,
                stdout="",
                stderr=reason,
                return_code=-1,
                execution_time=0.0,
                timestamp=datetime.now()
            )
        
        start_time = time.time()
        
        try:
            # Prepare the command for execution
            if self.platform == "windows":
                cmd_list = full_command
                shell = True
            else:
                cmd_list = [command] + args
                shell = False
            
            # Execute the command
            result = subprocess.run(
                cmd_list,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.current_directory,
                env=self.environment_vars
            )
            
            execution_time = time.time() - start_time
            
            command_result = CommandResult(
                command=full_command,
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            command_result = CommandResult(
                command=full_command,
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                return_code=-1,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            command_result = CommandResult(
                command=full_command,
                success=False,
                stdout="",
                stderr=f"Error executing command: {str(e)}",
                return_code=-1,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
        
        # Store in history
        self.command_history.append(command_result)
        
        return command_result
    
    def execute_command_from_text(self, user_input: str) -> CommandResult:
        """Parse and execute a command from text input"""
        command, args, metadata = self.parse_command(user_input)
        
        if not command:
            return CommandResult(
                command=user_input,
                success=False,
                stdout="",
                stderr="No command specified",
                return_code=-1,
                execution_time=0.0,
                timestamp=datetime.now()
            )
        
        return self.execute_command(command, args)
    
    def get_command_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions based on partial input"""
        suggestions = []
        
        # Search in allowed commands
        for cmd in self.allowed_commands.keys():
            if cmd.startswith(partial_command.lower()):
                suggestions.append(cmd)
        
        # Search in aliases
        for alias in self.aliases.keys():
            if alias.startswith(partial_command.lower()):
                suggestions.append(alias)
        
        return sorted(suggestions)
    
    def get_command_help(self, command: str) -> str:
        """Get help information for a command"""
        if command in self.allowed_commands:
            info = self.allowed_commands[command]
            help_text = f"Command: {command}\n"
            help_text += f"Description: {info['description']}\n"
            help_text += f"Risk Level: {info['risk']}\n"
            
            # Try to get man page or help
            try:
                if self.platform == "windows":
                    help_result = subprocess.run(
                        f"{command} /?",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                else:
                    help_result = subprocess.run(
                        [command, "--help"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                
                if help_result.returncode == 0:
                    help_text += f"\nCommand Help:\n{help_result.stdout[:500]}..."
                    
            except Exception:
                pass
            
            return help_text
        else:
            return f"Command '{command}' is not available or is restricted"
    
    def change_directory(self, path: str) -> bool:
        """Safely change working directory"""
        try:
            # Resolve the path
            new_path = os.path.expanduser(path)
            new_path = os.path.abspath(new_path)
            
            # Security check - prevent going to restricted directories
            restricted_dirs = ["/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin"]
            if any(new_path.startswith(restricted) for restricted in restricted_dirs):
                return False
            
            if os.path.exists(new_path) and os.path.isdir(new_path):
                self.current_directory = new_path
                os.chdir(new_path)
                return True
            else:
                return False
        except Exception:
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "current_directory": self.current_directory,
            "python_version": platform.python_version(),
        }
        
        # Add memory and CPU info
        try:
            info["memory"] = {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            }
            info["cpu"] = {
                "count": psutil.cpu_count(),
                "usage": psutil.cpu_percent(interval=1)
            }
            info["disk"] = {
                "total": psutil.disk_usage('/').total if os.name != 'nt' else psutil.disk_usage('C:\\').total,
                "free": psutil.disk_usage('/').free if os.name != 'nt' else psutil.disk_usage('C:\\').free,
                "percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
            }
        except Exception:
            pass
        
        return info
    
    def get_command_history(self, limit: int = 10) -> List[CommandResult]:
        """Get recent command history"""
        return self.command_history[-limit:]
    
    def clear_history(self):
        """Clear command history"""
        self.command_history = []
    
    def format_command_result(self, result: CommandResult) -> str:
        """Format command result for display"""
        output = f"Command: {result.command}\n"
        output += f"Status: {'Success' if result.success else 'Failed'}\n"
        output += f"Exit Code: {result.return_code}\n"
        output += f"Execution Time: {result.execution_time:.2f}s\n"
        
        if result.stdout:
            output += f"\nOutput:\n{result.stdout}\n"
        
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}\n"
        
        return output
    
    def get_available_commands(self) -> Dict[str, str]:
        """Get list of available commands with descriptions"""
        return {cmd: info["description"] for cmd, info in self.allowed_commands.items()}
    
    def is_command_safe(self, command: str) -> bool:
        """Quick check if a command is considered safe"""
        return command in self.allowed_commands and command not in self.restricted_commands