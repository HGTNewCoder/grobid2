import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
from lxml import etree
import secret_input
import PyPDF2
import os

GROBID_IP = secret_input.GROBID_IP  # IP address of GROBID server
GROBID_URL = f"http://{GROBID_IP}:8070/api/processHeaderDocument" # Adjust if GROBID is hosted elsewhere

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
SHEETS_SERVICE = build('sheets', 'v4', credentials=CREDS)

# Parameters
sheet_id = secret_input.SHEET_ID  # Replace with your Google Sheet ID
pdf_url_column = secret_input.PDF_URL_COLUMN  # Column with PDF URLs
output_start_column = secret_input.OUTPUT_START_COLUMN  # Column for Title
output_end_column = secret_input.OUTPUT_END_COLUMN  # Column for Year
output_start_row = secret_input.OUTPUT_START_ROW
status_column = secret_input.STATUS_COLUMN  # Column for Status

def extract_metadata(pdf_url):
    try:
        #Download PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Process with GROBID
        files = {'input': response.content}
        grobid_response = requests.post(
            GROBID_URL, 
            files=files, 
            headers={'Accept': 'application/xml'},  # Add this line
            timeout=60
        )
        grobid_response.raise_for_status()
        
        # ... (same PDF download and GROBID request logic) ...
        xml_content = grobid_response.content
        
        # Parse XML with namespaces
        root = etree.fromstring(xml_content)
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        
        # Extract title
        title_elem = root.find('.//tei:title[@type="main"]', namespaces=ns)
        title = title_elem.text if title_elem is not None else "N/A"
        
        # Extract authors
        authors = []
        for author in root.findall('.//tei:author/tei:persName', namespaces=ns):
            forename = author.find('tei:forename', namespaces=ns)
            surname = author.find('tei:surname', namespaces=ns)
            if forename is not None and surname is not None:
                authors.append(f"{forename.text} {surname.text}")
        authors_str = ", ".join(authors) if authors else "N/A"
        
        # Extract year from <date> (prioritize @when attribute)
        date_elem = root.find('.//tei:imprint/tei:date', namespaces=ns)
        year = "N/A"
        if date_elem is not None:
            if 'when' in date_elem.attrib:  # ISO date format (YYYY-MM-DD)
                year = date_elem.attrib['when'].split('-')[0]
            elif date_elem.text:  # Fallback to text content
                year_match = re.search(r'\d{4}', date_elem.text)
                year = year_match.group(0) if year_match else "N/A"
        
        #Extract keywords
        keywords = []
        kw_container = root.find('.//tei:profileDesc/tei:textClass/tei:keywords', namespaces=ns)
        if kw_container is not None:
            for term in kw_container.findall('tei:term', namespaces=ns):
                if term.text:
                    keywords.append(term.text)
        keywords_str = ", ".join(keywords) if keywords else "N/A"
        
        return title, authors_str, year, keywords_str
    
    except Exception as e:
        print(f"Error processing {pdf_url}: {str(e)}")
        return "N/A", "N/A", "N/A" , "N/A"
    
def extract_page_number(pdf_url):
    try:
        # Download PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Save to a temporary file
        with open('file.pdf', 'wb') as f:
            f.write(response.content)
        
        with open('file.pdf', 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
        # Clean up temporary file
        os.remove('file.pdf')
        return num_pages
    except Exception as e:
        print(f"Error downloading {pdf_url}: {str(e)}")
        return "N/A"

# Function to update Google Sheet
def update_sheet(sheet_id, range_name, data):
    body = {'values': [data]}
    SHEETS_SERVICE.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()

pages = ["1.1", "1.2", "2.1", "2.2"]

def main(page_id):
    # Fetch PDF URLs from Sheet
    sheet = SHEETS_SERVICE.spreadsheets()

    # Fetch the URLs and statuses from the Google Sheet
    url_crawl = sheet.values().get(
        spreadsheetId=sheet_id,
        range=f"{page_id}!{pdf_url_column}2:{pdf_url_column}"
    ).execute()

    status_crawl = sheet.values().get(
        spreadsheetId=sheet_id,
        range=f"{page_id}!{status_column}2:{status_column}"
    ).execute()


    urls = [row[0] for row in url_crawl.get('values', [])]
    statuses = [row[0] for row in status_crawl.get('values', [])] 

    # Process each URL
    lst = []
    for i, status in enumerate(statuses):
        if status.lower() == 'true':
            lst.append(i+2)
    
    for j in lst:
        url = urls[j-2]
        title, authors, year, keywords = extract_metadata(url)
        num_pages = extract_page_number(url)

        cols = [title, authors, year, keywords, num_pages]

        target_range = f"{page_id}!{output_start_column}{j}:{output_end_column}{j}"
        update_sheet(sheet_id, target_range, cols)

        print(f"Results: Title={title[:50]}, Authors={authors[:50]}, Year={year}, Keywords={keywords[:50]}, Number of pages: {num_pages} ")
# Main function
if __name__ == "__main__":
    for page in pages:
        print(f"Processing {page}...")
        main(page)