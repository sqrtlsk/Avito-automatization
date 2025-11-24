from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime
import random
import time

from urls import urls

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("avito-python-01a1368c99e4.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Avito_Python").worksheet("data")

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=options)
driver.get("https://www.avito.ru/")
print("✅ Подключено к Google Chrome")

def get_stats(ad_url):
    try:
        driver.get(ad_url)
        time.sleep(random.uniform(0, 4))

        elements = driver.find_elements(By.CLASS_NAME, "styles-module-size_m-Z4wLz")
        views = 0
        contacts = 0
        if len(elements) >= 2:
            text = elements[1].text.strip()
            if text.isdigit():
                views = int(text)
        if len(elements) >= 4:
            text = elements[3].text.strip()
            if text.isdigit():
                contacts = int(text)

#-----------
        try:
            title_element = driver.find_element(
                By.CSS_SELECTOR,
                ".styles-module-root-Are5S.styles-module-root-J2o1F.styles-module-size_xxxxl-Dvz74"
            )
            title = title_element.text.strip()
        except:
            title = "NO title"
#-----------
        try:
            amount_element = driver.find_element(
                By.CLASS_NAME, "styles-module-size_ms-Ax4X5"
                )
            amount = amount_element.text.strip()
            amount = amount.split(" ")[0]
        except:
            amount = "NO amount"
#-----------
        try:
            price_element = driver.find_element(
                By.CLASS_NAME, "style-item-price-vCxf3"
                )
            price = price_element.text.strip()
        except:
            price = "NO price"
#-----------
        try:
            describe_element = driver.find_element(
                By.CLASS_NAME, "style-item-description-text-EDz3_"
                )
            describe = describe_element.text.strip()
        except:
            describe = "NO describe"

        return views, contacts, title, amount, price, describe
    
    except Exception as e:
        print(f"Ошибка при обработке {ad_url}: {e}")
        return 0, 0

counter = 0
for ad in urls:
    counter+=1
    views, contacts, title, amount, price, describe = get_stats(ad)
    today = datetime.today().strftime("%d.%m.%Y")

    sheet.append_row([counter, today, ad, views, contacts, title, amount, price, describe])
    print(f"✅ Объявление {counter} выгружено")

print("Выгрузка завершена")
driver.quit()