import pymupdf




class pdf_processer:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
    def process_pdf(self):
        try:
            doc = pymupdf.open(self.pdf_path)
            for page in doc:
                text = page.get_text()
            return text
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return None




