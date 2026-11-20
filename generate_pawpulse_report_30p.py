import os
import sys
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, PageBreak, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Import modular page packages
from report_pages_1_to_10 import add_pages_1_to_10
from report_pages_11_to_20 import add_pages_11_to_20
from report_pages_21_to_30 import add_pages_21_to_30

# ── COLOR PALETTE DEFINITIONS ────────────────────────────────────────────────
PRIMARY_DARK   = colors.HexColor('#0f172a') # Slate 900
PRIMARY_NAVY   = colors.HexColor('#1e293b') # Slate 800
ACCENT_PLUM    = colors.HexColor('#9B5B87') # PawPulse Brand Plum
ACCENT_BLUE    = colors.HexColor('#2563eb') # Royal Blue
SUCCESS_GREEN  = colors.HexColor('#059669') # Emerald 600
WARNING_AMBER  = colors.HexColor('#d97706') # Amber 600
DANGER_RED     = colors.HexColor('#dc2626') # Red 600
BG_LIGHT_GRAY  = colors.HexColor('#f8fafc') # Slate 50
BG_CARD_GRAY   = colors.HexColor('#f1f5f9') # Slate 100
BORDER_GRAY    = colors.HexColor('#cbd5e1') # Slate 300
BORDER_DARK    = colors.HexColor('#334155') # Slate 700
TEXT_DARK      = colors.HexColor('#0f172a') # Slate 900
TEXT_MUTED     = colors.HexColor('#475569') # Slate 600
TEXT_LIGHT     = colors.HexColor('#ffffff') # White

C = {
    'PRIMARY_DARK': PRIMARY_DARK,
    'PRIMARY_NAVY': PRIMARY_NAVY,
    'ACCENT_PLUM': ACCENT_PLUM,
    'ACCENT_BLUE': ACCENT_BLUE,
    'SUCCESS_GREEN': SUCCESS_GREEN,
    'WARNING_AMBER': WARNING_AMBER,
    'DANGER_RED': DANGER_RED,
    'BG_LIGHT_GRAY': BG_LIGHT_GRAY,
    'BG_CARD_GRAY': BG_CARD_GRAY,
    'BORDER_GRAY': BORDER_GRAY,
    'BORDER_DARK': BORDER_DARK,
    'TEXT_DARK': TEXT_DARK,
    'TEXT_MUTED': TEXT_MUTED,
    'TEXT_LIGHT': TEXT_LIGHT
}

# ── NUMBERED CANVAS (PAGE X OF Y) ────────────────────────────────────────────
class PawPulseCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            # Running Header
            self.setFont('Helvetica-Bold', 7.5)
            self.setFillColor(TEXT_MUTED)
            self.drawString(54, 752, "PAWPULSE AUTONOMOUS VISION SENTINEL — ENGINEERING & MATHEMATICAL MASTER REPORT")
            self.setFont('Helvetica', 7.5)
            self.drawRightString(612 - 54, 752, "RTX 5080 / RT-DETR-X / PYQT6 PC SUITE")
            
            self.setStrokeColor(BORDER_GRAY)
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

            # Running Footer
            self.line(54, 46, 612 - 54, 46)
            self.setFont('Helvetica', 7.5)
            self.drawString(54, 34, "CONFIDENTIAL & PROPRIETARY — PAWPULSE CLINICAL SHELTER AUTOMATION")
            self.setFont('Helvetica-Bold', 7.5)
            self.setFillColor(ACCENT_PLUM)
            self.drawRightString(612 - 54, 34, f"Page {self._pageNumber} of {page_count}")
            self.restoreState()

# ── STYLES INITIALIZATION ────────────────────────────────────────────────────
base_styles = getSampleStyleSheet()

style_cover_title = ParagraphStyle(
    'CoverTitle',
    parent=base_styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=24,
    leading=30,
    textColor=PRIMARY_DARK,
    spaceAfter=8
)

style_cover_sub = ParagraphStyle(
    'CoverSub',
    parent=base_styles['Normal'],
    fontName='Helvetica',
    fontSize=12,
    leading=17,
    textColor=ACCENT_PLUM,
    spaceAfter=14
)

style_h1 = ParagraphStyle(
    'CustomH1',
    parent=base_styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=13.5,
    leading=17.5,
    textColor=PRIMARY_DARK,
    spaceBefore=0,
    spaceAfter=3
)

style_h2 = ParagraphStyle(
    'CustomH2',
    parent=base_styles['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=10,
    leading=13.5,
    textColor=ACCENT_PLUM,
    spaceBefore=5,
    spaceAfter=2.5
)

style_h3 = ParagraphStyle(
    'CustomH3',
    parent=base_styles['Heading3'],
    fontName='Helvetica-Bold',
    fontSize=8.8,
    leading=11.5,
    textColor=PRIMARY_NAVY,
    spaceBefore=3.5,
    spaceAfter=1.5
)

style_body = ParagraphStyle(
    'CustomBody',
    parent=base_styles['Normal'],
    fontName='Helvetica',
    fontSize=7.8,
    leading=10.6,
    textColor=TEXT_DARK,
    spaceAfter=3.5
)

style_body_bold = ParagraphStyle(
    'CustomBodyBold',
    parent=style_body,
    fontName='Helvetica-Bold'
)

style_body_muted = ParagraphStyle(
    'CustomBodyMuted',
    parent=style_body,
    textColor=TEXT_MUTED
)

style_code = ParagraphStyle(
    'CustomCode',
    parent=base_styles['Code'],
    fontName='Courier',
    fontSize=6.8,
    leading=8.6,
    textColor=PRIMARY_DARK,
    spaceBefore=1.5,
    spaceAfter=1.5
)

style_formula = ParagraphStyle(
    'CustomFormula',
    parent=base_styles['Normal'],
    fontName='Courier-Bold',
    fontSize=7.5,
    leading=10,
    textColor=PRIMARY_DARK,
    alignment=1 # Center
)

S = {
    'CoverTitle': style_cover_title,
    'CoverSub': style_cover_sub,
    'CustomH1': style_h1,
    'CustomH2': style_h2,
    'CustomH3': style_h3,
    'CustomBody': style_body,
    'CustomBodyBold': style_body_bold,
    'CustomBodyMuted': style_body_muted,
    'CustomCode': style_code,
    'CustomFormula': style_formula
}

# ── HELPER FORMATTING FUNCTIONS ──────────────────────────────────────────────
def create_callout(text, title=None, border_color=ACCENT_PLUM, bg_color=BG_LIGHT_GRAY, width=504):
    content = []
    if title:
        content.append(Paragraph(f"<b>{title}</b>", ParagraphStyle('CalloutT', parent=style_body_bold, textColor=border_color, fontSize=8, leading=10)))
        content.append(Spacer(1, 1.5))
    content.append(Paragraph(text, style_body))
    
    t = Table([[content]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('BOX', (0,0), (-1,-1), 0.8, border_color),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    return t

def create_formula_card(formula_text, title=None, notes=None, width=504):
    content = []
    if title:
        content.append(Paragraph(f"<b>FORMULATION: {title}</b>", ParagraphStyle('FTitle', parent=style_body_bold, textColor=PRIMARY_NAVY, fontSize=7.2, leading=9)))
        content.append(Spacer(1, 1.5))
    content.append(Paragraph(f"<b>{formula_text.replace(chr(10), '<br/>').replace(' ', '&nbsp;')}</b>", style_formula))
    if notes:
        content.append(Spacer(1, 1.5))
        content.append(Paragraph(f"<i>{notes}</i>", ParagraphStyle('FNotes', parent=style_body_muted, fontSize=6.8, leading=8.5, alignment=1)))
    
    t = Table([[content]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD_GRAY),
        ('BOX', (0,0), (-1,-1), 0.6, BORDER_GRAY),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    return t

def create_code_card(code_text, title=None, width=504):
    content = []
    if title:
        content.append(Paragraph(f"<b>{title}</b>", ParagraphStyle('CTitle', parent=style_body_bold, textColor=PRIMARY_NAVY, fontSize=7.2, leading=9)))
        content.append(Spacer(1, 1.5))
    content.append(Paragraph(code_text.replace('\n', '<br/>').replace(' ', '&nbsp;'), style_code))
    
    t = Table([[content]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.6, colors.HexColor('#e2e8f0')),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    return t

def make_header_block(chapter_num, title, subtitle):
    p1 = Paragraph(f"<b>CHAPTER {chapter_num}</b>", ParagraphStyle('CHNum', parent=style_body_bold, textColor=ACCENT_PLUM, fontSize=7.5, leading=9.5))
    p2 = Paragraph(title, style_h1)
    p3 = Paragraph(subtitle, ParagraphStyle('CHSub', parent=style_body_muted, fontSize=8, leading=10.5))
    line = HRFlowable(width="100%", thickness=0.6, color=BORDER_GRAY, spaceBefore=3, spaceAfter=6)
    return [p1, p2, p3, line]

H = {
    'create_callout': create_callout,
    'create_formula_card': create_formula_card,
    'create_code_card': create_code_card,
    'make_header_block': make_header_block
}

# ── MAIN EXECUTION ───────────────────────────────────────────────────────────
def main():
    output_pdf = r"C:\animal\PawPulse_Complete_Technical_Report.pdf"
    alt_pdf = r"C:\animal\PawPulse_Technical_Master_Report_30_Pages.pdf"
    print(f"🚀 Building PawPulse 30-Page Technical Master Report: {output_pdf}")
    
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    story = []
    print("-> Appending Pages 1 to 10...")
    add_pages_1_to_10(story, S, C, H)
    print("-> Appending Pages 11 to 20...")
    add_pages_11_to_20(story, S, C, H)
    print("-> Appending Pages 21 to 30...")
    add_pages_21_to_30(story, S, C, H)
    
    print(f"-> Total Flowable Elements: {len(story)}")
    print("-> Compiling PDF with PawPulseCanvas...")
    doc.build(story, canvasmaker=PawPulseCanvas)
    
    # Also save a copy under the second name requested
    import shutil
    shutil.copyfile(output_pdf, alt_pdf)
    
    # Verify file size and page count
    file_size_mb = os.path.getsize(output_pdf) / (1024 * 1024)
    print(f"✅ SUCCESS! Generated {output_pdf} ({file_size_mb:.2f} MB)")
    print(f"✅ DUPLICATE SAVED: {alt_pdf}")
    
    # Check exact page count
    with open(output_pdf, 'rb') as f:
        content = f.read()
        # Count pages via PDF trailer dictionary /Pages
        import re
        pages_matches = re.findall(rb'/Type\s*/Page\b', content)
        print(f"📄 Exact Physical Page Count in PDF: {len(pages_matches)} pages")

if __name__ == '__main__':
    main()
