import pandas as pd
import socket
import netaddr
import logging
import requests
import json
from bs4 import BeautifulSoup
import re
from selenium import webdriver

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s: %(message)s"
)

umbrella_top_million = pd.read_csv('top_website_data/top-1m.csv', names=['Ranking', 'Domain'], sep=',', index_col=False, header=0)
test_df = umbrella_top_million.head(1)
#TO DO - Add in the Majestic ones too
#majestic_top_million = pd.read_csv('top_website_data/majestic_million.csv')
domains_to_visit = test_df['Domain'].tolist()
for index, item in enumerate(domains_to_visit):
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
    browser = webdriver.Chrome('./ChromeDriver/chromedriver.exe')
    browser.get(domain_and_method)
    browser.implicitly_wait(100)
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    a_tags_with_href = soup.find_all('a', href=True)
    all_iframes = soup.find_all('iframe')
    iframe_tags = soup.find_all('iframe', src=True)
    script_tags = soup.find_all('script', src=True)
    link_tags_with_href = soup.find_all('link', href=True)
    hrefs_sel.append([a_tag['href'] for a_tag in a_tags_with_href if "http" in a_tag['href'] and item not in a_tag['href']])
    hrefs_sel.append([link_tag['href'] for link_tag in link_tags_with_href if item not in link_tag['href']])
    hrefs_sel.append([iframe_tag['src'] for iframe_tag in iframe_tags if item not in iframe_tag['src']])
    hrefs_sel.append([script_tag['src'] for script_tag in script_tags])


    

    

