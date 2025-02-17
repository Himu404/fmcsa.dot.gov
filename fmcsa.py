import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Function to read last page number
def read_last_page():
    if os.path.exists("last_page.txt"):
        with open("last_page.txt", "r") as file:
            return int(file.read())
    return 0  # Default to 0 if no file exists

# Function to write last page number
def write_last_page(page_number):
    with open("last_page.txt", "w") as file:
        file.write(str(page_number))

# Setup Selenium WebDriver
options = Options()
options.add_argument("--start-maximized")
options.add_extension("C:\\Users\\A\\Desktop\\himu\\Free VPN for Chrome - VPN Proxy VeePN - Chrome Web Store 3.3.1.0.crx")

chrome_driver_path = "C:\\Users\\A\\Desktop\\himu\\chromedriver-win64\\chromedriver.exe"
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Data storage setup
data = []  # List to hold extracted data for each company

# Open the website
driver.get("https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist")

# Wait for VPN, CAPTCHA, and Filters (Manual Step)
input("Manually enable VPN, solve CAPTCHA, set filters, then press Enter...")

# Read the last processed page number (if exists)
page_count = read_last_page()
print(f"Resuming from Page {page_count + 1}...")

# Click the Search Button
try:
    search_button = WebDriverWait(driver, 0).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and contains(@value, 'Search')]"))
    )
    search_button.click()
    print("Search button clicked!")

    time.sleep(0)  # Wait for results to load

    # If there is a last page number, navigate to that page by clicking 'Next' button the required number of times
    for _ in range(page_count):  # Click 'Next' for the number of times it takes to get to the last page
        next_button = WebDriverWait(driver, 0).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and contains(@value, 'Next 10 Records')]"))
        )
        next_button.click()
        print(f"Clicked 'Next' button to go to Page {page_count + 1}...")
        time.sleep(0)  # Wait for the next page to load

    while True:  # Loop through all pages
        page_count += 1
        print(f"Processing Page {page_count}...")

        try:
            # Locate the main table
            table = WebDriverWait(driver, 0).until(
                EC.presence_of_element_located((By.XPATH, "//table[@summary='table used for formating purposes only']"))
            )
            rows = table.find_elements(By.XPATH, ".//tr[position()>1]")  # Skip header row
            print(f"Found {len(rows)} companies on this page.")

            for index, row in enumerate(rows, start=2):  # Start index at 2 since the first row is the header
                try:
                    # Dynamically generate XPath for each row
                    row_xpath = f"/html/body/font/table[2]/tbody/tr[{index}]/td[8]/center/font/form/input[3]"

                    # Wait until the button is clickable
                    html_button = WebDriverWait(driver, 0).until(
                        EC.element_to_be_clickable((By.XPATH, row_xpath))
                    )

                    # Click the HTML button to open details in the same tab
                    html_button.click()
                    print(f"Opened company details for row {index}...")

                    # Wait for the details to load (adjust time if necessary)
                    time.sleep(0)

                    # Extract company details
                    try:
                        company_name = driver.find_element(By.XPATH, "//td[@colspan='3' and @headers='lname']/font").text.strip()
                        address_parts = driver.find_elements(By.XPATH, "//td[@headers='business_address']//font")
                        address = " ".join([part.text.strip() for part in address_parts if part.text.strip()])

                        phone_parts = driver.find_elements(By.XPATH, "//td[@headers='business_tel_and_fax']//font")
                        phone_number = ", ".join([part.text.strip() for part in phone_parts if part.text.strip()])

                        # Add extracted data to the list
                        data.append({
                            'Company Name': company_name,
                            'Address': address,
                            'Phone Number': phone_number
                        })

                        # Save data to Excel after each company (append to file)
                        df = pd.DataFrame(data)
                        df.to_excel("company_details.xlsx", index=False)

                    except Exception as e:
                        print(f"Error scraping company details: {e}")

                    # Navigate back to the main listing page
                    driver.back()
                    time.sleep(0)  # Allow the page to reload

                except Exception as e:
                    print(f"Error processing row {index}: {e}")

        except Exception as e:
            print(f"Error locating the results table: {e}")
            break

        # Click "Next 10 Records" to go to the next page
        try:
            next_button = WebDriverWait(driver, 0).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and contains(@value, 'Next 10 Records')]"))
            )
            next_button.click()
            print("Navigated to the next page...\n")
            time.sleep(0)  # Wait for the next page to load

            # Write the current page number to the file
            write_last_page(page_count)

        except:
            print("No more pages. Scraping complete.")
            break  # Exit loop when no more pages

except Exception as e:
    print(f"An error occurred: {e}")

# Close the browser
driver.quit()
