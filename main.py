import pandas as pd
import socket
import netaddr
import logging
import requests
import json
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tldextract

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s: %(message)s"
)

umbrella_top_million = pd.read_csv('top_website_data/top-1m.csv', names=['Ranking', 'Domain'], sep=',', index_col=False, header=0)
test_df = umbrella_top_million.head(50)
#TO DO - Add in the Majestic ones too
#majestic_top_million = pd.read_csv('top_website_data/majestic_million.csv')
domains_to_visit = test_df['Domain'].tolist()
results_df = pd.DataFrame(columns=['Domain_Visited', 'Referenced_Domain'])
results = set()
for index, item in enumerate(domains_to_visit):
    #item = "newsnow.co.uk"
    #loop over the domains of interest
    #do a dns lookup to ensure the domain is still up and about
    logging.debug(f'Currently Processing {item}...')
    ip_addr = socket.gethostbyname(item)
    logging.debug(f'IP Address for {item}: {ip_addr}...')
    #check if the ip address is real
    try:
        ip_addr = netaddr.IPAddress(ip_addr)
    except netaddr.core.AddrFormatError:
        logging.error(f'Not an IP Address {ip_addr}, Skipping...')
        continue
    #append https and try request, if that doesn't work go to http
    domain_and_method = 'https://' + item
    """
    #append https and try request, if that doesn't work go to http
    domain_and_method = 'https://' + 'newsnow.co.uk/'
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    headers = {'User-Agent': user_agent}
    r = requests.get(domain_and_method, headers=headers)
    with open('sample.json', 'w') as output:
        output.write(r.text)
    #parse to beaut soup
    soup = BeautifulSoup(r.text, 'html.parser')
    hrefs_bs = []
    item = "newsnow.co.uk"
    a_tags_with_href = soup.find_all('a', href=True)
    all_iframes = soup.find_all('iframe')
    iframe_tags = soup.find_all('iframe', src=True)
    link_tags_with_href = soup.find_all('link', href=True)
    script_tags = soup.find_all('script', src=True)
    hrefs_bs.append([a_tag['href'] for a_tag in a_tags_with_href if "http" in a_tag['href'] and item not in a_tag['href']])
    hrefs_bs.append([link_tag['href'] for link_tag in link_tags_with_href if item not in link_tag['href']])
    hrefs_bs.append([iframe_tag['src'] for iframe_tag in iframe_tags if "http" in iframe_tag['src'] and item not in iframe_tag['src']])
    hrefs_bs.append([script_tag['src'] for script_tag in script_tags])"""
    hrefs_sel = []
    chrome_options = Options()
    chrome_options.add_argument("--headless") # doesn't open the browser window
    chrome_options.add_argument("--log-level=2") # set log leve lto errors only
    browser = webdriver.Chrome('./ChromeDriver/chromedriver.exe', options=chrome_options)
    browser.get(domain_and_method)
    browser.implicitly_wait(50)
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    a_tags_with_href = soup.find_all('a', href=True)
    all_iframes = soup.find_all('iframe')
    iframe_tags = soup.find_all('iframe', src=True)
    script_tags = soup.find_all('script', src=True)
    link_tags_with_href = soup.find_all('link', href=True)
    meta_tag_category = [tag for tag in soup.find_all('meta', {"name":"category"}) if tag['name'] == "category"]
    meta_tag_keywords = soup.find_all('meta', {"name":"keywords"})
    print(meta_tag_category)
    print(meta_tag_keywords)
    keywords = [item['content'] for item in meta_tag_keywords]
    category = [item['content'] for item in meta_tag_category]
    hrefs_sel.extend([a_tag['href'] for a_tag in a_tags_with_href if "http" in a_tag['href'] and item not in a_tag['href']])
    hrefs_sel.extend([link_tag['href'] for link_tag in link_tags_with_href if item not in link_tag['href']])
    hrefs_sel.extend([iframe_tag['src'] for iframe_tag in iframe_tags])
    hrefs_sel.extend([script_tag['src'] for script_tag in script_tags])
    ##Got a list of all the references on the page, now need to find the top level domains
    #use the cache file in order to stop it calling out with a HTTP request everytime
    for full_domain in hrefs_sel:
        extracted = tldextract.extract(full_domain)
        main_domain = '.'.join([extracted.domain, extracted.suffix])
        if main_domain != '.':
            logging.debug(f'About to add {main_domain} to list for {item}...')
            results.add((item, str(keywords), str(category), main_domain))
    logging.debug(f'Completed {item}...')
    browser.close()
browser.quit()
results_df = pd.DataFrame(list(results), columns=['Domain_Visited', 'Domain_Visited_Keywords', 'Domain_Visied Category', 'Referenced_Domain'])



    

    

