"""
File System Crawler for Yuvan AI Assistant
Provides advanced file system analysis, duplicate detection, and cleanup suggestions
"""

import os
import hashlib
import mimetypes
import stat
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import fnmatch
import json
import shutil

# Additional libraries for file analysis
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

@dataclass
class FileInfo:
    """Comprehensive file information"""
    path: str
    name: str
    size: int
    creation_time: datetime
    modification_time: datetime
    access_time: datetime
    file_type: str
    mime_type: str
    hash_md5: Optional[str] = None
    hash_sha256: Optional[str] = None
    permissions: str = ""
    is_hidden: bool = False
    is_symlink: bool = False
    extension: str = ""

@dataclass
class DuplicateGroup:
    """Group of duplicate files"""
    files: List[FileInfo]
    total_size: int
    potential_savings: int
    confidence: float

@dataclass
class CleanupSuggestion:
    """Cleanup suggestion for files"""
    suggestion_type: str  # 'duplicate', 'large', 'old', 'temporary', 'empty'
    files: List[FileInfo]
    reason: str
    potential_savings: int
    confidence: float
    action: str  # 'delete', 'move', 'compress'

class FileSystemCrawler:
    """Advanced file system crawler with analysis capabilities"""
    
    def __init__(self, exclude_system_dirs: bool = True):
        self.exclude_system_dirs = exclude_system_dirs
        
        # File analysis cache
        self.file_cache: Dict[str, FileInfo] = {}
        self.hash_cache: Dict[str, str] = {}
        
        # Analysis results
        self.duplicates: List[DuplicateGroup] = []
        self.cleanup_suggestions: List[CleanupSuggestion] = []
        self.large_files: List[FileInfo] = []
        self.old_files: List[FileInfo] = []
        
        # Configuration
        self.large_file_threshold = 100 * 1024 * 1024  # 100MB
        self.old_file_threshold = 365  # days
        self.duplicate_min_size = 1024  # 1KB
        
        # System directories to exclude
        self.system_dirs = {
            '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/lib', '/lib64',
            '/proc', '/sys', '/dev', '/run', '/var/run', '/var/lock',
            'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
            '/System', '/Library', '/Applications'
        }
        
        # Temporary file patterns
        self.temp_patterns = [
            '*.tmp', '*.temp', '*.log', '*.cache', '*~', '*.bak',
            '*.old', '*.orig', '*.swp', '.DS_Store', 'Thumbs.db',
            '*.pid', '*.lock', '*.pyc', '__pycache__'
        ]
        
        # Threading
        self.stop_crawling = False
        self.crawl_progress = 0
        self.total_files_found = 0
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'total_directories': 0,
            'total_size': 0,
            'file_types': {},
            'largest_files': [],
            'oldest_files': [],
            'scan_time': 0
        }
    
    def crawl_directory(self, root_path: str, max_depth: Optional[int] = None,
                       calculate_hashes: bool = False, follow_symlinks: bool = False) -> Dict[str, Any]:
        """Crawl a directory and analyze its contents"""
        start_time = time.time()
        self.stop_crawling = False
        self.crawl_progress = 0
        self.total_files_found = 0
        
        root_path = os.path.abspath(root_path)
        
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Path does not exist: {root_path}")
        
        if not os.path.isdir(root_path):
            raise ValueError(f"Path is not a directory: {root_path}")
        
        # Clear previous results
        self.file_cache.clear()
        self.duplicates.clear()
        self.cleanup_suggestions.clear()
        self.large_files.clear()
        self.old_files.clear()
        
        try:
            # Start crawling
            self._crawl_recursive(root_path, 0, max_depth, calculate_hashes, follow_symlinks)
            
            # Analyze results
            self._analyze_duplicates()
            self._analyze_large_files()
            self._analyze_old_files()
            self._generate_cleanup_suggestions()
            
            # Update statistics
            scan_time = time.time() - start_time
            self._update_statistics(scan_time)
            
            return {
                'files_found': len(self.file_cache),
                'duplicates_found': len(self.duplicates),
                'cleanup_suggestions': len(self.cleanup_suggestions),
                'scan_time': scan_time,
                'total_size': self.stats['total_size']
            }
            
        except Exception as e:
            raise Exception(f"Error during crawling: {str(e)}")
    
    def _crawl_recursive(self, current_path: str, current_depth: int, 
                        max_depth: Optional[int], calculate_hashes: bool, 
                        follow_symlinks: bool):
        """Recursively crawl directories"""
        if self.stop_crawling:
            return
        
        if max_depth is not None and current_depth >= max_depth:
            return
        
        # Skip system directories if configured
        if self.exclude_system_dirs and self._is_system_directory(current_path):
            return
        
        try:
            entries = os.listdir(current_path)
        except (PermissionError, OSError):
            return
        
        for entry in entries:
            if self.stop_crawling:
                break
            
            entry_path = os.path.join(current_path, entry)
            
            try:
                # Get file stats
                if follow_symlinks:
                    file_stat = os.stat(entry_path)
                else:
                    file_stat = os.lstat(entry_path)
                
                if stat.S_ISDIR(file_stat.st_mode):
                    # Directory
                    self.stats['total_directories'] += 1
                    
                    if not os.path.islink(entry_path) or follow_symlinks:
                        self._crawl_recursive(
                            entry_path, current_depth + 1, max_depth, 
                            calculate_hashes, follow_symlinks
                        )
                
                elif stat.S_ISREG(file_stat.st_mode):
                    # Regular file
                    file_info = self._analyze_file(entry_path, file_stat, calculate_hashes)
                    self.file_cache[entry_path] = file_info
                    self.total_files_found += 1
                    
                    # Update progress (rough estimate)
                    if self.total_files_found % 100 == 0:
                        self.crawl_progress = min(90, self.total_files_found // 10)
                
            except (PermissionError, OSError, UnicodeDecodeError):
                continue
    
    def _analyze_file(self, file_path: str, file_stat: os.stat_result, 
                     calculate_hashes: bool) -> FileInfo:
        """Analyze a single file and extract information"""
        file_info = FileInfo(
            path=file_path,
            name=os.path.basename(file_path),
            size=file_stat.st_size,
            creation_time=datetime.fromtimestamp(file_stat.st_ctime),
            modification_time=datetime.fromtimestamp(file_stat.st_mtime),
            access_time=datetime.fromtimestamp(file_stat.st_atime),
            file_type=self._detect_file_type(file_path),
            mime_type=self._get_mime_type(file_path),
            permissions=stat.filemode(file_stat.st_mode),
            is_hidden=os.path.basename(file_path).startswith('.'),
            is_symlink=os.path.islink(file_path),
            extension=Path(file_path).suffix.lower()
        )
        
        # Calculate hashes if requested and file is not too large
        if calculate_hashes and file_stat.st_size < 100 * 1024 * 1024:  # 100MB limit
            try:
                file_info.hash_md5 = self._calculate_file_hash(file_path, 'md5')
                if file_stat.st_size < 10 * 1024 * 1024:  # 10MB limit for SHA256
                    file_info.hash_sha256 = self._calculate_file_hash(file_path, 'sha256')
            except Exception:
                pass
        
        return file_info
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type using various methods"""
        # Try magic library first
        if MAGIC_AVAILABLE:
            try:
                return magic.from_file(file_path)
            except Exception:
                pass
        
        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return mime_type
        
        # Fallback to extension-based detection
        ext = Path(file_path).suffix.lower()
        ext_types = {
            '.txt': 'text/plain',
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.html': 'text/html',
            '.css': 'text/css',
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.jpg': 'image/jpeg',
            '.png': 'image/png',
            '.mp4': 'video/mp4',
            '.mp3': 'audio/mpeg'
        }
        
        return ext_types.get(ext, 'application/octet-stream')
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type of file"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def _calculate_file_hash(self, file_path: str, hash_type: str = 'md5') -> str:
        """Calculate file hash"""
        if hash_type == 'md5':
            hash_obj = hashlib.md5()
        elif hash_type == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported hash type: {hash_type}")
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return ""
    
    def _is_system_directory(self, path: str) -> bool:
        """Check if path is a system directory"""
        abs_path = os.path.abspath(path)
        
        for sys_dir in self.system_dirs:
            if abs_path.startswith(sys_dir):
                return True
        
        return False
    
    def _analyze_duplicates(self):
        """Find duplicate files based on size and hash"""
        if not self.file_cache:
            return
        
        # Group files by size first (quick filter)
        size_groups: Dict[int, List[FileInfo]] = {}
        
        for file_info in self.file_cache.values():
            if file_info.size >= self.duplicate_min_size:
                if file_info.size not in size_groups:
                    size_groups[file_info.size] = []
                size_groups[file_info.size].append(file_info)
        
        # Check groups with multiple files
        for size, files in size_groups.items():
            if len(files) > 1:
                # Group by hash if available
                if any(f.hash_md5 for f in files):
                    hash_groups: Dict[str, List[FileInfo]] = {}
                    
                    for file_info in files:
                        if file_info.hash_md5:
                            if file_info.hash_md5 not in hash_groups:
                                hash_groups[file_info.hash_md5] = []
                            hash_groups[file_info.hash_md5].append(file_info)
                    
                    # Create duplicate groups
                    for hash_key, duplicate_files in hash_groups.items():
                        if len(duplicate_files) > 1:
                            total_size = sum(f.size for f in duplicate_files)
                            savings = total_size - duplicate_files[0].size  # Keep one copy
                            
                            duplicate_group = DuplicateGroup(
                                files=duplicate_files,
                                total_size=total_size,
                                potential_savings=savings,
                                confidence=0.95  # High confidence with hash match
                            )
                            self.duplicates.append(duplicate_group)
                else:
                    # Size-only matching (lower confidence)
                    if len(files) > 1:
                        total_size = sum(f.size for f in files)
                        savings = total_size - files[0].size
                        
                        duplicate_group = DuplicateGroup(
                            files=files,
                            total_size=total_size,
                            potential_savings=savings,
                            confidence=0.7  # Lower confidence without hash
                        )
                        self.duplicates.append(duplicate_group)
    
    def _analyze_large_files(self):
        """Find large files that might need attention"""
        self.large_files = [
            file_info for file_info in self.file_cache.values()
            if file_info.size >= self.large_file_threshold
        ]
        
        # Sort by size descending
        self.large_files.sort(key=lambda f: f.size, reverse=True)
    
    def _analyze_old_files(self):
        """Find old files that haven't been accessed recently"""
        cutoff_date = datetime.now() - timedelta(days=self.old_file_threshold)
        
        self.old_files = [
            file_info for file_info in self.file_cache.values()
            if file_info.access_time < cutoff_date and file_info.modification_time < cutoff_date
        ]
        
        # Sort by modification time
        self.old_files.sort(key=lambda f: f.modification_time)
    
    def _generate_cleanup_suggestions(self):
        """Generate cleanup suggestions based on analysis"""
        self.cleanup_suggestions.clear()
        
        # Duplicate file suggestions
        for duplicate_group in self.duplicates:
            if duplicate_group.potential_savings > 0:
                suggestion = CleanupSuggestion(
                    suggestion_type='duplicate',
                    files=duplicate_group.files[1:],  # Keep first, suggest removing others
                    reason=f"Duplicate files found, can save {self._format_size(duplicate_group.potential_savings)}",
                    potential_savings=duplicate_group.potential_savings,
                    confidence=duplicate_group.confidence,
                    action='delete'
                )
                self.cleanup_suggestions.append(suggestion)
        
        # Large file suggestions
        very_large_files = [f for f in self.large_files if f.size > 500 * 1024 * 1024]  # 500MB
        if very_large_files:
            suggestion = CleanupSuggestion(
                suggestion_type='large',
                files=very_large_files[:10],  # Top 10
                reason="Very large files that might be candidates for compression or archival",
                potential_savings=sum(f.size for f in very_large_files[:10]) // 2,  # Estimate 50% compression
                confidence=0.6,
                action='compress'
            )
            self.cleanup_suggestions.append(suggestion)
        
        # Old file suggestions
        very_old_files = [f for f in self.old_files if 
                         (datetime.now() - f.modification_time).days > 730]  # 2 years
        if very_old_files:
            suggestion = CleanupSuggestion(
                suggestion_type='old',
                files=very_old_files[:20],  # Top 20
                reason="Very old files that haven't been modified in over 2 years",
                potential_savings=sum(f.size for f in very_old_files[:20]),
                confidence=0.5,
                action='move'
            )
            self.cleanup_suggestions.append(suggestion)
        
        # Temporary file suggestions
        temp_files = self._find_temporary_files()
        if temp_files:
            suggestion = CleanupSuggestion(
                suggestion_type='temporary',
                files=temp_files,
                reason="Temporary files that can likely be safely deleted",
                potential_savings=sum(f.size for f in temp_files),
                confidence=0.8,
                action='delete'
            )
            self.cleanup_suggestions.append(suggestion)
        
        # Empty file suggestions
        empty_files = [f for f in self.file_cache.values() if f.size == 0]
        if empty_files:
            suggestion = CleanupSuggestion(
                suggestion_type='empty',
                files=empty_files,
                reason="Empty files that serve no purpose",
                potential_savings=0,  # No space savings, but cleanup
                confidence=0.9,
                action='delete'
            )
            self.cleanup_suggestions.append(suggestion)
    
    def _find_temporary_files(self) -> List[FileInfo]:
        """Find temporary files based on patterns"""
        temp_files = []
        
        for file_info in self.file_cache.values():
            for pattern in self.temp_patterns:
                if fnmatch.fnmatch(file_info.name.lower(), pattern.lower()):
                    temp_files.append(file_info)
                    break
        
        return temp_files
    
    def _update_statistics(self, scan_time: float):
        """Update crawling statistics"""
        self.stats.update({
            'total_files': len(self.file_cache),
            'total_size': sum(f.size for f in self.file_cache.values()),
            'scan_time': scan_time
        })
        
        # File type distribution
        type_counts: Dict[str, int] = {}
        for file_info in self.file_cache.values():
            ext = file_info.extension or 'no_extension'
            type_counts[ext] = type_counts.get(ext, 0) + 1
        
        self.stats['file_types'] = dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True))
        
        # Top largest files
        self.stats['largest_files'] = sorted(
            self.file_cache.values(), 
            key=lambda f: f.size, 
            reverse=True
        )[:10]
        
        # Oldest files
        self.stats['oldest_files'] = sorted(
            self.file_cache.values(),
            key=lambda f: f.modification_time
        )[:10]
    
    def find_files(self, pattern: str, root_path: str = ".", 
                  case_sensitive: bool = False) -> List[FileInfo]:
        """Find files matching a pattern"""
        matches = []
        
        for file_info in self.file_cache.values():
            if file_info.path.startswith(os.path.abspath(root_path)):
                filename = file_info.name if case_sensitive else file_info.name.lower()
                search_pattern = pattern if case_sensitive else pattern.lower()
                
                if fnmatch.fnmatch(filename, search_pattern):
                    matches.append(file_info)
        
        return matches
    
    def find_by_size(self, min_size: int = 0, max_size: Optional[int] = None) -> List[FileInfo]:
        """Find files within size range"""
        matches = []
        
        for file_info in self.file_cache.values():
            if file_info.size >= min_size:
                if max_size is None or file_info.size <= max_size:
                    matches.append(file_info)
        
        return sorted(matches, key=lambda f: f.size, reverse=True)
    
    def find_by_date(self, after: Optional[datetime] = None, 
                    before: Optional[datetime] = None,
                    date_type: str = 'modification') -> List[FileInfo]:
        """Find files by date range"""
        matches = []
        
        for file_info in self.file_cache.values():
            if date_type == 'modification':
                file_date = file_info.modification_time
            elif date_type == 'creation':
                file_date = file_info.creation_time
            elif date_type == 'access':
                file_date = file_info.access_time
            else:
                continue
            
            if after and file_date < after:
                continue
            if before and file_date > before:
                continue
            
            matches.append(file_info)
        
        return sorted(matches, key=lambda f: getattr(f, f'{date_type}_time'))
    
    def get_directory_summary(self, directory_path: str) -> Dict[str, Any]:
        """Get summary of a specific directory"""
        abs_dir_path = os.path.abspath(directory_path)
        
        files_in_dir = [
            f for f in self.file_cache.values()
            if os.path.dirname(f.path) == abs_dir_path
        ]
        
        if not files_in_dir:
            return {'error': 'No files found in directory or directory not scanned'}
        
        total_size = sum(f.size for f in files_in_dir)
        file_types = {}
        
        for file_info in files_in_dir:
            ext = file_info.extension or 'no_extension'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            'path': abs_dir_path,
            'file_count': len(files_in_dir),
            'total_size': total_size,
            'total_size_formatted': self._format_size(total_size),
            'file_types': file_types,
            'largest_file': max(files_in_dir, key=lambda f: f.size),
            'newest_file': max(files_in_dir, key=lambda f: f.modification_time),
            'oldest_file': min(files_in_dir, key=lambda f: f.modification_time)
        }
    
    def execute_cleanup_suggestion(self, suggestion: CleanupSuggestion, 
                                 confirm: bool = False) -> Dict[str, Any]:
        """Execute a cleanup suggestion"""
        if not confirm:
            return {'error': 'Confirmation required for cleanup operations'}
        
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'space_freed': 0
        }
        
        for file_info in suggestion.files:
            try:
                if suggestion.action == 'delete':
                    os.remove(file_info.path)
                    results['space_freed'] += file_info.size
                    results['success'] += 1
                
                elif suggestion.action == 'move':
                    # Move to a backup directory
                    backup_dir = os.path.join(os.path.dirname(file_info.path), '.yuvan_backup')
                    os.makedirs(backup_dir, exist_ok=True)
                    
                    backup_path = os.path.join(backup_dir, file_info.name)
                    shutil.move(file_info.path, backup_path)
                    results['success'] += 1
                
                elif suggestion.action == 'compress':
                    # This would require compression implementation
                    results['errors'].append(f"Compression not implemented for {file_info.path}")
                    results['failed'] += 1
                
            except Exception as e:
                results['errors'].append(f"Failed to process {file_info.path}: {str(e)}")
                results['failed'] += 1
        
        return results
    
    def export_results(self, output_file: str, format: str = 'json'):
        """Export analysis results to file"""
        data = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats
            },
            'duplicates': [
                {
                    'files': [f.path for f in group.files],
                    'total_size': group.total_size,
                    'potential_savings': group.potential_savings,
                    'confidence': group.confidence
                }
                for group in self.duplicates
            ],
            'cleanup_suggestions': [
                {
                    'type': suggestion.suggestion_type,
                    'files': [f.path for f in suggestion.files],
                    'reason': suggestion.reason,
                    'potential_savings': suggestion.potential_savings,
                    'confidence': suggestion.confidence,
                    'action': suggestion.action
                }
                for suggestion in self.cleanup_suggestions
            ],
            'large_files': [
                {
                    'path': f.path,
                    'size': f.size,
                    'size_formatted': self._format_size(f.size)
                }
                for f in self.large_files[:20]
            ]
        }
        
        if format == 'json':
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def stop_crawl(self):
        """Stop the crawling process"""
        self.stop_crawling = True
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current crawling progress"""
        return {
            'progress_percent': self.crawl_progress,
            'files_found': self.total_files_found,
            'is_crawling': not self.stop_crawling
        }