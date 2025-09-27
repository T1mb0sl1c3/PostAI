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
from typing import Dict, List, Optional
import PyPDF2
import pytesseract
from PIL import Image
import io

# Ensure config.py is present and correctly configured
from config import Config

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, 'INFO'),
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
        """
        Extracts text from a PDF. If no text is found, falls back to OCR on embedded images.
        """
        text = ""
        try:
            # 1. First attempt: Standard text extraction
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            
            if text.strip():
                logger.info(f"Text successfully extracted from {pdf_path.name} using standard method.")
                return text.strip()

            # 2. Fallback: If no text was found, attempt OCR on embedded images
            logger.warning(f"No text layers found in {pdf_path.name}. Attempting OCR on embedded images.")
            ocr_text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    # page.images is a list of image objects
                    for i, image_file_object in enumerate(page.images):
                        try:
                            # Convert image data to a PIL Image
                            image = Image.open(io.BytesIO(image_file_object.data))
                            # Perform OCR
                            ocr_text += pytesseract.image_to_string(image, lang='deu') + "\n"
                            logger.debug(f"Performed OCR on image {i+1} from page {page_num+1} of {pdf_path.name}.")
                        except Exception as ocr_err:
                            logger.error(f"Could not perform OCR on an image in {pdf_path.name}: {ocr_err}")
            
            if ocr_text.strip():
                logger.info(f"Text successfully extracted from {pdf_path.name} using OCR fallback.")
                return ocr_text.strip()

        except Exception as e:
            logger.error(f"Failed to process {pdf_path.name}: {e}")
            return ""
            
        # 3. If both methods fail
        logger.warning(f"Could not extract any text or image content from {pdf_path.name}.")
        return ""
    
    def analyze_with_ollama(self, pdf_content: str, pdf_path: Path) -> Dict[str, str]:
        """Send PDF content to Ollama Qwen2.5VL for analysis"""
        try:
            prompt = f"""
            Du analysierst ein gescanntes Mail-Dokument. Bitte analysiere den folgenden Inhalt und extrahiere wichtige Informationen:
            
            PDF Inhalt:
            {pdf_content}
            
            Bitte gib eine JSON-Antwort mit folgenden Feldern zurück:
            - "content": Eine kurze Beschreibung des Hauptinhalts/Zwecks
            - "sender": Der Name oder die Organisation, die diese Mail gesendet hat. Organisationsname hat Priorität.
            - "subject_person": Der Name der Person, um die es in dieser Mail geht (der Betroffene/Adressat). Falls keine Person identifiziert werden kann, verwende "Unknown"
            
            WICHTIG: Identifiziere die Person, um die es in der Mail geht (nicht den Absender). Das ist die Person, deren Mail verwaltet wird.
            Fasse dich kurz, keiner der Felder sollte länger als 2 Wörter sein.
            
            Formatiere deine Antwort nur als gültiges JSON, ohne zusätzlichen Text.
            Antworte auf Deutsch.
            """
            
            payload = {
                "model": self.config.MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json", # Use JSON mode for reliable output
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
                result_json = response.json()
                # With 'format: "json"', the response is a stringified JSON object
                response_str = result_json.get('response', '{}')
                analysis = json.loads(response_str)
                return analysis
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {}
                
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON from AI response: {response.json().get('response', '')}")
            return self._fallback_parse(response.json().get('response', ''))
        except Exception as e:
            logger.error(f"Error analyzing with Ollama: {e}")
            return {}

    def _fallback_parse(self, response: str) -> Dict[str, str]:
        """Fallback parser when JSON parsing fails"""
        # This is a simple fallback and may not be needed if Ollama's JSON mode is stable.
        import re
        content = re.search(r'"content"\s*:\s*"([^"]+)"', response)
        sender = re.search(r'"sender"\s*:\s*"([^"]+)"', response)
        subject_person = re.search(r'"subject_person"\s*:\s*"([^"]+)"', response)

        return {
            "content": content.group(1) if content else "Document",
            "sender": sender.group(1) if sender else "Unknown",
            "subject_person": subject_person.group(1) if subject_person else "Unknown"
        }

    def match_person_in_database(self, identified_person: str) -> str:
        """Match the identified person against the database"""
        if not identified_person or identified_person.lower() == "unknown":
            return "Unknown"
        
        clean_person = identified_person.strip().lower()
        
        # Try exact and partial matches
        for db_key, person_info in self.persons_db.items():
            if clean_person in db_key or db_key in clean_person:
                return person_info['name']
        
        # Try matching individual words
        for word in clean_person.split():
            if len(word) > 2 and word in self.persons_db:
                return self.persons_db[word]['name']
        
        return identified_person

    def generate_filename(self, analysis: Dict[str, str], original_name: str) -> str:
        """Generate new filename based on analysis"""
        content = analysis.get('content', 'Document')
        sender = analysis.get('sender', 'Unknown')
        subject_person = analysis.get('subject_person', 'Unknown')
        
        matched_person = self.match_person_in_database(subject_person)
        
        content = self._clean_filename(content)
        sender = self._clean_filename(sender)
        subject_person = self._clean_filename(matched_person)
        
        content = '_'.join(content.split('_')[:3])
        
        new_name = f"{content}_{sender}_{subject_person}.pdf"
        
        logger.info(f"Generated filename: {new_name} (matched person: {matched_person})")
        return new_name

    def _clean_filename(self, text: str) -> str:
        """Clean text for use in filename"""
        import re
        cleaned = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE)
        cleaned = re.sub(r'[-\s]+', '_', cleaned)
        return cleaned.strip('_')

    def move_file(self, source_path: Path, dest_filename: str) -> bool:
        """Move file to destination directory with new name"""
        try:
            dest_path = self.dest_dir / dest_filename
            
            counter = 1
            original_stem = dest_path.stem
            while dest_path.exists():
                dest_path = dest_path.with_name(f"{original_stem}_{counter}{dest_path.suffix}")
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
            
            pdf_content = self.extract_text_from_pdf(pdf_path)
            
            if not pdf_content:
                logger.error(f"No content could be extracted from {pdf_path.name}. Skipping file.")
                return False
            
            analysis = self.analyze_with_ollama(pdf_content, pdf_path)
            
            if not analysis:
                logger.error(f"Failed to analyze {pdf_path.name}. Skipping file.")
                return False
            
            new_filename = self.generate_filename(analysis, pdf_path.name)
            success = self.move_file(pdf_path, new_filename)
            
            if success:
                logger.info(f"Successfully processed: {pdf_path.name} -> {new_filename}")
            
            return success
        except Exception as e:
            logger.error(f"An unexpected error occurred while processing {pdf_path}: {e}")
            return False
            
    def process_all_pdfs(self) -> Dict[str, int]:
        """Process all PDF files in the source directory"""
        logger.info("Starting PDF processing...")
        pdf_files = list(self.source_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.info("No PDF files found in source directory.")
            return {"processed": 0, "failed": 0, "total": 0}
        
        logger.info(f"Found {len(pdf_files)} PDF files to process.")
        results = {"processed": 0, "failed": 0, "total": len(pdf_files)}
        
        for pdf_file in pdf_files:
            if self.process_pdf(pdf_file):
                results["processed"] += 1
            else:
                results["failed"] += 1
            time.sleep(1)
        
        logger.info(f"Processing complete: {results['processed']} processed, {results['failed']} failed.")
        return results

# Main execution block remains the same
def main():
    """Main function to run the PDF processor"""
    try:
        processor = PDFProcessor()
        results = processor.process_all_pdfs()
        
        print("\n--- Processing Results ---")
        print(f"Total files found:      {results['total']}")
        print(f"Successfully processed: {results['processed']}")
        print(f"Failed to process:      {results['failed']}")
        
    except Exception as e:
        logger.critical(f"A fatal error occurred in main: {e}", exc_info=True)
        print(f"Error: {e}")

if __name__ == "__main__":
    main()