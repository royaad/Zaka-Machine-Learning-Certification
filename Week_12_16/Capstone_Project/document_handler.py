import os, re, string, docx
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from docx2pdf import convert

def docx_to_pdf(file_path):
    # Convert .docx to .pdf
    convert(file_path)

    # Path to PDF File
    base = os.path.splitext(file_path)[0]
    pdf_path = base + ".pdf"

    # Check if the .pdf file was successfully created
    if os.path.exists(pdf_path):
        # Delete the .docx file
        os.remove(file_path)
        return pdf_path
    
def extract_text(file_path):
    file_extension = os.path.splitext(file_path)[1]

    # Read the file based on its extension
    if file_extension == '.pdf':
        output_string = StringIO()
        with open(file_path, 'rb') as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            laparams = LAParams(all_texts=True)
            device = TextConverter(rsrcmgr, output_string, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)

            extracted_text = output_string.getvalue()

    elif file_extension == '.docx':
        extracted_text = ''
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            extracted_text += para.text + '\n'

    else:
        print(f'Unsupported file extension: {file_extension}. This script currently supports .pdf and .docx files.')
        
    return extracted_text

def text_checker(text):
    text = re.sub(r'([a-z0-9])\n([A-Z])',r'\1 \2', text)
    lines = text.split('\n')
    words = text.replace('\n', ' ')
    words = words.split()
    if len(lines)>len(words):
      tmp = []
      for i in lines:
        if i!='':
          tmp.append(i)
        else:
          tmp.append('\n')
      text = ''.join(tmp)
    return text

def clean_text(extracted_text):
    checked_text = text_checker(extracted_text)
    cleaned_text = re.sub('[^%s]' %re.escape(string.printable), '', checked_text)
    cleaned_text = re.sub(' +',' ', cleaned_text)
    cleaned_text = re.sub('\n+','\n', cleaned_text)
  
    return cleaned_text