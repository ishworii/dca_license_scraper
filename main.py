from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import requests
import re
import pandas as pd
from collections import defaultdict


# Headless/incognito Chrome driver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("headless")
driver = webdriver.Chrome(
    executable_path="C:\\Users\\PC\\Desktop\\upwork\\scraping_project\\chromedriver.exe",
    chrome_options=chrome_options,
)

driver.get("https://search.dca.ca.gov/")


# select board of bureau
driver.find_element(
    By.XPATH,
    "//select[@name='advBoardCode']/option[text()='Automotive Repair, Bureau of']",
).click()
sleep(2)

# select license type
element = driver.find_element(By.XPATH, "//*[@id='b21']/option[4]")
actions = ActionChains(driver)
actions.move_to_element(element).perform()
element.click()
sleep(2)

# # select city
element = driver.find_element(By.XPATH, "//*[@id='CA_cities']/option[731]")
actions = ActionChains(driver)
actions.move_to_element(element).perform()
element.click()
sleep(2)

# click on search
driver.find_element(By.XPATH, "//*[@id='srchSubmitHome']").click()
# sleep(10)


# Set sleep time for the page to load on scroll
SCROLL_PAUSE_TIME = 2

# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")

# If you want to limit the number of scroll loads, add a limit here
scroll_limit = 10

count = 0
while True and count < scroll_limit:
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height
    count += 1

sleep(2)

data = driver.find_element(By.XPATH, "//*[@id='main']").find_elements(
    By.TAG_NAME, "article"
)
result = defaultdict(list)
for index, article in enumerate(data):
    license_link = article.find_element(By.TAG_NAME, "a")
    details = license_link.get_attribute("href")
    response = requests.get(details)
    soup = BeautifulSoup(response.content, "lxml")
    detail_headers = soup.find("div", {"class": "detailContainer"}).text
    detail_headers = [x for x in detail_headers.split("\n") if x]
    name = detail_headers[0].split(":")[-1]
    license_type = detail_headers[1].split(":")[-1]
    license_status = detail_headers[2].split(":")[-1]
    address = (
        soup.find("div", {"class": "addContainer"})
        .find_all("p", {"class": "wrapWithSpace"})[-1]
        .text
    )

    address = (
        soup.find("div", {"class": "addContainer"})
        .find_all("p", {"class": "wrapWithSpace"})[-1]
        .__str__()
    )

    address = re.findall(">([^<>]*)<", address)
    address_number_street = address[0]
    city_state_zip = address[1].split(" ")
    zip, state = "", ""
    if city_state_zip:
        zip = city_state_zip.pop()
    if city_state_zip:
        state = city_state_zip.pop()
    city = " ".join(city_state_zip)
    county = address[-1].upper()
    params = {
        "Name": name,
        "License type": license_type,
        "License Status": license_status,
        "City": city,
        "State": state,
        "ZIP": zip,
        "County": county,
    }
    for k, v in params.items():
        result[k].append(v)

    print(f"Completed {index + 1} / {len(data)}")


df = pd.DataFrame(result)
df.to_csv("test.csv", index=False)
