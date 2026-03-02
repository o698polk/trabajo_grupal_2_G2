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
    csv_filename = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        URL = f"https://listado.mercadolibre.com.ec/{query}"
        selector = "#root-app" 
        
        html_content = get_html(driver, URL, selector)
        soup = BeautifulSoup(html_content, "html.parser")
        
        products = []
        cards = soup.find_all("div", class_="poly-card__content")
        
        if not cards:
             cards = soup.select(".ui-search-result__content-wrapper")

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
