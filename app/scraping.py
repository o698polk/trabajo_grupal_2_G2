from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import pandas as pd 
from io import StringIO
import numpy as np
from bs4 import BeautifulSoup
from datetime import datetime

def get_html(driver, url, selector, sleep_time=10):
    driver.get(url)
    time.sleep(sleep_time)
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        return element.get_attribute("outerHTML")
    except:
        # Fallback to full page source if selector fails
        return driver.page_source

def scrape_mercadolibre(query: str):
    driver = None
    products = []
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Set a real user-agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        selector = "#root-app" 
        
        for page in range(2): # First 5 pages
            # Mercado Libre uses offsets of 48 or 50 items. Starting at 1, 49, 97...
            offset = 1 + (page * 48)
            if page == 0:
                URL = f"https://listado.mercadolibre.com.ec/{query.replace(' ', '-')}"
            else:
                URL = f"https://listado.mercadolibre.com.ec/{query.replace(' ', '-')}_Desde_{offset}_NoIndex_True"
            
            print(f"DEBUG: Scraping Page {page+1}: {URL}")
            
            # get_html already has a 10s sleep by default
            html_content = get_html(driver, URL, selector, sleep_time=10)
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Broadened selectors for different Mercado Libre layouts
            cards = soup.select(".poly-card__content")
            if not cards:
                cards = soup.select(".ui-search-result__content-wrapper")
            if not cards:
                cards = soup.select(".ui-search-result")
            if not cards:
                cards = soup.select(".poly-card")

            if not cards:
                print(f"DEBUG: No more cards found on page {page+1}, stopping. Try without replacement if spaces exist.")
                # Try simple URL if dash-version failed?
                if page == 0:
                    URL_fallback = f"https://listado.mercadolibre.com.ec/{query}"
                    print(f"DEBUG: Falling back to {URL_fallback}")
                    html_content = get_html(driver, URL_fallback, selector, sleep_time=10)
                    soup = BeautifulSoup(html_content, "html.parser")
                    cards = soup.select(".poly-card__content") or soup.select(".ui-search-result__content-wrapper") or soup.select(".ui-search-result")

            if not cards:
                print(f"DEBUG: Still no cards found on page {page+1} after fallback.")
                break

            print(f"DEBUG: Found {len(cards)} cards on page {page+1}")

        for product in cards:
            title_tag = product.find("a", class_="poly-component__title")
            price_container = product.find("div", class_="poly-price__current")
            
            if title_tag and price_container:
                title = title_tag.get_text(strip=True)
                url = title_tag["href"] 
        
                price_whole = price_container.find("span", class_="andes-money-amount__fraction")
                price_cents = price_container.find("span", class_="andes-money-amount__cents")
        
                price_str = "0"
                if price_whole:
                    price_str = price_whole.get_text(strip=True).replace(".", "").replace(",", "")
                    if price_cents:
                        price_str += "." + price_cents.get_text(strip=True)
                
                try:
                    price_val = float(price_str)
                except:
                    price_val = 0.0
                    
                products.append({
                    "name": title,
                    "price": price_val,
                    "link": url
                })
        
        if products:
            # Create directory if it doesn't exist
            output_dir = "csv_archivos"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_{query}_{timestamp}.csv".replace(" ", "_")
            filepath = os.path.join(output_dir, filename)
            
            df = pd.DataFrame(products)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"Results saved to {filepath}")

        return products
    
    except Exception as e:
        print(f"Error scraping MercadoLibre: {e}")
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    res = scrape_mercadolibre("celulares")
    print(f"Encontrados: {len(res)}")
