import json, requests, re
from bs4 import BeautifulSoup

proxies = {"http": ""}
proxy_list = [line.rstrip('\n') for line in open('proxies.txt')]
proxy_number = 0

#ОПИСАНИЕ ИСПОЛЬЗУЕМЫХ ФУНКЦИЙ
def change_proxy():
    global proxy_number
    proxies['http'] = "http://"+proxy_list[proxy_number]
    proxy_number = proxy_number+1
    print("Произошла смена прокси-адреса на {}".format(proxy_list[proxy_number]) )

def parse (url):
    obj = {}
    r = requests.get(url, proxies=proxies, timeout=config['timeout'])
    webpage = BeautifulSoup(r.text, 'html.parser')
    obj['avito_id']   = webpage.find(id="item_id").string
    obj['title']      = webpage.find(class_="h1").string
    subtitle = webpage.find(class_="item-subtitle").get_text().split("\n")
    obj['date_avito'] = subtitle[1]
    obj['is_company'] = 1 if "Агентство" in webpage.find(class_="description_seller").string else 0
    price_string = webpage.find(itemprop="price").string
    obj['price'] = int(re.search(r'(.*)\ руб', price_string).group(0).replace(' ', '')[:-3]) if re.search(r'(.*)\ руб', price_string)  else 'Не указана' 
    obj['description'] = webpage.find(id="desc_text").get_text() if webpage.find(id="desc_text") else ''
    obj['href'] = url
    obj['seller'] = webpage.find(id="seller").find("strong").string
    obj['city'] = webpage.find(itemprop="name").string
    obj['addr'] = webpage.find(id="toggle_map").string
    #obj['region'] = re.search(r'р-н\ (.*)\,\ ', obj['addr']).group(0)
    
    #print (obj)

def analyze (page):
    percentage = step = 0
    r = requests.get(config['url'], params={"p": page}, proxies=proxies, timeout=config['timeout'])
    print (r.status_code)
    webpage = BeautifulSoup(r.text, 'html.parser')
    items = webpage.find_all(class_='item-description-title-link')
    print ("Страница {}. Выполнено: {}%".format(page, percentage), end=" ")
    for item in items:
        parse('http://avito.ru'+item.get('href'))
        step = step+1
        percentage = round(100*step / len(items))
        print("\rСтраница {}. Выполнено: {}%".format(page, percentage), end=" ")

#ВЫПОЛНЕНИЕ САМОГО СКРИПТА
print("Парсер объявлений о недвижимости с Авито.\n")

with open('config.json') as data_file:
    config = json.load(data_file)
print("Получено содержимое файла config.json. \nСсылка: %(url)s \nКол-во страниц: %(pages)s \nТаймаут ожидания: %(timeout)sсек." % config)

change_proxy()

while True:
    try:
        r = requests.get(config['url'], proxies=proxies, timeout=config['timeout'])
    except Exception:
        change_proxy()
    else:
        if r.status_code == 403:
            print ("Авито выдал ошибку 403!")
            change_proxy()
        elif r.status_code == 200:
            break

webpage     = BeautifulSoup(r.text, 'html.parser')
total_pages = webpage.find_all(class_='pagination-page')[-1].get('href').split("?p=")
total_pages = int(total_pages[1])

config['pages'] = total_pages if config['pages'] > total_pages or config['pages'] == 0 else config['pages']
print("Первая страница загружена. Будет обработано {} из {} стр. - около {} объявлений"
.format( config['pages'], total_pages, config['pages']*50 ))

page = 1
while page <= config['pages']:
    try:
        analyze(page)
    except Exception:
        change_proxy()
    else:
        page = page + 1
