# dependencies: database
from dbconfig import dbconfig
import mysql.connector

# dependencies: scraping and parsing
import requests
import re
import ftfy
import html
import time
import io
from pdfminer.high_level import extract_text
from selenium import webdriver
from bs4 import BeautifulSoup, Comment, Tag, ProcessingInstruction
from datetime import datetime

# speedup between midnight and 6 am
speedup = 6 > datetime.now().hour

# connect to maria db
try:
    conn = mysql.connector.connect(**dbconfig)
    db = conn.cursor(dictionary=True)
except mysql.connector.Error as e:
    print(e)

# returns clean html content
def clean_html(content):

    # sanity check
    if not content.strip():
        return ''

    # soup' up, utiilize main/article if possible
    soup = BeautifulSoup(content, 'html.parser')
    soup = soup.find('body') or soup
    soup = soup.find('main') or soup

    # remove comments and processing instructions (like random <?xml in the middle of the content)
    specials = soup.find_all(string=lambda text: isinstance(text, (Comment, ProcessingInstruction)))
    for special in specials:
        special.extract()

    # define noisy roles
    noise_roles = ['dialog', 'navigation', 'banner', 'alert']

    # define noisy classes
    noise_classes = ['crumb', 'foot', 'sidebar', 'side-bar', 'topbar', 'top-bar', 'login', 'loading', 'captcha', 'signup'
                     'disabled', 'testimonial', 'contact', 'navigation', 'glassdoor', 'language',
                     'topmenu', 'top-menu', 'globalmenu', 'global-menu', 'top-level-menu', 'shortcuts', 'menu_header',
                     'social-media', 'logo__title', 'toast__message', 'social-network']

    # define noisy tags
    noise_tags = ['head', 'script', 'noscript', 'style', 'code', 'video', 'audio', 'media', 'picture', 'object', 'figure',
                  'svg', 'textarea', 'button', 'dialog', 'footer', 'legend', 'fieldset', 'nav', 'aside', 'template',
                   'symbol', 'path', 'time', 'source', 'label']

    #noise_roles=[]
    #noise_classes=[]
    #noise_tags=[]

    # define tags with structural importance
    structure_tags = ['div', 'p', 'li', 'h1', 'h2', 'h3', 'h4']

    # decompose, unwrap or remove attributes based on tag, id, class, role
    for tag in soup.find_all(True):
        if tag.name == 'br':
            pass
        elif tag.name in noise_tags:
            tag.decompose()
        elif all(not isinstance(child, Tag) and not str(child).strip() for child in tag.children):
            tag.decompose()
        elif tag.has_attr('id') and any(c in tag['id'].lower() for c in noise_classes):
            tag.decompose()
        elif tag.has_attr('class') and any(c in ' '.join(tag['class']).lower() for c in noise_classes):
            tag.decompose()
        elif tag.has_attr('role') and tag.get('role').lower().strip() in noise_roles:
            tag.decompose()
        elif tag.name not in structure_tags:
            tag.insert_before(' ')
            tag.insert_after(' ')
            tag.unwrap()
        else:
            tag.attrs = {}

    # unwrap remaining structure tags with only tags as children, prioritize li
    while True:
        changed = False
        for tag in soup.find_all(structure_tags):
            if tag.name != 'li' and all(isinstance(child, Tag) or not str(child).strip() for child in tag.children):
                tag.insert_before(' ')
                tag.insert_after(' ')
                tag.unwrap()
                changed = True
            elif tag.parent.name == 'li':
                tag.insert_before(' ')
                tag.insert_after(' ')
                tag.unwrap()
                changed = True
        if not changed:
            break

    # decode, fix and normalize white space
    content = soup.decode_contents()
    content = ftfy.fix_text(content)
    content = re.sub(r'&gt;|&lt;|&#0*6[02];', ' ', content)
    content = html.unescape(content)
    content = re.sub(r'\s+', ' ', content)
    content = content.replace('<li>', '• ')
    content = content.replace('•', '\n•')
    content = re.sub(r'\{+[^\}]*\}+|\<+[^\>]*\>+', '\n', content)
    content = content.replace('\n-', '\n• ')
    content = re.sub(r'\s*\n\s*', '\n', content)
    content = re.sub(r'\n(\W*\n)+', '\n', content)
    content = re.sub(r' +', ' ', content).strip()

    # done!
    return content

# returns clean pdf content
def clean_pdf(content):

    # sanity check
    if not content.strip():
        return ''

    # decode, fix and normalize white space
    content = ftfy.fix_text(content)
    content = re.sub(r'\n\s*[•\-]', '\n', content)
    content = '\n'.join([re.sub(r'\s+', ' ', c).strip() for c in content.split('\n')])
    content = re.sub(r'(?<=\S)\- *\n\s*', '', content)
    content = re.sub(r'\n(?![A-ZÆØÅ•\-\"\'\n])', ' ', content)
    content = re.sub(r'\s*\n\s*', '\n', content)
    content = re.sub(r'[ \t\x0B\f\r]+', ' ', content)
    content = re.sub(r'\n(\W*\n)+', '\n', content)
    content = content.strip()

    # done!
    return content

# init requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Chrome OS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
})

# init selenium
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

# recursive selenium
def deep_content(driver):
    content = clean_html(driver.page_source)
    if len(content) > 255:
        return content
    for index, _ in enumerate(driver.find_elements(webdriver.common.by.By.TAG_NAME, 'iframe')):
        driver.switch_to.frame(index)
        content = deep_content(driver)
        if len(content) > 255:
            return content
    driver.switch_to.parent_frame()
    return ''

# get ads for harvesting
db.execute('SELECT * FROM jobads WHERE crawled IS NULL LIMIT %s',
           [10 if speedup else 10])
jobads = db.fetchall()

# go through all ads
for jobad in jobads:
    
    # (re)set content
    content = ''
    is_pdf = False

    # request archived version (simple)
    try:
        response = session.get(jobad['url'])
        response.raise_for_status()
        content = clean_html(response.content.decode())
        content = content if len(content) > 255 else ''
    except:
        content = ''
    
    # request original version (simple + check pdf)
    if not content:
        try:
            response = session.get(jobad['real_url'])
            response.raise_for_status()
            is_pdf = (jobad['real_url'].lower()[-4:] == '.pdf'
                      and (response.headers.get('Content-Type') == 'application/pdf'
                           or response.content.startswith(b'%PDF-')))
            if is_pdf:
                content = clean_pdf(extract_text(io.BytesIO(response.content)))
            else:
                content = clean_html(response.content.decode())
            content = content if len(content) > 255 else ''
        except:
            content = ''

    # request deep content (selenium, javascript, iframe, etc)
    if not content and not is_pdf:
        try:
            driver.implicitly_wait(2)
            driver.get(jobad['real_url'])
            time.sleep(1)
            content = deep_content(driver)
        except:
            content = ''
    
    # update
    db.execute('UPDATE jobads SET content = %s, crawled = NOW() WHERE id = %s',
               [content[:32768], jobad['id']])
    conn.commit()

# kill selenium and db connection
driver.quit()
db.close()
conn.close()
