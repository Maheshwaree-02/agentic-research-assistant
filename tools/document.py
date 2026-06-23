# tools/document.py
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from docx import Document
from docx.shared import Inches

def clean_text(text: str) -> str:
    """Clean text before PDF generation"""
    if not text:
        return "No content generated."
    # Remove problematic tags
    text = text.replace('<para>', '').replace('</para>', '')
    text = text.replace('<br>', '\n')
    return text.strip()


def save_as_pdf(markdown_text: str, filename: str):
    """Robust PDF generation"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    cleaned_text = clean_text(markdown_text)
    
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=20)
    story.append(Paragraph("ResearchPilot AI - Technical Report", title_style))
    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), styles['Normal']))
    story.append(Spacer(1, 30))

    # Process content
    lines = cleaned_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('# '):
            story.append(Paragraph(line[2:], styles['Heading1']))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], styles['Heading2']))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], styles['Heading3']))
        elif line.startswith('- ') or line.startswith('* '):
            story.append(Paragraph(f"• {line[2:]}", styles['Normal']))
        else:
            story.append(Paragraph(line, styles['Normal']))
        
        story.append(Spacer(1, 12))

    doc.build(story)
    return filename


def save_as_docx(markdown_text: str, filename: str):
    """Robust DOCX generation"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    cleaned_text = clean_text(markdown_text)
    doc = Document()
    
    doc.add_heading('ResearchPilot AI - Technical Report', 0)
    doc.add_paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}")
    doc.add_paragraph("-" * 50)

    lines = cleaned_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        else:
            doc.add_paragraph(line)
    
    doc.save(filename)
    return filename
