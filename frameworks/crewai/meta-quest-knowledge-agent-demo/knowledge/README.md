# Meta Quest Knowledge Base

This directory contains PDF documentation about Meta Quest that the knowledge agent uses to answer questions.

## Current Documents

1. **meta_quest_guide.txt** - Comprehensive guide covering:
   - Introduction and overview
   - Setup and configuration
   - Controllers and hand tracking
   - Mixed reality features
   - WiFi connectivity
   - Charging and battery management
   - Apps and games
   - Guardian system
   - Troubleshooting
   - Technical specifications
   - Care and maintenance
   - Safety guidelines
   - Account and privacy
   - Warranty and support

## Adding PDF Documents

To add Meta Quest PDF documentation:

1. Download official PDF guides from:
   - Meta Quest Safety Center: https://www.meta.com/quest/safety-center/quest-3/
   - Meta Quest Help: https://www.meta.com/help/quest/

2. Place PDF files in this directory

3. The knowledge agent will automatically index and search all PDFs

## Converting Text to PDF

The included text file can be converted to PDF using various tools:

```bash
# Using Python with reportlab (if available)
python -c "
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Read text file
with open('meta_quest_guide.txt', 'r') as f:
    content = f.read()

# Create PDF
c = canvas.Canvas('meta_quest_guide.pdf', pagesize=letter)
text = c.beginText(0.5 * inch, 10.5 * inch)
text.setFont('Courier', 10)

for line in content.split('\n'):
    if text.getY() < 1 * inch:
        c.drawText(text)
        c.showPage()
        text = c.beginText(0.5 * inch, 10.5 * inch)
        text.setFont('Courier', 10)
    text.textLine(line)

c.drawText(text)
c.save()
"

# Or use online converters:
# - https://www.adobe.com/acrobat/online/txt-to-pdf.html
# - https://www.pdf2go.com/txt-to-pdf
```

## File Format Support

The knowledge agent supports:
- PDF files (.pdf)
- Text files (.txt) - for development and testing

**Note:** For production use, convert the text guide to PDF format for better compatibility with the PDF processing tools.
