from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

def create_lorem_pdf(filename):
    text = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n"
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco.\n"
    )
    c = canvas.Canvas(filename, pagesize=LETTER)
    text_obj = c.beginText(40, 750)
    for line in text.split('\n'):
        text_obj.textLine(line)
    c.drawText(text_obj)
    c.save()
    print(f"Sample PDF created: {filename}")

create_lorem_pdf("sample.pdf")
