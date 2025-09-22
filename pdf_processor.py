"""
PDF Processing Automation
Extracts PDFs from a folder, analyzes them using Ollama Qwen2.5VL, 
and renames/moves them based on content analysis.
"""

import os
import json
import logging
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import PyPDF2
from PIL import Image
import io

from config import Config

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self):
        self.config = Config()
        self.config.validate_paths()
        self.source_dir = Path(self.config.SOURCE_DIR)
        self.dest_dir = Path(self.config.DESTINATION_DIR)
        self.persons_db = self.config.load_persons_database()
        logger.info(f"Loaded {len(self.persons_db)} person entries from database")
        
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def get_pdf_images(self, pdf_path: Path) -> List[bytes]:
        """Extract images from PDF for visual analysis"""
        try:
            images = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    # For scanned documents, we'll focus on text extraction
                    # If needed, we can enhance this to extract actual images
                    pass
                    
            return images
        except Exception as e:
            logger.error(f"Error extracting images from {pdf_path}: {e}")
            return []
    
    def analyze_with_ollama(self, pdf_content: str, pdf_path: Path) -> Dict[str, str]:
        """Send PDF content to Ollama Qwen2.5VL for analysis"""
        try:
            prompt = f"""
            Du analysierst ein gescanntes Mail-Dokument. Bitte analysiere den folgenden Inhalt und extrahiere wichtige Informationen:
            
            PDF Inhalt:
            {pdf_content}
            
            Bitte gib eine JSON-Antwort mit folgenden Feldern zurück:
            - "content": Eine kurze Beschreibung des Hauptinhalts/Zwecks (maximal 3 Wörter)
            - "sender": Der Name oder die Organisation, die diese Mail gesendet hat. Organisationsname hat Priorität.
            - "subject_person": Der Name der Person, um die es in dieser Mail geht (der Betroffene/Adressat). Falls keine Person identifiziert werden kann, verwende "Unknown"
            
            WICHTIG: Identifiziere die Person, um die es in der Mail geht (nicht den Absender). Das ist die Person, deren Mail verwaltet wird.
            
            Formatiere deine Antwort nur als gültiges JSON, ohne zusätzlichen Text.
            Antworte auf Deutsch.
            """
            
            payload = {
                "model": self.config.MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.config.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '')
                
                # Try to parse JSON response
                try:
                    # Clean the response to extract JSON
                    ai_response = ai_response.strip()
                    if ai_response.startswith('```json'):
                        ai_response = ai_response[7:]
                    if ai_response.endswith('```'):
                        ai_response = ai_response[:-3]
                    
                    analysis = json.loads(ai_response)
                    return analysis
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON from AI response: {ai_response}")
                    # Fallback parsing
                    return self._fallback_parse(ai_response)
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error analyzing with Ollama: {e}")
            return {}
    
    def _fallback_parse(self, response: str) -> Dict[str, str]:
        """Fallback parser when JSON parsing fails"""
        content = "Document"
        sender = "Unknown"
        subject_person = "Unknown"
        
        lines = response.split('\n')
        for line in lines:
            line = line.lower().strip()
            if 'content:' in line:
                content = line.split('content:')[1].strip()[:20]
            elif 'sender:' in line:
                sender = line.split('sender:')[1].strip()[:20]
            elif 'subject_person:' in line:
                subject_person = line.split('subject_person:')[1].strip()[:20]
        
        return {
            "content": content,
            "sender": sender,
            "subject_person": subject_person
        }
    
    def match_person_in_database(self, identified_person: str) -> str:
        """Match the identified person against the database"""
        if not identified_person or identified_person.lower() == "unknown":
            return "Unknown"
        
        # Clean the identified person name
        clean_person = identified_person.strip().lower()
        
        # Try exact match first
        if clean_person in self.persons_db:
            return self.persons_db[clean_person]['name']
        
        # Try partial matches
        for db_key, person_info in self.persons_db.items():
            if clean_person in db_key or db_key in clean_person:
                return person_info['name']
        
        # Try matching individual words
        person_words = clean_person.split()
        for word in person_words:
            if len(word) > 2 and word in self.persons_db:
                return self.persons_db[word]['name']
        
        # If no match found, return the original identified person (don't default to "Unknown")
        return identified_person
    
    def generate_filename(self, analysis: Dict[str, str], original_name: str) -> str:
        """Generate new filename based on analysis"""
        content = analysis.get('content', 'Document')
        sender = analysis.get('sender', 'Unknown')
        subject_person = analysis.get('subject_person', 'Unknown')
        
        # Match the subject person against the database
        matched_person = self.match_person_in_database(subject_person)
        
        # Clean and format the fields
        content = self._clean_filename(content)
        sender = self._clean_filename(sender)
        subject_person = self._clean_filename(matched_person)
        
        # Limit content to 3 words max
        content_words = content.split()[:3]
        content = '_'.join(content_words)
        
        # Create new filename: content_sender_subjectperson.pdf (without original name)
        new_name = f"{content}_{sender}_{subject_person}.pdf"
        
        logger.info(f"Generated filename: {new_name} (matched person: {matched_person})")
        return new_name
    
    def _clean_filename(self, text: str) -> str:
        """Clean text for use in filename"""
        # Remove special characters and replace spaces with underscores
        import re
        cleaned = re.sub(r'[^\w\s-]', '', text)
        cleaned = re.sub(r'[-\s]+', '_', cleaned)
        return cleaned.strip('_')
    
    def move_file(self, source_path: Path, dest_filename: str) -> bool:
        """Move file to destination directory with new name"""
        try:
            dest_path = self.dest_dir / dest_filename
            
            # Handle duplicate filenames
            counter = 1
            original_dest = dest_path
            while dest_path.exists():
                stem = original_dest.stem
                suffix = original_dest.suffix
                dest_path = original_dest.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            
            source_path.rename(dest_path)
            logger.info(f"Moved {source_path.name} to {dest_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file {source_path}: {e}")
            return False
    
    def process_pdf(self, pdf_path: Path) -> bool:
        """Process a single PDF file"""
        try:
            logger.info(f"Processing: {pdf_path.name}")
            
            # Extract text content
            pdf_content = self.extract_text_from_pdf(pdf_path)
            
            if not pdf_content:
                logger.warning(f"No text content found in {pdf_path.name}")
                pdf_content = f"Scanned document: {pdf_path.name}"
            
            # Analyze with Ollama
            analysis = self.analyze_with_ollama(pdf_content, pdf_path)
            
            if not analysis:
                logger.error(f"Failed to analyze {pdf_path.name}")
                return False
            
            # Generate new filename
            new_filename = self.generate_filename(analysis, pdf_path.name)
            
            # Move file
            success = self.move_file(pdf_path, new_filename)
            
            if success:
                logger.info(f"Successfully processed: {pdf_path.name} -> {new_filename}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return False
    
    def process_all_pdfs(self) -> Dict[str, int]:
        """Process all PDF files in the source directory"""
        logger.info("Starting PDF processing...")
        
        pdf_files = list(self.source_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.info("No PDF files found in source directory")
            return {"processed": 0, "failed": 0, "total": 0}
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        results = {"processed": 0, "failed": 0, "total": len(pdf_files)}
        
        for pdf_file in pdf_files:
            try:
                if self.process_pdf(pdf_file):
                    results["processed"] += 1
                else:
                    results["failed"] += 1
                    
                # Add small delay to avoid overwhelming the API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Unexpected error processing {pdf_file}: {e}")
                results["failed"] += 1
        
        logger.info(f"Processing complete: {results['processed']} processed, {results['failed']} failed")
        return results


def main():
    """Main function to run the PDF processor"""
    try:
        processor = PDFProcessor()
        results = processor.process_all_pdfs()
        
        print(f"\nProcessing Results:")
        print(f"Total files: {results['total']}")
        print(f"Successfully processed: {results['processed']}")
        print(f"Failed: {results['failed']}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
