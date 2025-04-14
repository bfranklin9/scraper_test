from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver

import time
import math
import re
import gzip
import jmespath
import json
import requests

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
            re.sub(r'\s*\(\d{1,3}(?:,\d{3})*\)$', '', element.text.strip())
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
                    
                except Exception as e:
                    print(f"Error selecting driveline {driveline}: {e}")
                    continue

                time.sleep(3)
                base_category_page_url = driver.current_url
                print("Base category page URL:", base_category_page_url)

                # Click the button to populate categories
                button = WebDriverWait(driver, 100).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[2]/div/div[4]/div[1]/div/div[2]/div[1]/div[2]/div/form/div[2]/button"))
                )
                button.click()
                time.sleep(1)

                
                categories_count = len(WebDriverWait(driver, 100).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//label[contains(@for, 'categories')]"))
                ))
                print(f"Number of categories: {categories_count}")

                category_options = get_category_options(driver, "//label[contains(@for, 'categories')]")
                
                # print(f"Category options for year {year}, model {model}, trim {trim}, driveline {driveline}:", category_options)

                for category in category_options:
                    category_xpath = f"//label[contains(@for, 'categories') and contains(text(), '{category}')]"
                    category_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, category_xpath)))
                    category_element.click()
                    del driver.requests 
                    
                    print("Selected category:", category)

                    desired_value = "model_year_code"
                    expression = "variables.filter[?attribute=='categories']"
                    target_request = None
                    timeout_seconds = 500
                    start_time = time.time()

                    while time.time() - start_time < timeout_seconds:

                        for request in driver.requests:
                            
                            if request.response and "https://autoparts.toyota.com/graphql" in request.url and request.method == 'POST':
                                # Convert headers to a dict and then to a JSON string if needed
                                try:
                                    payload_str = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
                                    payload = json.loads(payload_str)
                                except Exception as e:
                                    continue

                                result = jmespath.search(expression, payload)
                                if result:
                                    target_request = request
                                    headers = target_request.headers
                                    break
                        if target_request:
                            break
                        else:
                            time.sleep(10)
                    #putting this in for now to close the window
                    

                    if target_request:
                        response_body = target_request.response.body

                        model_year_values = jmespath.search("variables.filter[?attribute=='model_year_code'].in[]", payload)
                        category_values = jmespath.search("variables.filter[?attribute=='categories'].in[]", payload)

                        # Check response headers to see if the body is gzip-compressed
                        content_encoding = target_request.response.headers.get("Content-Encoding", "")
                        if "gzip" in content_encoding.lower():
                            try:
                                # Decompress the body using gzip
                                decompressed_body = gzip.decompress(response_body)
                                response_str = decompressed_body.decode("utf-8")
                            except Exception as e:
                                print("Error decompressing and decoding response:", e)
                                response_str = response_body.decode("utf-8", errors="replace")
                        else:
                            # If not compressed, attempt a normal UTF-8 decoding
                            try:
                                response_str = response_body.decode("utf-8")
                            except UnicodeDecodeError as e:
                                print("Unicode decode error:", e)
                                response_str = response_body.decode("utf-8", errors="replace")

                        try:
                            response_payload = json.loads(response_str)
                        except json.JSONDecodeError:
                            response_payload = response_str  # Fallback to raw string if JSON parsing fails
                        
                        
                        number_of_parts_query = "data.productSearch.total_count"

                        
                        number_of_parts = jmespath.search(number_of_parts_query, response_payload)

                        # For this example, assume we want the first available value from the arrays:
                        model_year_code = model_year_values[0] if model_year_values else None
                        category_code = category_values[0] if category_values else None

                        # Print the extracted values
                        print("Model Year Code:", model_year_code)
                        print("Category Code:", category_code)
                        print("Number of Parts:", number_of_parts)

                        headers = target_request.headers

                        url = "https://autoparts.toyota.com/graphql"

                        max_page_size = 250
                        total_pages = math.ceil(number_of_parts / max_page_size)

                        graphql_query = """                            
                        query productSearch(
                            $phrase: String!
                            $pageSize: Int
                            $currentPage: Int = 1
                            $filter: [SearchClauseInput!]
                            $sort: [ProductSearchSortInput!]
                            $context: QueryContextInput
                        ) {
                            productSearch(
                                phrase: $phrase
                                page_size: $pageSize
                                current_page: $currentPage
                                filter: $filter
                                sort: $sort
                                context: $context
                            ) {
                                total_count
                                items {
                                    ...Product
                                    ...ProductView
                                }
                                facets {
                                    ...Facet
                                }
                                page_info {
                                    current_page
                                    page_size
                                    total_pages
                                }
                            }
                            attributeMetadata {
                                sortable {
                                    label
                                    attribute
                                    numeric
                                }
                            }
                        }
                        
                        fragment Product on ProductSearchItem {
                            product {
                                __typename
                                sku
                                description {
                                    html
                                }
                                short_description{
                                    html
                                }
                                name
                                canonical_url
                                small_image {
                                    url
                                }
                                image {
                                    url
                                }
                                thumbnail {
                                    url
                                }
                                price_range {
                                    minimum_price {
                                        fixed_product_taxes {
                                            amount {
                                                value
                                                currency
                                            }
                                            label
                                        }
                                        regular_price {
                                            value
                                            currency
                                        }
                                        final_price {
                                            value
                                            currency
                                        }
                                        discount {
                                            percent_off
                                            amount_off
                                        }
                                    }
                                    maximum_price {
                                        fixed_product_taxes {
                                            amount {
                                                value
                                                currency
                                            }
                                            label
                                        }
                                        regular_price {
                                            value
                                            currency
                                        }
                                        final_price {
                                            value
                                            currency
                                        }
                                        discount {
                                            percent_off
                                            amount_off
                                        }
                                    }
                                }
                            }
                        }

                        
                        fragment ProductView on ProductSearchItem {
                            productView {
                                __typename
                                sku
                                name
                                inStock
                                url
                                urlKey
                                images {
                                    label
                                    url
                                    roles
                                }
                                attributes {
                                    name
                                    label
                                    value
                                    roles
                                }
                                ... on ComplexProductView {
                                    priceRange {
                                        maximum {
                                            final {
                                                amount {
                                                    value
                                                    currency
                                                }
                                            }
                                            regular {
                                                amount {
                                                    value
                                                    currency
                                                }
                                            }
                                        }
                                        minimum {
                                            final {
                                                amount {
                                                    value
                                                    currency
                                                }
                                            }
                                            regular {
                                                amount {
                                                    value
                                                    currency
                                                }
                                            }
                                        }
                                    }
                                    options {
                                        id
                                        title
                                        values {
                                            title
                                            ... on ProductViewOptionValueSwatch {
                                                id
                                                inStock
                                                type
                                                value
                                            }
                                        }
                                    }
                                }
                                ... on SimpleProductView {
                                    price {
                                        final {
                                            amount {
                                                value
                                                currency
                                            }
                                        }
                                        regular {
                                            amount {
                                                value
                                                currency
                                            }
                                        }
                                    }
                                }
                            }
                            highlights {
                                attribute
                                value
                                matched_words
                            }
                        }

                        
                        fragment Facet on Aggregation {
                            title
                            attribute
                            buckets {
                                title
                                __typename
                                ... on CategoryView {
                                    name
                                    count
                                    path
                                    level
                                    roles
                                }
                                ... on ScalarBucket {
                                    count
                                }
                                ... on RangeBucket {
                                    from
                                    to
                                    count
                                }
                                ... on StatsBucket {
                                    min
                                    max
                                }
                            }
                        }


                        """

                        response_filename = "toyota_responses.json"

                        for current_page in range(1, total_pages + 1):
                            payload = {
                                "query": graphql_query,
                                "variables": {
                                "phrase": "",
                                "pageSize": max_page_size,
                                "currentPage": current_page,
                                "filter": [
                                    {
                                    "attribute": "model_year_code",
                                    "in": [
                                        model_year_code,
                                        "unknown_fitment",
                                        "universal_fitment"
                                    ]
                                    },
                                    {
                                    "attribute": "categories",
                                    "in": [
                                        category_code
                                    ]
                                    },
                                    {
                                    "attribute": "visibility",
                                    "in": [
                                        "Search",
                                        "Catalog, Search"
                                    ]
                                    },
                                    {
                                    "attribute": "inStock",
                                    "eq": "true"
                                    }
                                ],
                                "sort": [
                                    {
                                    "attribute": "fitment_status",
                                    "direction": "ASC"
                                    },
                                    {
                                    "attribute": "relevance",
                                    "direction": "DESC"
                                    }
                                ],
                                "context": {
                                    "customerGroup": "base",
                                    "userViewHistory": []
                                }
                                }
                            }
                            
                            response = requests.post(url, headers=headers, json=payload)
                            time.sleep(1)

                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                except json.JSONDecodeError:
                                    response_data = {"error": "Response not in JSON format", "raw": response.text}
                                print(f"Page {current_page}: Request successful.")
                            else:
                                response_data = {"error": "Request failed", "status_code": response.status_code, "raw": response.text}
                                print(f"Page {current_page}: Request failed with status code {response.status_code}.")


                            # with open(response_filename, "a") as f:
                            #     f.write(json.dumps(response_data, indent=2))
                            #     f.write("\n")
                            


                            with open(response_filename, "a") as f:
                                # Add ALL FOUR variables to the response data
                                response_data.update({
                                    "Year": year,
                                    "Model": model,
                                    "Trim": trim,
                                    "Drive Line": driveline,
                                    "Category": category,
                                })
                                
                                # Write as JSON Lines format
                                f.write(json.dumps(response_data) + "\n")

                    driver.get(base_category_page_url)
                    time.sleep(1)

                    # Click the button to populate categories
                    button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[2]/div/div[4]/div[1]/div/div[2]/div[1]/div[2]/div/form/div[2]/button"))
                    )
                    button.click()



                driver.get("https://autoparts.toyota.com")
                # close_banner(driver)
                time.sleep(2)
    