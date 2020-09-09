import io
import requests
import zipfile
import argparse
import asyncio
import csv
from bs4 import BeautifulSoup
import tldextract

from arsenic import get_session
from arsenic.browsers import Firefox
from arsenic.services import Geckodriver
class Error(Exception):
    """Base class for other exceptions"""
    pass

class ValueTooLargeError(Error):
    """Raised when the input value is too large"""
    pass

class Anvertising:
    def __init__(self, adDomainLists=None, searchList=None, outputDir=None):
        print("Initialising Anvertising...")
        self.adDomainFiles = adDomainLists if adDomainLists is not None else None
        #Chnage this to enable single domains
        searchFile = searchList if searchList is not None else self.getTopMillionDomains("top-1m.csv")
        self.searchList = open(searchFile, "r")
        self.outputDir = outputDir if outputDir is not None else "output"
        self.adDomains = self.updateAdDomainList() if self.adDomainFiles is None else None #Need to create a function here to read in file without response

    def updateAdDomainList(self):
        #Known good Advert Blocking Lists firebog.net
        #TODO Scrape the page instead of hardcoding this.
        advertisingDomains = []
        adBlockLists = [
            "https://adaway.org/hosts.txt",
            "https://v.firebog.net/hosts/AdguardDNS.txt",
            "https://v.firebog.net/hosts/Admiral.txt",
            "https://raw.githubusercontent.com/anudeepND/blacklist/master/adservers.txt",
            "https://s3.amazonaws.com/lists.disconnect.me/simple_ad.txt",
            "https://v.firebog.net/hosts/Easylist.txt",
            "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext",
            "https://raw.githubusercontent.com/FadeMind/hosts.extras/master/UncheckyAds/hosts",
            "https://raw.githubusercontent.com/bigdargon/hostsVN/master/hosts"
        ]
        for adBlockList in adBlockLists:
            r = requests.get(adBlockList)
            if r.status_code == 200 and r.content is not None:
                advertisingDomains.extend(self.consumeAdDomainList(r.content))
            else:
                print(f"Issue Initialising {adBlockList}...")
        print("Finished Initialising AdBlock Lists...")
        return advertisingDomains

    def consumeAdDomainList(self, responseContent):
        domains = []
        for line in responseContent.decode('utf-8').split('\n'):
            if len(line) > 0:
                if line[0] != "#":
                    #adblock lists have "127.0.0.1 domain.domain" because it redirects ads to localhost where it gets blackholed
                    if len(line.split(" ")) == 2:
                        domain = line.split(" ")[1]
                        domains.append(domain)
        return domains

    def getTopMillionDomains(self, filename):
        #Alexa list is quite good http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip
        print("Collecting Top Million Alexa List...")
        r = requests.get("http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip")
        if r.status_code == 200:
            #cast data to io reader for zipfile functionarlity
            responseReader = io.BytesIO(r.content)
            zipfile_ob = zipfile.ZipFile(responseReader)
            zipfile_ob.extractall()
        else:
            print("Error Updating Top 1m List...")
        print("Top Million Alexa List Collected...")
        return "top-1m.csv"

    def topMillionDomainGen(self, blockSize):
        #TODO I might be able to do this without unzipping it
        #Generator to yield domains instead of reading them all into memory
        block = []
        for line in self.searchList:
            if "," in line:
                block.append(val[1] for val in line.split(","))
            else:
                block.append(line)
            if len(block) == blockSize:
                yield block
                block = []
        if block:
            yield block

    def getDomain(self):
        for line in self.searchList:
            if "," in line:
                domain = line.split(",")[1].replace("\n", "")
            else:
                domain = line
            yield domain

    def parsePageSourceForAds(self, pageSource, domain):
        print(f"Parsing {domain}")
        hrefs_sel = []
        results = set()
        #Make sure to install the bs4 html parser
        soup = BeautifulSoup(pageSource, 'html.parser')
        print(pageSource)
        a_tags_with_href = soup.find_all('a', href=True)
        all_iframes = soup.find_all('iframe')
        iframe_tags = soup.find_all('iframe', src=True)
        script_tags = soup.find_all('script', src=True)
        link_tags_with_href = soup.find_all('link', href=True)
        meta_tag_category = [tag for tag in soup.find_all('meta', {"name":"category"}) if tag['name'] == "category"]
        meta_tag_keywords = soup.find_all('meta', {"name":"keywords"})
        hrefs_sel.extend([a_tag['href'] for a_tag in a_tags_with_href if "http" in a_tag['href'] and domain not in a_tag['href']])
        hrefs_sel.extend([link_tag['href'] for link_tag in link_tags_with_href if domain not in link_tag['href']])
        hrefs_sel.extend([iframe_tag['src'] for iframe_tag in iframe_tags])
        hrefs_sel.extend([script_tag['src'] for script_tag in script_tags])
        ##Got a list of all the references on the page, now need to find the top level domains
        #use the cache file in order to stop it calling out with a HTTP request everytime
        print(f"Got a list of Ads for {domain}...Results are {hrefs_sel}...")
        for full_domain in hrefs_sel:
            print(f"{domain}: advert result {full_domain}")
            extracted = tldextract.extract(full_domain)
            main_domain = '.'.join([extracted.subdomain, extracted.domain, extracted.suffix])
            print(f"{domain}: main domain = {main_domain}")
            if main_domain != '..':
                if main_domain[0] == '.':
                    main_domain = main_domain[1:]
                #TODO if there is no subdomain it become .domain.com so need to fix that
                print(f"About to Compare Links for {domain} to Ad List...")
                ad_domain = True if main_domain in self.adDomains else False
                results.add((domain, main_domain, ad_domain, False))
                print(f"Results for {domain}: {results}")
        with open(f"{self.outputDir}/Anvertising.csv",'a') as out:
            csv_out = csv.writer(out)
            for row in results:
                csv_out.writerow(row)

    async def getPage(self, domain, semaphore):
        # Runs geckodriver and starts a firefox session
        firefox_browser = Firefox(**{'moz:firefoxOptions': {'args': ['-headless']}})
        domain = "https://" + domain
        print(f"Getting Domain {domain}")
        async with semaphore, get_session(Geckodriver(), firefox_browser) as session:
            print(f"About to Parse page for {domain}...")
            await session.get(domain)
            self.parsePageSourceForAds(await session.get_page_source(), domain)

    async def main(self):
        with open(f"{self.outputDir}/Anvertising.csv", "w") as out:
            writer = csv.writer(out)
            writer.writerow(['Domain_Visited', 'Referenced_Domain', 'Advertising_Domain', 'Error'])
        print("Collecting Asyncio Tasks")
        semaphore = asyncio.Semaphore(10)
        tasks = (asyncio.ensure_future(self.getPage(domainBlock, semaphore)) for domainBlock in self.getDomain())
        results = await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Anvertiser!', description="""This will scrape websites looking for advertising domains.
    This will hopefully find the biggest Advertising exchanges in the world.
    """
    )
    #parser.add_argument("domain", type=str,
    #                help="domains to be analysed")
    parser.add_argument(
                        "-od", "--outputDirectory", 
                        help="Assign an output directory for the csv",
                        metavar="OUTPUT_DIRECTORY",
                        dest='outputDir'
                        )
    parser.add_argument(
                        "-i", "--inputFile",
                        help="Manually load in domain file if you have one",
                        metavar="DOMAIN_FILE",
                        dest='domainFile'
                        )
    args = parser.parse_args()
    anvertising = Anvertising(adDomainLists=None, searchList=args.domainFile, outputDir=args.outputDir)

    print("About to start Asyncio Loop")
    #Python 3.7 equivalent
    r = asyncio.run(anvertising.main(), debug=True)
    # loop = asyncio.get_event_loop()
    # result = loop.run_until_complete(anvertising.collectTasks())