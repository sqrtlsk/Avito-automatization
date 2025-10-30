from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from oauth2client.service_account import ServiceAccountCredentials
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import gspread
from datetime import datetime
import random
import time

from urls import urls


today = datetime.today()
weekday = today.weekday()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("avito-python-8b6e211890cd.json", scope)
client = gspread.authorize(creds)

sheet = client.open("анализ Авито").worksheet("bot_pars")  # имя твоей таблицы

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=options)
driver.get("https://www.avito.ru/")
print("✅ Подключено к открытому Chrome!")

def get_stats(ad_url):
    try:
        driver.get(ad_url)
        time.sleep(random.uniform(0, 2))

        elements = driver.find_elements(By.CLASS_NAME, "styles-module-size_m-Z4wLz")
        hover_elements = driver.find_elements(By.CLASS_NAME, "styles-root-HkN9I")

        contacts = 0
        infos = []

        if len(elements) >= 4:
            text = elements[3].text.strip()
            if text.isdigit():
                contacts = int(text)

        for el in hover_elements:
            ActionChains(driver).move_to_element(el).perform()
            
            try:
                tooltip = WebDriverWait(driver, 1, poll_frequency=0.2).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "styles-tooltip-Encbf"))
                )
                info = tooltip.text.strip()
                info = info.split(" ", 1)[0]
                infos.append(info)
            
            except TimeoutException:
                infos.append(None)
                continue

        return infos, contacts

    except Exception as e:
        print(f"Ошибка при обработке {ad_url}: {e}")
        return [], ''

start_row_count = len(sheet.get_all_values())

if weekday != 0:
    num_rows_to_delete = len(urls)

    if num_rows_to_delete > 0:
        total_rows = len(sheet.get_all_values())
        start_row = total_rows - num_rows_to_delete + 1
        end_row = total_rows
        sheet.delete_rows(start_row, end_row)

counter = 0
for ad in urls:
    counter+=1
    infos, contacts = get_stats(ad)
    today = datetime.today().strftime("%d.%m.%Y")

    sheet.append_row([counter, today, ad] + infos + [contacts])
    print(f"{counter} объявлениe завершено ✅")

print("✅ Данные успешно выгружены в Google Sheets!")

end_row_count = len(sheet.get_all_values())

spreadsheet = client.open("анализ Авито")

target_sheet = spreadsheet.worksheet("переверн")

data = sheet.get_values(f"A{start_row_count + 1}:Z{end_row_count}")

transposed = list(map(list, zip(*data)))

columns_to_remove = [1, 2]
filtered_transposed = [
    row for i, row in enumerate(transposed) if i not in columns_to_remove
]

next_row = len(target_sheet.get_all_values()) + 1

if weekday == 0:
    target_sheet.update(f"A{next_row}", filtered_transposed)

else:
    total_rows_target = len(target_sheet.get_all_values())
    num_rows_to_delete = 9

    if total_rows_target >= num_rows_to_delete:
        start_row = total_rows_target - num_rows_to_delete + 1
        end_row = total_rows_target
        target_sheet.delete_rows(start_row, end_row)

    next_row = len(target_sheet.get_all_values()) + 1
    target_sheet.update(f"A{next_row}", filtered_transposed)
    print("✅ Все сделано")

driver.quit()