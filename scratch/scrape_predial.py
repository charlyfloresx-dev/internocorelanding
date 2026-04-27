import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_predial(clave):
    session = requests.Session()
    
    url = "https://pagos.tijuana.gob.mx/predialTj/Default.aspx"
    try:
        response = session.get(url, verify=False, timeout=10)
    except Exception as e:
        print("Failed to load page:", e)
        return
        
    if response.status_code != 200:
        print("Failed to get main page")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        viewstate = soup.find('input', {'id': '__VIEWSTATE'})['value']
        eventvalidation = soup.find('input', {'id': '__EVENTVALIDATION'})['value']
        viewstategenerator = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value']
    except Exception as e:
        print("Failed to find ASP.NET hidden fields:", e)
        return
        
    print("Got tokens, sending POST...")
    
    data = {
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategenerator,
        '__EVENTVALIDATION': eventvalidation,
        'ctl00$MainContent$txtClave': clave,
        'ctl00$MainContent$btnAgregar': 'Agregar'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': url
    }
    
    post_resp = session.post(url, data=data, headers=headers, verify=False)
    
    if post_resp.status_code == 200:
        print("POST successful. Parsing results...")
        post_soup = BeautifulSoup(post_resp.text, 'html.parser')
        
        # Searching for the data
        if "MONTOYA" in post_resp.text:
            print("SUCCESS! Found the owner name.")
            # Try to extract the specific row
            table = post_soup.find('table', {'id': 'MainContent_GridConceptos'})
            if table:
                print("Found data table!")
        else:
            print("Did not find MONTOYA. Outputting some text nodes:")
            for span in post_soup.find_all('span', id=lambda x: x and 'MainContent' in x):
                print(span.get('id'), ":", span.get_text(strip=True))
    else:
        print("POST failed:", post_resp.status_code)

if __name__ == "__main__":
    scrape_predial("PK020119")
