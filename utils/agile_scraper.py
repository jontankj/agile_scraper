import requests
from bs4 import BeautifulSoup
import json
import re
import logging
import datetime

# logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(
   level=logging.INFO,
   format="%(asctime)s: %(name)s [%(levelname)s] %(message)s")


def regex_matcher(
                  # rows: list,
                  string_obj: str,
                  regex_pattern: str,
                  match_group: int) -> str:
    """Returns you the match by regex based on 
    regex_pattern and match_group. Designed to work through
    a list

    Args:
        string_obj (str): string that you are searching  in
        regex_pattern (str): the pattern you want to search for
        match_group (int): 0 for the first match, etc

    Returns:
        str: returns the string (date, avg_peak, avg_offpeak)
    """
    match = re.search(regex_pattern, string_obj)
    if match:
        return match.group(match_group)
    return None


# Scrape a page and return extracted text
def scrape_page(url):
  response = requests.get(url)
  soup = BeautifulSoup(response.text, 'html.parser')
  text = soup.get_text()
  return text


# Get list of all internal links on a page   
def get_links(url):
  response = requests.get(url)
  soup = BeautifulSoup(response.text, 'html.parser')
  links = []
  for link in soup.find_all('a'):
    href = link.get('href')
    if href.startswith('/'):
      links.append(url + href)
  return links


# Crawl and scrape pages starting from a root URL 
def crawl(root_url: str) -> str:
  content = {}
  queue = [root_url]
  while queue:
    url = queue.pop(0) 
    filename = re.sub(r'[\\/*?:"<>|]', '', url)
    if url not in content:
      content[url] = scrape_page(url)
      # save_to_text(filename,content[url])
      links = get_links(url)
      for link in links:
        if link not in content:
          queue.append(link)
  return content


def scrape_clean(webpage: str = "https://agileprices.co.uk/?region=E") -> json:
  """At 1600 agileprices updates tomorrows Agile Pricing.
  This function scrapes the average prices for the current
  month and returns it as a json in the following format
  {2023-12-20: 0.15}
  Big movements of +/-20% should be used to trigger downstream actions
  Format types are: {datetime: float}

  Args:
      webpage (str): (optional) Default webpage is for Agile tariff in
      West Midlands region

  Returns:
      json: Date and average electric pricing
  """
  content = scrape_page(webpage)
  data = content.split("\n")
  rows = [r.split(',') for r in data]

  filtered_rows = []

  for row in rows:
      if row and (row[0].startswith("Average price") or row[0].startswith("00:00")):
          filtered_rows.append(row)


  avg_prices = {}
  date = None
  avg = None
  # avg_peak = None
  # avg_offpeak = None
  date_list = []
  avg_list = []
  # avg_peak_list = []
  # avg_offpeak_list = []


  for i, filtered_row in enumerate(filtered_rows):
      # iterate on the contents of each row (going from list to string)
      for e,string_obj in enumerate(filtered_row):
        # creating list of dates
        date_pattern = r"\d{2} \w+ \d{4}"
        date_str = regex_matcher(
                            # filtered_row,
                            string_obj,
                            date_pattern,
                            0)
        if date_str is not None:
            date_object = datetime.datetime.strptime(date_str, "%d %B %Y")
            date = date_object.strftime("%Y-%m-%d")
            date_list.append(date)
        # creating list of average_prices
        avg_regex = r"Average price for day = (\d+\.\d+p)"
        avg_string = regex_matcher(
                        # filtered_row,
                        string_obj,
                        avg_regex,
                        1)
        if avg_string is not None:
            avg_string = avg_string.rstrip("p")
            # converting to float
            avg = round(float(avg_string),1)
            avg_list.append(avg)

        # peak and off peak data draw
        # peak_regex = r"Avg Peak = (\d+\.\d+p)"
        # avg_peak = regex_matcher(
        #                     # filtered_row,
        #                     string_obj,
        #                     peak_regex,
        #                     1)
        # if avg_peak is not None:
        #     avg_peak_list.append(avg_peak)
        # offpeak_regex = r"Avg Offpeak = (\d+\.\d+p)"
        # avg_offpeak = regex_matcher(
        #                     # filtered_row,
        #                     string_obj,
        #                     offpeak_regex,
        #                     1)
        # if avg_offpeak is not None:
        #     avg_offpeak_list.append(avg_offpeak)
            # prices[old_date] = {"avg peak": avg_peak, "avg offpeak": avg_offpeak}

  # logger.info(f"dates {date_list} with length {len(date_list)}")
  # logger.info(f"avg_peak_list {avg_peak_list} with length {len(avg_peak_list)}")

  # removing the average monthly offpeak value as not applicable
  # del avg_offpeak_list[0]
  # logger.info(f"avg_offpeak_list {avg_offpeak_list} with length {len(avg_offpeak_list)}")
  # prices  = {date: {'avg': avg} for date, avg in zip(date_list, avg_list)}
  avg_prices  = {date: avg for date, avg in zip(date_list, avg_list)}
  # prices  = {date: {'peak': peak, 'offpeak': offpeak} for date, peak, offpeak in zip(date_list, avg_peak_list, avg_offpeak_list)}
  logger.info(f"\n\n\nprices json looks like:\n")
  logger.info(avg_prices)
  return avg_prices

scrape_clean("https://agileprices.co.uk/?region=E")