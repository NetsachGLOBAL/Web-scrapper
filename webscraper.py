from flask import Flask, render_template, request
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse

app = Flask(__name__)

# Define a list of social media domains to filter
SOCIAL_MEDIA_DOMAINS = [
    'twitter.com', 'facebook.com', 'instagram.com', 'linkedin.com', 'youtube.com',
    'pinterest.com', 'snapchat.com', 'tiktok.com', 'reddit.com', 'wa.me', 'whatsapp.com'
]

def is_social_media_link(link):
    """Check if the link contains any social media domains."""
    return any(domain in link for domain in SOCIAL_MEDIA_DOMAINS)

def extract_emails_and_phones(text):
    """Extract emails and phone numbers from the given text."""
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_regex = r'\+?\d[\d -]{8,}\d'
    
    emails = re.findall(email_regex, text)
    phones = re.findall(phone_regex, text)
    
    return emails, phones

def normalize_url(url):
    """Normalize the URL by ensuring it has a scheme."""
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = 'https://' + url  # Default to https
    elif parsed_url.scheme not in ['http', 'https']:
        url = 'https://' + url



def fetch_links_and_contact_info(url):
    """Fetch links, emails, and phones from a static page."""
    url = normalize_url(url)
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if is_social_media_link(a['href'])]
        text_content = soup.get_text()
        emails, phones = extract_emails_and_phones(text_content)

        return links, emails, phones
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return [], [], []

def fetch_links_and_contact_info_with_selenium(url):
    """Fetch links, emails, and phones from a dynamic page using Selenium."""
    url = normalize_url(url)
    try:
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        
        driver.get(url)
        driver.implicitly_wait(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if is_social_media_link(a['href'])]
        text_content = soup.get_text()
        emails, phones = extract_emails_and_phones(text_content)

        driver.quit()

        return links, emails, phones
    except Exception as e:
        print(f"An error occurred with Selenium: {e}")
        return [], [], []

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle form submission and display results on the same page."""
    if request.method == 'POST':
        url = request.form['url']

        if '#/' in url:
            links, emails, phones = fetch_links_and_contact_info_with_selenium(url)
        else:
            links, emails, phones = fetch_links_and_contact_info(url)
        
        return render_template('index.html', url=url, links=links, emails=emails, phones=phones)

    # Initial GET request, no results yet
    return render_template('index.html', url=None, links=None, emails=None, phones=None)

if __name__ == "__main__":
    app.run(debug=True)
