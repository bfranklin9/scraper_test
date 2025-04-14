from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver

import time

import re


def close_banner(driver):
    try:
        close_btn = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='modal close button']"))
        )
        close_btn.click()
        print("Banner closed.")
    except TimeoutException:
        print("No banner found.")


def get_dropdown_options(driver, css_selector, wait_time=100):
    """Wait for a dropdown to appear and return a list of non-empty option values."""
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        select = Select(element)
        options = [option.get_attribute("value") for option in select.options if option.get_attribute("value").strip() != ""]
        return options
    except TimeoutException:
        print(f"Timed out waiting for dropdown: {css_selector}")
        return []
    

def get_category_options(driver, xpath, wait_time=100):
    try:
        elements = WebDriverWait(driver, wait_time).until(
            EC.presence_of_all_elements_located((By.XPATH, xpath))
        )
        options = [
            re.sub(r'\s*\(\d+\)$', '', element.text.strip())
            for element in elements
            if element.text.strip() != ""
        ]
        return options
    except TimeoutException:
        print(f"Timed out waiting for dropdown: {xpath}")
        return []


# Initialize the driver and navigate to the site
driver = webdriver.Chrome()
driver.get("https://autoparts.toyota.com")
close_banner(driver)
time.sleep(2)

# Open the CSV file using a with-statement so it stays open for all the writing operations.
# with open("toyota_parts.csv", "w", newline="", encoding="utf-8", buffering =1) as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerow(["Year", "Model", "Trim", "Driveline", "Category", "Part Number", "Description", "Price"])

# Retrieve available options for the first dropdown (year)
year_options = get_dropdown_options(driver, "#yearSelectId")
print("Year options:", year_options)

for year in year_options:
    try:
        
        year_select = Select(driver.find_element(By.CSS_SELECTOR, "#yearSelectId"))
        year_select.select_by_value(year)
        print("Selected year:", year)
    except Exception as e:
        print(f"Error selecting year {year}: {e}")
        continue

    time.sleep(2)
    model_options = get_dropdown_options(driver, "#modelSelectId")
    print(f"Model options for year {year}:", model_options)

    for model in model_options:
        try:
            model_select = Select(driver.find_element(By.CSS_SELECTOR, "#modelSelectId"))
            model_select.select_by_value(model)
            print("Selected model:", model)
        except Exception as e:
            print(f"Error selecting model {model}: {e}")
            continue

        time.sleep(2)
        trim_options = get_dropdown_options(driver, "#trimLevelSelectId")
        print(f"Trim options for year {year}, model {model}:", trim_options)

        for trim in trim_options:
            try:
                trim_select = Select(driver.find_element(By.CSS_SELECTOR, "#trimLevelSelectId"))
                trim_select.select_by_value(trim)
                print("Selected trim:", trim)
            except Exception as e:
                print(f"Error selecting trim {trim}: {e}")
                continue

            time.sleep(2)
            driveline_options = get_dropdown_options(driver, "#driveLineSelectId")
            print(f"Driveline options for year {year}, model {model}, trim {trim}:", driveline_options)

            for driveline in driveline_options:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#driveLineSelectId"))
                    )
                    driveline_select = Select(driver.find_element(By.CSS_SELECTOR, "#driveLineSelectId"))
                    driveline_select.select_by_value(driveline)
                    print("Selected driveline:", driveline)
                    time.sleep(2)
                except Exception as e:
                    print(f"Error selecting driveline {driveline}: {e}")
                    continue
                    



                    # time.sleep(3)
                    # base_category_page_url = driver.current_url
                    # print("Base category page URL:", base_category_page_url)


                    # driver.get(base_category_page_url)

                    # button = WebDriverWait(driver, 100).until(
                    # EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[2]/div/div[4]/div[1]/div/div[2]/div[1]/div[2]/div/form/div[2]/button"))
                    # )
                    # button.click()

                    

                



                driver.get("https://autoparts.toyota.com")
                # close_banner(driver)
                time.sleep(2)
    
