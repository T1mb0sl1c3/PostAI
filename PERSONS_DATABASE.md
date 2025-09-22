# Person Database Setup

## Overview

The PDF processor now identifies the **subject person** (the person the mail is about) and uses this in the filename format: `content_sender_subjectperson.pdf`

## CSV Database Format

Edit the `persons.csv` file to include all persons whose mail you manage:

```csv
Name,Address,Email,Notes
Max Mustermann,Musterstraße 1 12345 Musterstadt,max.mustermann@email.com,Client
Anna Schmidt,Schmidtweg 5 54321 Berlin,anna.schmidt@company.de,Employee
Thomas Müller,Müllerplatz 2 98765 Hamburg,thomas.mueller@business.com,Partner
Lisa Weber,Weberstraße 10 11111 München,lisa.weber@firm.de,Client
David Klein,Kleinweg 3 22222 Köln,david.klein@corp.de,Supplier
```

### Required Fields:
- **Name**: Full name of the person
- **Address**: Address (optional, for better matching)
- **Email**: Email address (optional, for better matching)
- **Notes**: Additional notes (optional)

## How It Works

1. **AI Analysis**: The AI analyzes the PDF and identifies:
   - Content type (e.g., "Rechnung", "Vertrag")
   - Sender (e.g., "Firma XYZ")
   - **Subject Person** (e.g., "Max Mustermann")

2. **Database Matching**: The system matches the identified person against your CSV database:
   - Exact name matches
   - Partial matches
   - Individual word matches

3. **Filename Generation**: Creates filename in format:
   ```
   content_sender_subjectperson.pdf
   ```

## Examples

### Before Processing:
- `document_123.pdf` (contains invoice for Max Mustermann from Firma ABC)

### After Processing:
- `Rechnung_Firma_ABC_Max_Mustermann.pdf`

## Adding New Persons

To add a new person to the database:

1. Open `persons.csv`
2. Add a new row with the person's information:
   ```csv
   Name,Address,Email,Notes
   Neue Person,Neue Straße 1,neue@email.com,Client
   ```
3. Save the file
4. The system will automatically use the updated database on the next run

## Matching Logic

The system uses multiple matching strategies:

1. **Exact Match**: "Max Mustermann" → "Max Mustermann"
2. **Partial Match**: "Mustermann" → "Max Mustermann"
3. **Word Match**: "Max" → "Max Mustermann"

If no match is found, the system uses "Unknown" as the subject person.

## Troubleshooting

### Person Not Recognized:
- Check if the name is in the CSV file
- Try adding variations of the name
- Check spelling and formatting

### Wrong Person Matched:
- Make sure names in CSV are unique enough
- Consider adding more specific information to distinguish similar names

## File Structure

```
project/
├── persons.csv          # Person database
├── config.py           # Configuration (includes CSV loading)
├── pdf_processor.py    # Main processor with person matching
└── ...
```
