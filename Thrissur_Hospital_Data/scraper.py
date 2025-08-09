import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from typing import List, Dict

def extract_hospital_data(text: str) -> Dict[str, str]:
    """Extract hospital details from a text block"""
    data = {
        'Name': '',
        'Address': '',
        'Email': '',
        'Phone': '',
        'Website': '',
        'Pincode': ''
    }
    
    # Extract name (first line)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        data['Name'] = lines[0]
    
    # Extract address (lines between name and contact info)
    address_lines = []
    for line in lines[1:]:
        if any(keyword in line.lower() for keyword in ['email', 'phone', 'website', 'pincode']):
            break
        address_lines.append(line)
    data['Address'] = ' '.join(address_lines).strip()
    
    # Extract other fields using regex
    email_match = re.search(r'Email\s*:\s*([^\s@]+(?:\[at\]|@)[^\s@]+(?:\[dot\]|\.)[^\s@]+)', text, re.IGNORECASE)
    if email_match:
        data['Email'] = email_match.group(1).replace('[at]', '@').replace('[dot]', '.')
    
    phone_match = re.search(r'Phone\s*:\s*([+\d\s-]+)', text)
    if phone_match:
        data['Phone'] = phone_match.group(1).strip()
    
    website_match = re.search(r'Website(?: Link)?\s*:\s*(https?://[^\s]+)', text, re.IGNORECASE)
    if website_match:
        data['Website'] = website_match.group(1).strip()
    
    pincode_match = re.search(r'Pincode\s*:\s*(\d{6})', text)
    if pincode_match:
        data['Pincode'] = pincode_match.group(1).strip()
    
    return data

def scrape_thrissur_hospitals() -> List[Dict[str, str]]:
    """Scrape hospital data from Thrissur district website"""
    url = "https://thrissur.nic.in/en/public-utility-category/hospitals/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("Fetching data from website...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print("Parsing HTML content...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try different ways to find the main content
        main_content = soup.find('div', class_='entry-content') or \
                     soup.find('div', class_='content') or \
                     soup.find('div', id='content') or \
                     soup.find('article')
        
        if not main_content:
            print("Warning: Could not find main content div using standard selectors")
            print("Trying alternative approach...")
            main_content = soup.find('div', role='main') or soup.find('main') or soup
        
        hospitals = []
        current_hospital = []
        
        # Get all text elements
        text_elements = main_content.find_all(['p', 'div', 'h3', 'h4'])
        
        print(f"Found {len(text_elements)} potential text elements to process...")
        
        for element in text_elements:
            text = element.get_text().strip()
            if not text:
                continue
                
            # Check if this looks like a new hospital entry
            if (len(text.split()) <= 5 or 
                any(word in text.lower() for word in ['hospital', 'medical', 'institute', 'centre', 'clinic'])):
                if current_hospital:
                    hospital_text = '\n'.join(current_hospital)
                    hospital_data = extract_hospital_data(hospital_text)
                    if hospital_data['Name']:  # Only add if we got a name
                        hospitals.append(hospital_data)
                    current_hospital = []
            current_hospital.append(text)
        
        # Add the last hospital
        if current_hospital:
            hospital_text = '\n'.join(current_hospital)
            hospital_data = extract_hospital_data(hospital_text)
            if hospital_data['Name']:
                hospitals.append(hospital_data)
        
        return hospitals
    
    except Exception as e:
        print(f"Error scraping data: {str(e)}")
        return []

if __name__ == "__main__":
    print("Starting Thrissur Hospitals Scraper...")
    hospitals = scrape_thrissur_hospitals()
    
    if hospitals:
        df = pd.DataFrame(hospitals)
        output_file = "thrissur_hospitals.csv"
        df.to_csv(output_file, index=False)
        print(f"\nSuccessfully saved data for {len(hospitals)} hospitals to {output_file}")
        print("\nFirst 5 entries:")
        print(df.head())
    else:
        print("\nNo hospital data found. Possible reasons:")
        print("- Website structure may have changed")
        print("- The content is loaded dynamically with JavaScript")
        print("- The website is blocking scrapers")
        print("\nTry visiting the page manually to verify content exists:")
        print("https://thrissur.nic.in/en/public-utility-category/hospitals/")
