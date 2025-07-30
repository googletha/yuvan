"""
Application Launcher/Controller for Yuvan AI Assistant
Provides OS-level application management - launching, closing, and monitoring apps
"""

import os
import sys
import subprocess
import platform
import time
import psutil
import signal
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import threading
import json
import re
import shutil

# Platform-specific imports
if platform.system() == "Windows":
    import winreg
    import win32gui
    import win32con
    import win32process
elif platform.system() == "Darwin":  # macOS
    import plistlib
elif platform.system() == "Linux":
    import subprocess

@dataclass
class AppInfo:
    """Information about an installed application"""
    name: str
    path: str
    executable: str
    version: str = ""
    description: str = ""
    icon_path: str = ""
    categories: List[str] = None
    is_running: bool = False
    pid: Optional[int] = None

@dataclass
class RunningApp:
    """Information about a running application"""
    pid: int
    name: str
    executable: str
    command_line: str
    memory_usage: int
    cpu_percent: float
    start_time: datetime
    status: str

class ApplicationLauncher:
    """Cross-platform application launcher and manager"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.installed_apps: Dict[str, AppInfo] = {}
        self.running_apps: Dict[int, RunningApp] = {}
        
        # Platform-specific configurations
        self.app_directories = self._get_app_directories()
        self.executable_extensions = self._get_executable_extensions()
        
        # Application cache
        self.apps_cache_file = "yuvan_apps_cache.json"
        
        # Load applications
        self._load_apps_cache()
        
        # Monitoring
        self.monitor_thread = None
        self.monitoring = False
    
    def _get_app_directories(self) -> List[str]:
        """Get platform-specific application directories"""
        if self.platform == "windows":
            return [
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                os.path.expanduser("~\\AppData\\Local\\Programs"),
                os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs")
            ]
        elif self.platform == "darwin":
            return [
                "/Applications",
                "/System/Applications",
                os.path.expanduser("~/Applications"),
                "/usr/local/bin",
                "/opt/homebrew/bin"
            ]
        else:  # Linux
            return [
                "/usr/bin",
                "/usr/local/bin",
                "/opt",
                "/snap/bin",
                "/var/lib/flatpak/exports/bin",
                os.path.expanduser("~/.local/bin"),
                os.path.expanduser("~/Applications"),
                "/usr/share/applications"
            ]
    
    def _get_executable_extensions(self) -> List[str]:
        """Get platform-specific executable extensions"""
        if self.platform == "windows":
            return [".exe", ".bat", ".cmd", ".com", ".scr", ".msi"]
        else:
            return [""]  # No extensions needed on Unix-like systems
    
    def scan_installed_applications(self, force_refresh: bool = False) -> int:
        """Scan for installed applications"""
        if not force_refresh and self.installed_apps:
            return len(self.installed_apps)
        
        self.installed_apps.clear()
        
        if self.platform == "windows":
            self._scan_windows_apps()
        elif self.platform == "darwin":
            self._scan_macos_apps()
        else:
            self._scan_linux_apps()
        
        # Save to cache
        self._save_apps_cache()
        
        return len(self.installed_apps)
    
    def _scan_windows_apps(self):
        """Scan for Windows applications"""
        # Scan Program Files directories
        for app_dir in self.app_directories:
            if os.path.exists(app_dir):
                self._scan_directory_for_apps(app_dir)
        
        # Scan Windows Registry for installed programs
        self._scan_windows_registry()
    
    def _scan_macos_apps(self):
        """Scan for macOS applications"""
        for app_dir in self.app_directories:
            if os.path.exists(app_dir):
                if app_dir.endswith("Applications"):
                    # Scan .app bundles
                    self._scan_macos_app_bundles(app_dir)
                else:
                    # Scan for executables
                    self._scan_directory_for_apps(app_dir)
    
    def _scan_linux_apps(self):
        """Scan for Linux applications"""
        # Scan .desktop files
        desktop_dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications")
        ]
        
        for desktop_dir in desktop_dirs:
            if os.path.exists(desktop_dir):
                self._scan_linux_desktop_files(desktop_dir)
        
        # Scan executable directories
        for app_dir in self.app_directories:
            if os.path.exists(app_dir) and "applications" not in app_dir:
                self._scan_directory_for_apps(app_dir)
    
    def _scan_directory_for_apps(self, directory: str, max_depth: int = 3):
        """Recursively scan directory for executable files"""
        if max_depth <= 0:
            return
        
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                if os.path.isfile(item_path):
                    if self._is_executable_file(item_path):
                        app_info = self._create_app_info_from_executable(item_path)
                        if app_info:
                            self.installed_apps[app_info.name.lower()] = app_info
                
                elif os.path.isdir(item_path) and not item.startswith('.'):
                    self._scan_directory_for_apps(item_path, max_depth - 1)
                    
        except (PermissionError, OSError):
            pass
    
    def _scan_windows_registry(self):
        """Scan Windows registry for installed applications"""
        if self.platform != "windows":
            return
        
        try:
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hive, path in registry_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    i = 0
                    
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            app_info = self._extract_app_info_from_registry(subkey)
                            if app_info:
                                self.installed_apps[app_info.name.lower()] = app_info
                            
                            winreg.CloseKey(subkey)
                            i += 1
                            
                        except OSError:
                            break
                    
                    winreg.CloseKey(key)
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error scanning Windows registry: {e}")
    
    def _scan_macos_app_bundles(self, directory: str):
        """Scan macOS .app bundles"""
        try:
            for item in os.listdir(directory):
                if item.endswith('.app'):
                    app_path = os.path.join(directory, item)
                    app_info = self._create_app_info_from_macos_bundle(app_path)
                    if app_info:
                        self.installed_apps[app_info.name.lower()] = app_info
        except (PermissionError, OSError):
            pass
    
    def _scan_linux_desktop_files(self, directory: str):
        """Scan Linux .desktop files"""
        try:
            for item in os.listdir(directory):
                if item.endswith('.desktop'):
                    desktop_file = os.path.join(directory, item)
                    app_info = self._create_app_info_from_desktop_file(desktop_file)
                    if app_info:
                        self.installed_apps[app_info.name.lower()] = app_info
        except (PermissionError, OSError):
            pass
    
    def _is_executable_file(self, file_path: str) -> bool:
        """Check if file is executable"""
        if self.platform == "windows":
            return any(file_path.lower().endswith(ext) for ext in self.executable_extensions)
        else:
            return os.access(file_path, os.X_OK) and os.path.isfile(file_path)
    
    def _create_app_info_from_executable(self, executable_path: str) -> Optional[AppInfo]:
        """Create AppInfo from executable file"""
        try:
            name = os.path.splitext(os.path.basename(executable_path))[0]
            
            # Skip system files and common utilities
            skip_names = ['cmd', 'powershell', 'bash', 'sh', 'python', 'node', 'java']
            if name.lower() in skip_names:
                return None
            
            return AppInfo(
                name=name,
                path=os.path.dirname(executable_path),
                executable=executable_path,
                description=f"Executable: {name}"
            )
            
        except Exception:
            return None
    
    def _extract_app_info_from_registry(self, registry_key) -> Optional[AppInfo]:
        """Extract app info from Windows registry key"""
        try:
            display_name = winreg.QueryValueEx(registry_key, "DisplayName")[0]
            
            try:
                install_location = winreg.QueryValueEx(registry_key, "InstallLocation")[0]
            except FileNotFoundError:
                install_location = ""
            
            try:
                executable = winreg.QueryValueEx(registry_key, "DisplayIcon")[0]
                if ',' in executable:
                    executable = executable.split(',')[0]
            except FileNotFoundError:
                executable = ""
            
            try:
                version = winreg.QueryValueEx(registry_key, "DisplayVersion")[0]
            except FileNotFoundError:
                version = ""
            
            return AppInfo(
                name=display_name,
                path=install_location,
                executable=executable,
                version=version,
                description=f"Installed application: {display_name}"
            )
            
        except Exception:
            return None
    
    def _create_app_info_from_macos_bundle(self, app_path: str) -> Optional[AppInfo]:
        """Create AppInfo from macOS app bundle"""
        try:
            name = os.path.splitext(os.path.basename(app_path))[0]
            info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
            
            version = ""
            description = ""
            
            if os.path.exists(info_plist_path):
                try:
                    with open(info_plist_path, 'rb') as f:
                        plist_data = plistlib.load(f)
                    
                    version = plist_data.get('CFBundleShortVersionString', '')
                    description = plist_data.get('CFBundleGetInfoString', '')
                    
                except Exception:
                    pass
            
            return AppInfo(
                name=name,
                path=app_path,
                executable=app_path,
                version=version,
                description=description or f"macOS application: {name}"
            )
            
        except Exception:
            return None
    
    def _create_app_info_from_desktop_file(self, desktop_file: str) -> Optional[AppInfo]:
        """Create AppInfo from Linux .desktop file"""
        try:
            with open(desktop_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse desktop file
            name = ""
            executable = ""
            description = ""
            categories = []
            icon = ""
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('Name='):
                    name = line[5:]
                elif line.startswith('Exec='):
                    executable = line[5:].split()[0]  # Get first part (executable)
                elif line.startswith('Comment='):
                    description = line[8:]
                elif line.startswith('Categories='):
                    categories = line[11:].split(';')
                elif line.startswith('Icon='):
                    icon = line[5:]
            
            if name and executable:
                return AppInfo(
                    name=name,
                    path=os.path.dirname(desktop_file),
                    executable=executable,
                    description=description,
                    icon_path=icon,
                    categories=categories
                )
                
        except Exception:
            pass
        
        return None
    
    def launch_application(self, app_name: str, args: List[str] = None) -> Dict[str, Any]:
        """Launch an application"""
        args = args or []
        
        # Find the application
        app_info = self.find_application(app_name)
        if not app_info:
            return {
                'success': False,
                'error': f"Application '{app_name}' not found",
                'suggestions': self.suggest_similar_apps(app_name)
            }
        
        try:
            if self.platform == "windows":
                result = self._launch_windows_app(app_info, args)
            elif self.platform == "darwin":
                result = self._launch_macos_app(app_info, args)
            else:
                result = self._launch_linux_app(app_info, args)
            
            if result['success']:
                # Update running apps
                self.update_running_apps()
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to launch {app_name}: {str(e)}"
            }
    
    def _launch_windows_app(self, app_info: AppInfo, args: List[str]) -> Dict[str, Any]:
        """Launch Windows application"""
        cmd = [app_info.executable] + args
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=app_info.path or None,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return {
                'success': True,
                'pid': process.pid,
                'message': f"Launched {app_info.name}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _launch_macos_app(self, app_info: AppInfo, args: List[str]) -> Dict[str, Any]:
        """Launch macOS application"""
        if app_info.executable.endswith('.app'):
            # Use 'open' command for .app bundles
            cmd = ['open', app_info.executable] + args
        else:
            cmd = [app_info.executable] + args
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return {
                'success': True,
                'pid': process.pid,
                'message': f"Launched {app_info.name}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _launch_linux_app(self, app_info: AppInfo, args: List[str]) -> Dict[str, Any]:
        """Launch Linux application"""
        executable = app_info.executable
        
        # Handle desktop file executables
        if not os.path.isabs(executable):
            executable = shutil.which(executable)
            if not executable:
                return {
                    'success': False,
                    'error': f"Executable '{app_info.executable}' not found in PATH"
                }
        
        cmd = [executable] + args
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid  # Start new process group
            )
            
            return {
                'success': True,
                'pid': process.pid,
                'message': f"Launched {app_info.name}"
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def close_application(self, app_identifier: str, force: bool = False) -> Dict[str, Any]:
        """Close an application by name or PID"""
        # Try to parse as PID first
        try:
            pid = int(app_identifier)
            return self._close_app_by_pid(pid, force)
        except ValueError:
            # It's an app name
            return self._close_app_by_name(app_identifier, force)
    
    def _close_app_by_pid(self, pid: int, force: bool = False) -> Dict[str, Any]:
        """Close application by PID"""
        try:
            process = psutil.Process(pid)
            app_name = process.name()
            
            if force:
                process.kill()
                action = "killed"
            else:
                process.terminate()
                action = "terminated"
            
            return {
                'success': True,
                'message': f"Successfully {action} {app_name} (PID: {pid})"
            }
            
        except psutil.NoSuchProcess:
            return {
                'success': False,
                'error': f"Process with PID {pid} not found"
            }
        except psutil.AccessDenied:
            return {
                'success': False,
                'error': f"Access denied to close process with PID {pid}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error closing process: {str(e)}"
            }
    
    def _close_app_by_name(self, app_name: str, force: bool = False) -> Dict[str, Any]:
        """Close application by name"""
        matching_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if (app_name.lower() in proc.info['name'].lower() or
                    (proc.info['exe'] and app_name.lower() in os.path.basename(proc.info['exe']).lower())):
                    matching_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not matching_processes:
            return {
                'success': False,
                'error': f"No running processes found matching '{app_name}'"
            }
        
        closed_count = 0
        errors = []
        
        for proc in matching_processes:
            try:
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                closed_count += 1
            except Exception as e:
                errors.append(f"PID {proc.pid}: {str(e)}")
        
        if closed_count > 0:
            return {
                'success': True,
                'message': f"Closed {closed_count} process(es) matching '{app_name}'",
                'errors': errors if errors else None
            }
        else:
            return {
                'success': False,
                'error': f"Failed to close any processes: {'; '.join(errors)}"
            }
    
    def find_application(self, app_name: str) -> Optional[AppInfo]:
        """Find an application by name (case-insensitive, partial match)"""
        app_name_lower = app_name.lower()
        
        # Exact match first
        if app_name_lower in self.installed_apps:
            return self.installed_apps[app_name_lower]
        
        # Partial match
        for name, app_info in self.installed_apps.items():
            if app_name_lower in name or app_name_lower in app_info.name.lower():
                return app_info
        
        return None
    
    def suggest_similar_apps(self, app_name: str, limit: int = 5) -> List[str]:
        """Suggest similar application names"""
        suggestions = []
        app_name_lower = app_name.lower()
        
        for name, app_info in self.installed_apps.items():
            if any(word in name for word in app_name_lower.split()):
                suggestions.append(app_info.name)
        
        return suggestions[:limit]
    
    def get_running_applications(self) -> List[RunningApp]:
        """Get list of currently running applications"""
        self.update_running_apps()
        return list(self.running_apps.values())
    
    def update_running_apps(self):
        """Update the list of running applications"""
        self.running_apps.clear()
        
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'memory_info', 'cpu_percent', 'create_time', 'status']):
            try:
                proc_info = proc.info
                
                # Skip system processes and those without names
                if not proc_info['name'] or proc_info['name'] in ['System', 'Registry', 'csrss.exe']:
                    continue
                
                running_app = RunningApp(
                    pid=proc_info['pid'],
                    name=proc_info['name'],
                    executable=proc_info['exe'] or '',
                    command_line=' '.join(proc_info['cmdline']) if proc_info['cmdline'] else '',
                    memory_usage=proc_info['memory_info'].rss if proc_info['memory_info'] else 0,
                    cpu_percent=proc_info['cpu_percent'] or 0.0,
                    start_time=datetime.fromtimestamp(proc_info['create_time']),
                    status=proc_info['status']
                )
                
                self.running_apps[proc_info['pid']] = running_app
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    
    def get_application_info(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an application"""
        app_info = self.find_application(app_name)
        if not app_info:
            return None
        
        # Check if app is running
        is_running = False
        running_pids = []
        
        for running_app in self.running_apps.values():
            if (app_name.lower() in running_app.name.lower() or
                app_name.lower() in os.path.basename(running_app.executable).lower()):
                is_running = True
                running_pids.append(running_app.pid)
        
        return {
            'name': app_info.name,
            'path': app_info.path,
            'executable': app_info.executable,
            'version': app_info.version,
            'description': app_info.description,
            'categories': app_info.categories or [],
            'is_running': is_running,
            'running_pids': running_pids
        }
    
    def list_installed_applications(self, category: str = None) -> List[Dict[str, str]]:
        """List all installed applications"""
        apps = []
        
        for app_info in self.installed_apps.values():
            if category and app_info.categories:
                if not any(category.lower() in cat.lower() for cat in app_info.categories):
                    continue
            
            apps.append({
                'name': app_info.name,
                'executable': app_info.executable,
                'version': app_info.version,
                'description': app_info.description
            })
        
        return sorted(apps, key=lambda x: x['name'].lower())
    
    def start_monitoring(self):
        """Start monitoring running applications"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring running applications"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_worker(self):
        """Worker thread for monitoring applications"""
        while self.monitoring:
            self.update_running_apps()
            time.sleep(5)  # Update every 5 seconds
    
    def _load_apps_cache(self):
        """Load applications cache from file"""
        try:
            if os.path.exists(self.apps_cache_file):
                with open(self.apps_cache_file, 'r') as f:
                    data = json.load(f)
                
                for app_data in data.get('applications', []):
                    app_info = AppInfo(**app_data)
                    self.installed_apps[app_info.name.lower()] = app_info
                    
        except Exception as e:
            print(f"Error loading apps cache: {e}")
    
    def _save_apps_cache(self):
        """Save applications cache to file"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'platform': self.platform,
                'applications': [
                    {
                        'name': app.name,
                        'path': app.path,
                        'executable': app.executable,
                        'version': app.version,
                        'description': app.description,
                        'icon_path': app.icon_path,
                        'categories': app.categories or []
                    }
                    for app in self.installed_apps.values()
                ]
            }
            
            with open(self.apps_cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving apps cache: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics related to applications"""
        self.update_running_apps()
        
        total_memory = sum(app.memory_usage for app in self.running_apps.values())
        total_processes = len(self.running_apps)
        
        return {
            'installed_applications': len(self.installed_apps),
            'running_processes': total_processes,
            'total_memory_usage': total_memory,
            'total_memory_usage_mb': total_memory / (1024 * 1024),
            'top_memory_apps': sorted(
                self.running_apps.values(),
                key=lambda x: x.memory_usage,
                reverse=True
            )[:5],
            'top_cpu_apps': sorted(
                [app for app in self.running_apps.values() if app.cpu_percent > 0],
                key=lambda x: x.cpu_percent,
                reverse=True
            )[:5]
        }