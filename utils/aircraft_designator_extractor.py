# aircraft_info_search/utils/aircraft_designator_extractor.py
# This program will extract data from https://www2023.icao.int/publications/DOC8643/Pages/Search.aspx
# This is included in the program for the ability to update /data/icao_aircraft.db when ICAO updates their list.


"""
ICAO Aircraft Type Designator Scraper
Extracts all aircraft data from the official ICAO database
"""

import time
import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ICAOScraper:
    def __init__(self, headless=True): # headless=True: run Chrome invisibly
        """Initialize the scraper with Chrome options"""
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.driver = None
        self.wait = None
        
    def start_driver(self):
        """Start the Chrome driver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            print("Chrome driver started successfully")
        except Exception as e:
            print(f"Error starting Chrome driver: {e}")
            print("Make sure you have Chrome and ChromeDriver installed")
            raise
    
    def load_page(self):
        """Load the ICAO search page and set to 100 entries per page"""
        url = "https://www2023.icao.int/publications/DOC8643/Pages/Search.aspx"
        print(f"Loading page: {url}")
        self.driver.get(url)
        
        # Wait for the table to load
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            print("Page loaded successfully")
            time.sleep(3)  # Additional wait for JavaScript to fully load
            
            # Try to change to 100 entries per page
            self.set_entries_per_page()
            
        except TimeoutException:
            print("Timeout waiting for page to load")
            raise
    
    def set_entries_per_page(self):
        """Try to set the page to show 100 entries instead of 10"""
        try:
            print("Attempting to change to 100 entries per page...")
            
            # Look for dropdown or select element that controls entries per page
            selectors_to_try = [
                "select[name*='PageSize']",
                "select[id*='PageSize']", 
                "select[class*='pagesize']",
                "select[aria-label*='entries']",
                ".ms-paging select",
                "select option[value='100']", # as of now 100 is the max available per page
                "[id*='ddlPageSize']"
            ]
            
            for selector in selectors_to_try:
                try:
                    if "option[value='100']" in selector:
                        # Find the parent select of the 100 option
                        option = self.driver.find_element(By.CSS_SELECTOR, selector)
                        select_element = option.find_element(By.XPATH, "./..")
                    else:
                        select_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if select_element.is_displayed():
                        # Try to select 100 entries
                        from selenium.webdriver.support.ui import Select
                        select = Select(select_element)
                        
                        # Try different ways to select 100
                        try:
                            select.select_by_value("100")
                            print("Successfully set to 100 entries per page via select by value")
                            time.sleep(3)  # Wait for page to reload
                            return
                        except:
                            try:
                                select.select_by_visible_text("100")
                                print("Successfully set to 100 entries per page via select by visible text")
                                time.sleep(3)
                                return
                            except:
                                continue
                except:
                    continue
            
            # If dropdown approach fails, try clicking on pagination controls
            print("Dropdown approach failed, trying pagination controls...")
            pagination_links = self.driver.find_elements(By.CSS_SELECTOR, "a, span")
            for link in pagination_links:
                if "100" in link.text and link.is_displayed():
                    try:
                        link.click()
                        print("Clicked 100 entries link")
                        time.sleep(3)
                        return
                    except:
                        continue
            
            print("Could not find way to change entries per page - continuing with default")
            
        except Exception as e:
            print(f"Error setting entries per page: {e}")
            print("Continuing with default page size")
    
    def extract_table_data(self):
        """Extract data from the current page's table"""
        try:
            # Find the table with aircraft data
            table = self.driver.find_element(By.CSS_SELECTOR, "table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            data = []
            header_found = False
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    cells = row.find_elements(By.TAG_NAME, "th")
                
                if len(cells) >= 7:  # Should have 7 columns
                    row_data = [cell.text.strip() for cell in cells]
                    
                    # Skip header row and loading rows
                    if (row_data[0] in ["Manufacturer", "​​Manufacturer"] or 
                        "Loading" in row_data[0] or 
                        not row_data[0]):
                        if not header_found and row_data[0] in ["Manufacturer", "​​Manufacturer"]:
                            header_found = True
                        continue
                    
                    # Only add rows with actual data
                    if row_data[0] and row_data[2]:  # Must have manufacturer and type designator
                        data.append({
                            'manufacturer': row_data[0],
                            'model': row_data[1],
                            'type_designator': row_data[2],
                            'description': row_data[3],
                            'engine_type': row_data[4],
                            'engine_count': row_data[5],
                            'wtc': row_data[6] if len(row_data) > 6 else ''
                        })
            
            print(f"Extracted {len(data)} records from current page")
            return data
            
        except Exception as e:
            print(f"Error extracting table data: {e}")
            return []
    
    def find_next_button(self):
        """Find and return the next page button"""
        try:
            # Look for various possible next button selectors
            next_selectors = [
                "a[title*='Next']",
                "a[aria-label*='Next']",
                ".ms-paging a:last-child",
                "a:contains('Next')",
                "[id*='Next']",
                ".paging-next",
                "a[onclick*='next']"
            ]
            
            for selector in next_selectors:
                try:
                    if selector.startswith("a:contains"):
                        # Use XPath for text-based search
                        elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Next')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            return element
                except:
                    continue
            
            # Try to find pagination controls
            pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, ".ms-paging a, .paging a, [class*='pag'] a")
            for element in pagination_elements:
                text = element.text.lower()
                if 'next' in text or '>' in text or '»' in text:
                    if element.is_displayed() and element.is_enabled():
                        return element
            
            return None
            
        except Exception as e:
            print(f"Error finding next button: {e}")
            return None
    
    def scrape_all_pages(self, max_pages=None):
        """Scrape all pages of aircraft data"""
        all_data = []
        page_num = 1
        
        print("Starting to scrape all pages...")
        
        while True:
            print(f"\n--- Processing Page {page_num} ---")
            
            # Extract data from current page
            page_data = self.extract_table_data()
            if page_data:
                all_data.extend(page_data)
                print(f"Total records so far: {len(all_data)}")
            else:
                print("No data found on this page")
            
            # Check if we've reached the maximum pages limit
            if max_pages and page_num >= max_pages:
                print(f"Reached maximum pages limit: {max_pages}")
                break
            
            # Try to find and click the next button
            next_button = self.find_next_button()
            if next_button:
                try:
                    print("Clicking next page...")
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)  # Wait for page to load
                    
                    # Wait for new data to load
                    time.sleep(2)
                    page_num += 1
                    
                except Exception as e:
                    print(f"Error clicking next button: {e}")
                    break
            else:
                print("No next button found - reached last page")
                break
        
        print(f"\nScraping completed! Total records: {len(all_data)}")
        return all_data
    
    def save_to_csv(self, data, filename="docs/csv_files/icao_aircraft_data.csv"):
        """Save data to CSV file"""
        if not data:
            print("No data to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['manufacturer', 'model', 'type_designator', 'description', 
                         'engine_type', 'engine_count', 'wtc']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"Data saved to {filename}")
    
    def save_to_json(self, data, filename="docs/json_files/icao_aircraft_data.json"):
        """Save data to JSON file"""
        if not data:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")

def main():
    """Main function to run the scraper"""
    scraper = ICAOScraper(headless=True)  # Set to False to run with browser window for debug
    
    try:
        scraper.start_driver()
        scraper.load_page()
        
        # Scrape all pages - no limit to get complete database
        data = scraper.scrape_all_pages(max_pages=74)
        
        if data:
            # Save to both CSV and JSON formats
            scraper.save_to_csv(data)
            scraper.save_to_json(data)
            
            print(f"\nSample of extracted data:")
            for i, record in enumerate(data[:3]):
                print(f"{i+1}. {record}")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()