import re
from time import sleep
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def parse_html(html):
    """Parse content from updated OpenTable restaurant listing HTML."""
    data, item = pd.DataFrame(), {}
    soup = BeautifulSoup(html, 'lxml')
      
    for i, resto in enumerate(soup.find_all('div', class_='-kEmfWQTmGY-')):
        try:
            # Price
            price_span = resto.find('span', class_='fAwKcPtLqSo-')  # Outer price span
            if price_span:
                price_text = ''.join(price_span.find_all(string=True, recursive=False)).strip()
                item['price'] = price_text.count('$')
            else:
                item['price'] = 'NA'

           # Extract star level
            star_div = resto.find('div', class_='yEKDnyk-7-g-')  # Locate the specific star rating div
            if star_div:
                #print(f"Found star_div: {star_div}")  # Debugging
                if 'aria-label' in star_div.attrs:  # Check if aria-label exists
                    star_label = star_div['aria-label']  # Extract aria-label
                    item['star_level'] = star_label.split()[0]  # Extract numeric value (e.g., "4.7")
                    print(f"Extracted star level: {item['star_level']}")  # Debugging
                else:
                    print("aria-label not found in star_div attributes.")
                    item['star_level'] = 'NA'
            else:
                print("Star div not found.")
                item['star_level'] = 'NA'


            # Cuisine and Location
            cuisine_location = resto.find('div', class_='_4QF0cXfwR9Q-')
            if cuisine_location:
                cuisine_location_text = cuisine_location.text.split(' • ')
                item['cuisine'] = cuisine_location_text[1].strip() if len(cuisine_location_text) > 1 else 'NA'
                item['location'] = cuisine_location_text[2].strip() if len(cuisine_location_text) > 2 else 'NA'
            else:
                item['cuisine'] = 'NA'
                item['location'] = 'NA'

            # Add item to DataFrame
            data[i] = pd.Series(item)

        except Exception as e:
            print(f"Error parsing restaurant info: {e}")

    return data.T


def slow_scroll(driver, scroll_pause_time=1):
    """
    Scroll the page slowly to reveal dynamically loaded content.
    :param driver: Selenium WebDriver instance
    :param scroll_pause_time: Time (in seconds) to wait after each scroll
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down by 500 pixels
        driver.execute_script("window.scrollBy(0, 1000);")
        sleep(scroll_pause_time)  # Pause to allow new content to load

        # Get the new height after scrolling
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If no new content is loaded, break the loop
            break
        last_height = new_height

# Configure Selenium with SSL options
chrome_options = Options()
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--ignore-ssl-errors")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--allow-running-insecure-content")

# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)
url = "https://www.opentable.com/new-york-restaurant-listings"
driver.get(url)

# Set up variables
page = collected = 0

try:
    while True:
        # Scroll through the page to load all listings
        # previous_height = driver.execute_script("return document.body.scrollHeight")
        # while True:
        #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #     sleep(2)  # Wait for new content to load
        #     current_height = driver.execute_script("return document.body.scrollHeight")
        #     if current_height == previous_height:
        #         break
        #     previous_height = current_height

        # Handle pagination
        try:
            # Scroll to the bottom of the page to make the "Next" button visible
            slow_scroll(driver, 1)
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)  # Wait for any dynamic content to load

            # Parse the HTML of the fully loaded page
            full_html = driver.page_source
            new_data = parse_html(full_html)

            if new_data.empty:
                print(f"Page {page}: No data scraped!")
                break

            # Save scraped data to CSV
            if page == 0:
                new_data.to_csv('results.csv', index=False)
            else:
                new_data.to_csv('results.csv', index=False, header=None, mode='a')

            page += 1
            collected += len(new_data)
            print(f"Page: {page} | Downloaded: {collected}")

            # Wait for the "Next" button to become clickable
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-test="pagination-next"]'))
            )
            # Click the "Next" button
            next_button.click()
        except Exception as e:
            print("No more pages or an error occurred:", e)
            break
finally:
    driver.quit()

# Load and print final dataset
try:
    restaurants = pd.read_csv('results.csv')
    print(restaurants)
except FileNotFoundError:
    print("No results.csv file created. No data was scraped.")



