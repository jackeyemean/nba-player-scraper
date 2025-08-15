from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_nba_stats():
    print("Setting up Chrome browser...")
    
    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--log-level=3")  # show fatal errors
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Initialize driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Start scraping from most recent seasons
        for year in range(2025, 1949, -1):
            url = f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html"
            print(f"Attempting to access: {url}")
            
            try:
                driver.get(url)
                
                # Wait for page to load
                wait = WebDriverWait(driver, 15)  # Increased timeout
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Time for JavaScript to load
                time.sleep(3)
                
                # Check if we got blocked or if page failed to load
                if "Access denied" in driver.page_source or "blocked" in driver.page_source.lower():
                    print(f"Access denied for {year}. Skipping...")
                    continue
                
                # Check if page loaded properly
                if len(driver.page_source) < 1000:  # very small page, likely error
                    print(f"Page for {year} seems too small, likely an error. Skipping...")
                    continue
                
                # Get page source, parse with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # Find stats table
                table = soup.find("table", {"id": "per_game_stats"})
                
                if table:
                    print(f"Found stats table for {year}! Extracting data...")
                    
                    # Extract headers
                    headers = [header.text.strip() for header in table.find("thead").find_all("th")]
                    
                    # Extract data rows
                    rows = table.find("tbody").find_all("tr")
                    year_data = []
                    for row in rows:
                        cols = row.find_all("td")
                        if cols:  # Skip empty rows
                            row_data = [col.text.strip() for col in cols]
                            year_data.append(row_data)
                    
                    if year_data:
                        print(f"Extracted {len(year_data)} rows for {year}")
                        
                        # Ensure headers and data match in length
                        if len(year_data[0]) == len(headers) - 1:
                            headers = headers[1:]
                        
                        # Create DataFrame for this year
                        df_year = pd.DataFrame(year_data, columns=headers)
                        
                        # Clean data
                        df_year = df_year[df_year["Age"].apply(lambda x: str(x).isdigit())]
                        
                        # Handle players who played for multiple teams, keep the first occurrence
                        duplicates = df_year[df_year.duplicated(subset=["Player"], keep=False)]
                        if not duplicates.empty:
                            print(f"  Found {len(duplicates)} duplicate players for {year}, keeping first team...")
                            df_year = df_year.drop_duplicates(subset=["Player"], keep="first")
                        
                        # Save individual season CSV
                        filename = f"NBA_{year}_per_game_stats.csv"
                        df_year.to_csv(filename, index=False, encoding="utf-8-sig")
                        print(f"  Saved {len(df_year)} rows to {filename}")
                        
                    else:
                        print(f"No data rows found for {year}")
                else:
                    print(f"Could not find the stats table for {year}")
                    
            except Exception as e:
                print(f"Error scraping {year}: {e}")
                continue
            
            # small delay between requests
            time.sleep(1)
        
        print("\nAll seasons completed!")
        return True
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    scrape_nba_stats()