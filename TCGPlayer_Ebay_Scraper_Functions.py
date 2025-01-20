import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time

class ScraperFunctions:
    # Creates Dataframes based on url, wait time, and set title
    # URL : TCGPlayer Price Guide Links
    # Wait Time: 20 typically Works
    # Set: Set title that preceeds all sealed product on TCGPlayer
    # Describes the expected probability of positive returns from opening packs at market price

    def singles_sealed_data_frame(url, wait_time, set):
        # Initialize the WebDriver
        driver = webdriver.Firefox() #driver_path
        driver.get(url)

        # Wait for the table to load (adjust the selector)
        driver.implicitly_wait(wait_time)  # Adjust timeout as needed
        rows = driver.find_elements(By.CSS_SELECTOR, "#app > div > div > section.marketplace__content.white-bg > section > div.table-wrapper > div > div > div > div.table-wrap")

        # Collecting data for single cards
        data = []

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = []
            
            for cell in cells:
                cell_text = cell.text.replace("$", "").replace(",", "")
                if cell_text != "":
                    row_data.append(cell_text)
                elif (row_data != [] and cell_text == ""):
                    data.append(row_data)
                    row_data = []
                else:
                    continue
            
            if row_data:
                data.append(row_data)

        singles_df = pd.DataFrame(data, columns=['Product Name', 'Printing', 'Condition', 'Rarity', 'Number', 'Market Price', 'Add to Cart'])
        #print('df refresh')
        #print(singles_df.shape)

        # Wait for the table to load and switch tabs
        driver.implicitly_wait(wait_time)  # Adjust timeout as needed
        driver.find_element(By.CSS_SELECTOR, "#sealed\ products").click()
        rows = driver.find_elements(By.CSS_SELECTOR, "#app > div > div > section.marketplace__content.white-bg > section > div.table-wrapper > div > div > div > div.table-wrap")

        # Collecting data for sealed products
        data = []

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = []
            
            for cell in cells:
                cell_text = cell.text.replace("$", "").replace(",","")
                if cell_text != "":
                    row_data.append(cell_text)
                elif (row_data != [] and cell_text == ""):
                    data.append(row_data)
                    row_data = []
                else:
                    continue
            
            if row_data:
                data.append(row_data)
        

        sealed_df = pd.DataFrame(data, columns=['Product Name', 'Market Price', 'Add to Cart'])
        #print('df refresh')
        #print(sealed_df.shape)


        # Close the driver
        driver.quit()

        # Cleaning the data, if self-cleaning is desired, comment out this code
        singles_df = singles_df.drop(['Condition','Add to Cart'], axis=1)
        singles_df['Market Price'] = singles_df['Market Price'].astype(float)
        singles_df['Rarity'] = singles_df['Rarity'].replace(['Common', 'Uncommon', 'Rare'], np.nan)
        singles_df = singles_df.dropna()

        sealed_df = sealed_df.drop(['Add to Cart'], axis=1)
        sealed_df['Market Price'] = sealed_df['Market Price'].astype(float)
        sealed_df['Product Name'] = sealed_df['Product Name'].astype(str)
        sealed_df['Product Name'] = sealed_df['Product Name'].replace('{} '.format(set), '', regex=True)
        

        return singles_df, sealed_df


    # Analyzes card and booster pack prices to determine the chance of making money from a set
    # carddata: pandas dataframe, dataframe with card price and rarity information
    # productdata: pandas dataframe, dataframe with booster pack price information
    # pullrates: dict, dictionary that uses rarity as keys and probabilities as values
    # set: str, name of set
    # Output: None, all information is printed

    def recovery_rate_func(carddata, productdata, pull_rates, set):
        price_rarity_dict = carddata.groupby('Rarity')['Market Price'].mean().to_dict()
        #print(price_rarity_dict)

        evpp = {}
        for rarity in list(price_rarity_dict.keys()):
            ev = price_rarity_dict[rarity] * pull_rates[rarity]
            evpp.update({rarity:ev})
        
        #print(evpp)
        sum_ev_pp = sum(list(evpp.values()))
        #print(sum_ev_pp)

        boost_price = productdata[productdata['Product Name'] == 'Booster Pack']['Market Price'].values
        #print(boost_price)
        recov_rate = (sum_ev_pp / boost_price) * 100

        print("{0} Recovery Rate: {1}%".format(set, recov_rate))
        
        return 



    # Collects data on singles and sealed products from TCGPlayer using the price guide url
    # urls_: dict, set names as keys and urls as values
    # wait_time: int, amount of time the program pauses for the website to load (20 typically works)
    # sets_ : list, list of sets
    # Output: pandas dataframe

    def market_data_frame(urls_, wait_time, sets_):
        
        data = []

        for set_ in sets_:
            # Initialize the WebDriver
            driver = webdriver.Firefox() #driver_path
            driver.get(urls_[set_])

            # Wait for the table to load (adjust the selector)
            driver.implicitly_wait(wait_time)  # Adjust timeout as needed
            rows = driver.find_elements(By.CSS_SELECTOR, "#app > div > div > section.marketplace__content.white-bg > section > div.table-wrapper > div > div > div > div.table-wrap")
            
            # Collecting data for single cards
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = [set_]
                
                for cell in cells:
                    cell_text = cell.text.replace("$", "").replace(",", "")
                    if cell_text != "":
                        if " - " in cell_text:
                            row_data.append(re.sub(r' - \d+/\d+', '', cell_text))
                        else:
                            row_data.append(cell_text)
                    elif (row_data != [set_] and cell_text == ""):
                        data.append(row_data)
                        row_data = [set_]
                    else:
                        continue
                
                if row_data:
                    data.append(row_data)

                    driver.quit()

        singles_df = pd.DataFrame(data, columns=['Set', 'Product Name', 'Printing', 'Condition', 'Rarity', 'Number', 'Market Price', 'Add to Cart'])

        singles_df = singles_df.drop(['Condition','Add to Cart'], axis=1)
        singles_df['Market Price'] = singles_df['Market Price'].astype(float)


        return singles_df


    # Scrapes eBay for card price, name, and sold date
    # card_name: str, specific title for the card. ex. Pikachu ex 238/191
    # sold: bool, specifies whether it scrapes sold or available listings
    # graded: bool, specifics graded or raw cards
    # Output: pandas dataframe

    def ebay_scraper(card_name, sold = False, graded = False):

        # Initialize the WebDriver
        driver = webdriver.Firefox() #driver_path
        driver.get('https://www.ebay.com/')

        wait = WebDriverWait(driver, 30)
        action = ActionChains(driver)

        # Type Search into search bar
        search_bar = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="gh-ac"]')))
        action.move_to_element(search_bar).click().send_keys(card_name).perform()

        # Complete Search
        search_button = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="gh-search-btn"]')))
        action.move_to_element(search_button).click().perform()

        # Sort by sold or open
        if sold:
            sold_listings_filter = wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Sold Items")]')))
            sold_listings_filter.click()

        if graded:
            graded_filter = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="x-refine__group_1__0"]/ul/li[2]/div/a/div/span/input')))
            graded_filter.click()
        
        if graded == False:
            not_graded_filter = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="x-refine__group_1__0"]/ul/li[1]/div/a/div/span/input')))
            not_graded_filter.click()

        # Find Listings
        time.sleep(5)
        listings = driver.find_elements(By.CSS_SELECTOR,'#srp-river-results > ul > li.s-item')    
        
        # For each listing, copy date, title, price

        listing_data = []
        for listing in listings:
            name = listing.find_element(By.CLASS_NAME, 's-item__title').text
            price = listing.find_element(By.CLASS_NAME, 's-item__price').text.replace("$","").replace(",", "")
            date = listing.find_element(By.CLASS_NAME, 's-item__caption').text.replace("Sold", "")

            if "NEW LISTING" in name:
                name = name.replace("NEW LISTING", "")        
            
            listing_data.append([name, price, date])
        
        
        driver.quit()

        # Output dataframe of listing data
        ebay_data = pd.DataFrame(listing_data, columns=['Name', 'Price', 'Sold Date'])
        ebay_data['Price'] = ebay_data['Price'].astype(float)

        
        return ebay_data
