"""
Configuration settings for PDF processing automation
"""
import os
import csv
from pathlib import Path

class Config:
    # Directory paths
    SOURCE_DIR = r"C:\Users\aaaaaaa\Desktop\nand2tetris\AIanalyse\Testinput"  # Change this to your source folder
    DESTINATION_DIR = r"C:\Users\aaaaaaa\Desktop\nand2tetris\AIanalyse\Testoutput"  # Change this to your destination folder
    
    # Ollama API settings
    OLLAMA_BASE_URL = "http://localhost:11434"
    MODEL_NAME = "qwen2.5vl:latest"
    
    # Processing settings
    MAX_CONTENT_WORDS = 3  # Maximum words for content description
    SUPPORTED_FORMATS = ['.pdf']
    
    # Person database
    PERSONS_CSV = "persons.csv"
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "pdf_processor.log"
    
    @classmethod
    def validate_paths(cls):
        """Validate that source and destination paths exist or can be created"""
        source = Path(cls.SOURCE_DIR)
        dest = Path(cls.DESTINATION_DIR)
        
        if not source.exists():
            raise FileNotFoundError(f"Source directory does not exist: {cls.SOURCE_DIR}")
        
        dest.mkdir(parents=True, exist_ok=True)
        return True
    
    @classmethod
    def load_persons_database(cls):
        """Load the persons database from CSV file"""
        persons = {}
        csv_path = Path(cls.PERSONS_CSV)
        
        if not csv_path.exists():
            return persons
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    name = row.get('Name', '').strip()
                    address = row.get('Address', '').strip()
                    email = row.get('Email', '').strip()
                    
                    if name:
                        # Store person info with normalized name as key
                        persons[name.lower()] = {
                            'name': name,
                            'address': address,
                            'email': email
                        }
                        
                        # Also add variations for better matching
                        # Split name and add individual parts
                        name_parts = name.lower().split()
                        for part in name_parts:
                            if len(part) > 2:  # Only meaningful parts
                                persons[part] = {
                                    'name': name,
                                    'address': address,
                                    'email': email
                                }
        except Exception as e:
            print(f"Error loading persons database: {e}")
        
        return persons
