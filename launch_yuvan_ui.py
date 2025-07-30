#!/usr/bin/env python3
"""
Launch script for Yuvan AI Assistant Web UI

This script handles the setup and launching of the Yuvan web interface
with ChatGPT-like design and voice animation features.
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'plotly',
        'numpy',
        'pygame'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", *missing_packages
            ])
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    return True

def setup_environment():
    """Setup the environment for Yuvan UI"""
    print("🚀 Setting up Yuvan AI Assistant Web UI...")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    yuvan_dir = current_dir / "yuvan"
    
    if not yuvan_dir.exists():
        print("❌ Error: yuvan directory not found!")
        print("Please run this script from the Yuvan project root directory.")
        return False
    
    # Check if main yuvan files exist
    required_files = [
        "yuvan/task_handler.py",
        "yuvan/voice_system.py",
        "yuvan_ui.py",
        "voice_animation.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not (current_dir / file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ Environment setup complete!")
    return True

def launch_ui():
    """Launch the Streamlit UI"""
    print("🌐 Launching Yuvan Web UI...")
    print("🎯 Open your browser and go to: http://localhost:8501")
    print("🎤 Voice features will be available once the UI loads")
    print("❌ Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Launch Streamlit with custom configuration
        cmd = [
            sys.executable, "-m", "streamlit", "run", "yuvan_ui.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501",
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Yuvan UI...")
    except Exception as e:
        print(f"❌ Error launching UI: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("=" * 60)
    print("🤖 YUVAN AI ASSISTANT - WEB UI LAUNCHER")
    print("=" * 60)
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Failed to setup dependencies. Exiting...")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Failed to setup environment. Exiting...")
        sys.exit(1)
    
    # Launch UI
    if not launch_ui():
        print("❌ Failed to launch UI. Exiting...")
        sys.exit(1)

if __name__ == "__main__":
    main()