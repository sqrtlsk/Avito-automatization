from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime
import random
import time

from urls import urls

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("avito-python-8b6e211890cd.json", scope)
client = gspread.authorize(creds)
sheet = client.open("анализ Авито").worksheet("bot_pars")

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
options.page_load_strategy = "none"
driver = webdriver.Chrome(options=options)
driver.get("https://www.avito.ru/")
print("✅ Подключено к Google Chrome")

def get_stats(ad_url):
    try:
        driver.get(ad_url)
        time.sleep(random.uniform(0.5, 1.5))

        elements = driver.find_elements(By.CLASS_NAME, "styles-module-size_m-Z4wLz")
        contacts = None
        if len(elements) >= 4:
            text = elements[3].text.strip()
            if text.isdigit():
                contacts = int(text)

        hover_elements = driver.find_elements(By.CLASS_NAME, "styles-root-HkN9I")
        week_infos = [None]*7
        for idx, el in enumerate(hover_elements):
            if idx >= 7:
                break
            try:
                ActionChains(driver).move_to_element(el).perform()
                tooltip = WebDriverWait(driver, 1, poll_frequency=0.2).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "styles-tooltip-Encbf"))
                )
                info = tooltip.text.strip().split(" ", 1)[0]
                week_infos[idx] = info
            except TimeoutException:
                continue

        return week_infos, contacts
    except Exception as e:
        return [None]*7, None

all_values = sheet.get_all_values()
if not all_values:
    raise SystemExit("Лист bot_pars пуст или недоступен")
headers = all_values[0]
link_col = headers.index("Ссылка")
contact_col = headers.index("контакты")
day_cols = [headers.index(d) for d in ["пн","вт","ср","чт","пт","сб","вс"]]

data = all_values[1:]
link_to_row = {row[link_col]: i+2 for i,row in enumerate(data) if len(row)>link_col and row[link_col]}

def same_iso_week(d1, d2):
    return d1.isocalendar()[:2] == d2.isocalendar()[:2]

def create_new_week_block(today_date):
    next_row = len(sheet.get_all_values()) + 1 
    for idx, url in reversed(list(enumerate(urls, 1))):
        row_data = [str(idx), today_date, url] + [""]*7 + [""]
        sheet.insert_row(row_data, next_row)


last_block_date = None
if data:
    for row in reversed(data):
        if len(row) > 1 and row[1]:
            try:
                last_block_date = datetime.strptime(row[1], "%d.%m.%Y")
                break
            except:
                continue

today = datetime.today()
today_date = today.strftime("%d.%m.%Y")

if not last_block_date or not same_iso_week(today, last_block_date):
    print("Создан новый недельный блок")
    create_new_week_block(today_date)
    all_values = sheet.get_all_values()
    data = all_values[1:]
    link_to_row = {row[link_col]: i+2 for i,row in enumerate(data) if len(row)>link_col and row[link_col]}

k=0
for ad_url in urls:
    k+=1
    if ad_url not in link_to_row:
        print(f"⏭ Пропускаем новое объявление (не найдено в текущем блоке): {ad_url}")
        continue

    row_num = link_to_row[ad_url]
    week_infos, contacts = get_stats(ad_url)
    current_row = sheet.row_values(row_num)
    if len(current_row)<len(headers):
        current_row += [""]*(len(headers)-len(current_row))

    updates = []
    for i, col_idx in enumerate(day_cols):
        new_val = week_infos[i]
        old_val = current_row[col_idx]
        if new_val is not None and str(new_val).strip()!="" and str(new_val)!=str(old_val):
            cell = f"{chr(65+col_idx)}{row_num}"
            updates.append({"range":cell,"values":[[str(new_val)]]})
    if contacts is not None and str(contacts)!=str(current_row[contact_col]):
        cell = f"{chr(65+contact_col)}{row_num}"
        updates.append({"range":cell,"values":[[str(contacts)]]})

    if updates:
        sheet.batch_update(updates)
        print(f"✅ Обновлена строка {k} - записано {len(updates)} ячеек)")
    else:
        print(f"⏭ Для {k} нет новых значений")

print("Обновление bot_pars завершено")

target_sheet = client.open("анализ Авито").worksheet("переверн")

all_values = sheet.get_all_values()
data = all_values[1:]
block = data[-len(urls):] if len(data)>=len(urls) else data[:]

indices_to_take = [0] + list(range(3,11))
selected = []
for row in block:
    row_extended = row + [""]*max(0,max(indices_to_take)+1-len(row))
    selected.append([row_extended[i] for i in indices_to_take])

def to_int_if_possible(v):
    try:
        if v is None:
            return v
        s = str(v).strip()
        if s=="": return ""
        num = float(s.replace(",","."))
        return int(round(num))
    except:
        return s

selected_conv = [[to_int_if_possible(cell) for cell in r] for r in selected]
transposed = list(map(list, zip(*selected_conv))) if selected_conv else []

first_col = ["Дата","пн","вт","ср","чт","пт","сб","вс","контакты"]
first_col[0] = today_date

final_data = []
while len(transposed)<len(first_col):
    transposed.append([""]*len(block))
for i in range(len(first_col)):
    final_data.append([first_col[i]] + transposed[i])

existing_target = target_sheet.get_all_values()

last_date = None
for row in reversed(existing_target):
    if row and row[0]:
        try:
            last_date = datetime.strptime(row[0],"%d.%m.%Y")
            break
        except:
            continue

def same_week(d1,d2):
    return d1.isocalendar()[:2]==d2.isocalendar()[:2]

if last_date and same_week(today,last_date):
    start_row = None
    for i,row in enumerate(existing_target):
        if row and row[0]==last_date.strftime("%d.%m.%Y"):
            start_row=i+1
            break
    if start_row is None:
        next_row = len(existing_target)+1
        target_sheet.update(range_name=f"A{next_row}", values=final_data)
        print(f"Добавлен блок в 'переверн', дата {today_date}")
    else:
        target_sheet.update(range_name=f"A{start_row}", values=final_data)
        print(f"Обновлен существующий блок недели в 'переверн', дата {today_date}")
else:
    next_row = len(existing_target)+1
    target_sheet.update(range_name=f"A{next_row}", values=final_data)
    print(f"Добавлен новый недельный блок в 'переверн', дата {today_date}")

driver.quit()