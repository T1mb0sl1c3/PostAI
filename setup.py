"""
Setup script for PDF Processing Automation
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup the environment for PDF processing"""
    print("Setting up PDF Processing Automation...")
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        return False
    
    # Install requirements
    print("Installing required packages...")
    os.system("pip install -r requirements.txt")
    
    # Create necessary directories if they don't exist
    config_file = Path("config.py")
    if config_file.exists():
        print("\nConfiguration file found. Please update the paths in config.py:")
        print("- SOURCE_DIR: Path to folder containing PDFs to process")
        print("- DESTINATION_DIR: Path to folder where processed PDFs will be moved")
        print("- OLLAMA_BASE_URL: URL of your Ollama instance (default: http://localhost:11434)")
    
    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Update config.py with your source and destination directories")
    print("2. Make sure Ollama is running with qwen2.5-vl model")
    print("3. Run: python pdf_processor.py")
    
    return True

if __name__ == "__main__":
    setup_environment()
