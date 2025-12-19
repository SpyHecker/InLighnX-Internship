import PyPDF2
import sys

def create_passwd_protect(inputpdf, outputpdf, passwd):
    try:
        with open(inputpdf,'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_writer = PyPDF2.PdfWriter()
            
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

            pdf_writer.encrypt(passwd)

            with open(outputpdf,'wb') as outfile:
                pdf_writer.write(outfile)
        
        print(f'Encrypted PDF saved as {outputpdf}')
    except FileNotFoundError:
        print(f'Error : {inputpdf} not found.')
    except PyPDF2.errors.PdfReadError:
        print(f'Error : {inputpdf} is not a valid pdf or is corrupted.')
    except Exception as e:
        print(f'Unexpected Error : {e}')

def main():
    if len(sys.argv) != 4:
        print("Usage: python script.py <input_pdf> <output_pdf> <password>")
        sys.exit(1)
    inputpdf = sys.argv[1]
    outputpdf = sys.argv[2]
    passwd = sys.argv[3]
    create_passwd_protect(inputpdf,outputpdf,passwd)

if __name__=="__main__":
    main()