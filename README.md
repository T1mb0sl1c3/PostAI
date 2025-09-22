# PostAI - Intelligent Mail Processing

PostAI is an automated PDF processing system that analyzes scanned mail documents using AI and organizes them intelligently.

## Features

- **AI-Powered Analysis**: Uses Ollama's Qwen2.5VL model to analyze German mail documents
- **Smart Person Identification**: Identifies the subject person (recipient) of each mail
- **Database Matching**: Matches identified persons against a CSV database
- **Intelligent Renaming**: Renames files to `content_sender_subjectperson.pdf` format
- **Automatic Organization**: Moves processed files to organized directories

## Quick Start

### Prerequisites

- Python 3.7+
- Ollama with Qwen2.5VL model
- Required Python packages

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/PostAI.git
   cd PostAI
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Ollama**:
   ```bash
   ollama pull qwen2.5vl:latest
   ollama serve
   ```

4. **Configure paths** in `config.py`:
   ```python
   SOURCE_DIR = r"path\to\your\source\pdfs"
   DESTINATION_DIR = r"path\to\your\destination\pdfs"
   ```

5. **Setup person database** in `persons.csv`:
   ```csv
   Name,Address,Email,Notes
   Max Mustermann,Musterstraße 1 12345 Musterstadt,max.mustermann@email.com,Client
   ```

### Usage

1. **Add PDF files** to your source directory
2. **Run the processor**:
   ```bash
   python pdf_processor.py
   ```
3. **Check results** in your destination directory

## File Naming Convention

Processed files are renamed using the format:
```
content_sender_subjectperson.pdf
```

Examples:
- `Rechnung_Amazon_Max_Mustermann.pdf`
- `Vertrag_Anwalt_Lisa_Weber.pdf`
- `Lebenslauf_Personalabteilung_Thomas_Mueller.pdf`

## Configuration

### Person Database

Edit `persons.csv` to include all persons whose mail you manage:

```csv
Name,Address,Email,Notes
Max Mustermann,Musterstraße 1 12345 Musterstadt,max.mustermann@email.com,Client
Anna Schmidt,Schmidtweg 5 54321 Berlin,anna.schmidt@company.de,Employee
```

### Settings

Configure paths and settings in `config.py`:

```python
SOURCE_DIR = r"C:\path\to\source\pdfs"
DESTINATION_DIR = r"C:\path\to\destination\pdfs"
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5vl:latest"
```

## How It Works

1. **PDF Extraction**: Extracts text content from PDF files
2. **AI Analysis**: Uses Qwen2.5VL to analyze content in German
3. **Person Identification**: Identifies the subject person (recipient)
4. **Database Matching**: Matches against CSV database
5. **File Organization**: Renames and moves files

## Project Structure

```
PostAI/
├── pdf_processor.py          # Main processing script
├── config.py                # Configuration settings
├── persons.csv              # Person database
├── requirements.txt         # Python dependencies
├── setup.py                 # Setup script
├── run_processor.bat        # Windows batch file
├── README.md               # This file
└── .gitignore              # Git ignore rules
```

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.