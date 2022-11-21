import configparser
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver  
import time, json
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import os

storage = MemoryStorage()
config = configparser.ConfigParser()
config.read('config.ini')
API_TOKEN = config['TELEGRAM']['TOKEN']
# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot,storage = storage)

# add district ?district=
# add metro &metro=
class FSMAdmin( StatesGroup ):
    radius = State()
    low_price = State()
    high_price = State()    

client_id = 0
low_price = 0
max_price = 99999
radius = 19


def get_browser_options() :
    _options = webdriver.ChromeOptions()
    _options.binary_location = r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
    _options.add_argument('--ignore-certificate-errors-spki-list')
    _options.add_argument('--ignore-ssl-errors')
    _options.add_argument('log-level=3')
    _options.add_argument("--disable-blink-features=AutomationControlled")

    _options.add_argument("enable-automation")
    _options.add_argument("--headless")
    # _options.add_argument("--window-size=1920,1080")
    _options.add_argument("--no-sandbox")
    _options.add_argument("--disable-extensions")
    _options.add_argument("--dns-prefetch-disable")
    _options.add_argument("--disable-gpu")
    _options.add_argument("--force-device-scale-factor=1")
    _options.add_argument("--blink-settings=imagesEnabled=false")
    _options.page_load_strategy = "normal"
    return _options


search = {
    "ширина профиля" : [175, 185, 195, 205, 215,225, 235,245,
    255,265,275,285,295,315,385],
    "высота профиля" : [],
    "диаметр" : [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 22.5],
    "сезон" : "летние"
}

def get_page():
    service = Service(executable_path="chromedriver.exe")
    options = get_browser_options()     
    options.headless = False
    browser = webdriver.Chrome(service=service, options = options) 

    url = "https://www.avito.ru/moskva/zapchasti_i_aksessuary/shiny_diski_i_kolesa/shiny"
    browser.get(url)
    browser.set_page_load_timeout(11) 
    time.sleep(4)  

    try:
        actions = ActionChains(browser)  
        actions.scroll_by_amount(0, 200)         
        actions.perform()
        time.sleep(1)
        diametr = browser.find_element(by=By.XPATH, value="//*[@id='app']/div/div[3]/div[3]/div[1]/div/div[2]/div[1]/form/div[6]/div/div[2]/div/div/div/div/label/input")  
        diametr.send_keys(radius)
        actions.move_to_element_with_offset(diametr, 10, 60)
        actions.click()
        actions.perform()
        time.sleep(1)

        price_min = browser.find_element(by=By.XPATH, value= "//*[@id='app']/div/div[3]/div[3]/div[1]/div/div[2]/div[1]/form/div[11]/div/div[2]/div/div/div/div/div/div/label[1]/input")
        price_min.send_keys(low_price)
        price_max = browser.find_element(by=By.XPATH, value= "//*[@id='app']/div/div[3]/div[3]/div[1]/div/div[2]/div[1]/form/div[11]/div/div[2]/div/div/div/div/div/div/label[2]/input")
        price_max.send_keys(max_price)        
        time.sleep(1)

        pivot = browser.find_element(by=By.XPATH, value="//*[@id='app']/div/div[3]/div[3]/div[1]/div/div[2]/div[1]/form/div[15]/div")        
        actions.scroll_by_amount(0, 600) 
        actions.perform()
        time.sleep(2)
        actions.move_to_element_with_offset(pivot, 10, 110)
        actions.click()
        actions.perform()
        time.sleep(1)
        # time.sleep(10)
        print(browser.current_url+"&s=104")
        browser.get(browser.current_url+"&s=104")
    except NoSuchElementException as ex:
        print(ex)

    page = browser.page_source
    browser.close()
    return page

def parse_page( page ):
    soup = BeautifulSoup(page, 'lxml')   
    divs = soup.find_all('div', attrs={ "data-marker" : "item" })
    items = []

    for ind, div in enumerate(divs, start=1):
        item = { "title" : "",
                "href" : "",
                "price" : "",
                "date" : "" }
            
        ch_divs  = div.find_all('div', recursive=False)
    
        for ch in ch_divs:
            it_content = ch.get('class')[0]
            if "iva-item-content-" in it_content:
                cont = ch.find_all('div', recursive=False)
                for c in cont:
                    if "iva-item-body-" in c.get('class')[0] :
                        blocks = c.find_all('div', recursive=False)
                        for b in blocks:
                            class_name = b.get('class')
                            if class_name:
                                if "iva-item-titleStep" in class_name[0]:
                                    item['href'] = b.a.get('href')
                                    item['title'] = b.get_text()
                                elif "iva-item-priceStep" in class_name[0]:
                                    item["price"] = b.get_text()
                                elif "iva-item-dateInfoStep" in class_name[0]:
                                    item["date"] = b.get_text()
                        items.append(item)        
    return items[:5]
    for it in items:
        print(f'{it["title"]}')
        print(f'{it["price"]}')
        print(f'{it["date"]}')
        print(f'{it["href"]}')
        print("----------------------------------------------")

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):    
    await message.answer("Выберите комманду search для начала работы")

@dp.message_handler(commands=['search'], state=None )
async def send_search(message: types.Message):  
    await FSMAdmin.radius.set()  
    await message.answer("Укажите радиус шин?")

@dp.message_handler( state=FSMAdmin.radius )
async def set_radius( message : types.Message, state: FSMContext ):
    global radius
    radius = message.text
    await FSMAdmin.next()
    await message.answer('Введите нижнюю границу диапазона цены')


@dp.message_handler( state=FSMAdmin.low_price )
async def set_low_price( message : types.Message, state: FSMContext ):
    global low_price
    low_price = message.text
    await FSMAdmin.next()
    await message.answer('Введите верхнюю границу диапазона цены')

@dp.message_handler( state=FSMAdmin.high_price )
async def set_high_price( message : types.Message, state: FSMContext ):
    global max_price
    max_price = message.text
    await state.finish()
    await message.answer('Ждите результаты...')
    page = get_page()
    items = parse_page(page)
    for it in items:
        print(f'{it["title"]}')
        print(f'{it["price"]}')
        print(f'{it["date"]}')
        print(f'{it["href"]}')
        await message.answer(f'{it["date"]}\nhttps://www.avito.ru{it["href"]}')
        time.sleep(1)
    

def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    main()
