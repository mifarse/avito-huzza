import json, requests, re, random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

ua = UserAgent()
proxies = {"http": "", "https": ""}
headers = {'User-Agent': ''}
proxy_list = [line.rstrip('\n') for line in open('proxies.txt')]
proxy_number = 0

#ОПИСАНИЕ ИСПОЛЬЗУЕМЫХ ФУНКЦИЙ
def change_proxy():
    proxy = random.choice(proxy_list)
    global headers
    headers['User-Agent'] = ua.random
    proxies['http'], proxies['https'] = "http://"+proxy,  "https://"+proxy
    print("!!! Cмена прокси: {}  {}".format(proxy, headers['User-Agent']) )

def parse (url):
	while True:
		obj = {}
		try:
			r = requests.get(url, proxies=proxies, headers=headers, timeout=config['timeout'])
		except Exception:
			print("in f parse() ", end="")
			change_proxy()
		else:
			if (r.status_code == 200):
				webpage = BeautifulSoup(r.text, 'html.parser')
				obj['avito_id']   = url.split("_")[-1]
				obj['title']      = webpage.find(class_="h1").string
				subtitle = webpage.find(class_="item-subtitle").get_text().split("\n")
				obj['date_avito'] = subtitle[1][11:]
				obj['is_company'] = 1 if "Агентство" in webpage.find(class_="description_seller").string else 0
				price_string = webpage.find(itemprop="price").string
				obj['price'] = int(re.search(r'(.*)\ руб', price_string).group(0).replace(' ', '')[:-3]) if re.search(r'(.*)\ руб', price_string)  else 'Не указана' 
				obj['description'] = webpage.find(id="desc_text").get_text() if webpage.find(id="desc_text") else ''
				obj['href'] = url
				obj['seller'] = webpage.find(id="seller").find("strong").string
				obj['city'] = webpage.find(id="map").find(itemprop="name").string
				obj['addr'] = webpage.find(itemprop="address").get_text()
				obj['region'] = re.search(r'р-н\ (.*)\,\ ', obj['addr']).group(0) if re.search(r'р-н\ (.*)\,\ ', obj['addr']) else ''
				item_params = webpage.find_all(class_="item-params")
				obj['type'] = item_params[0].get_text()
				obj['typeInfo'] = item_params[1].get_text()
				obj['images'] = []

				#надежно парсит любой тип квартиры
				matches = re.findall(r'([0-9]+)[\s.-]', obj['typeInfo'])
				if('Студия' in obj['typeInfo']):
					obj['rooms'] = 1
					if len(matches) == 3:
						obj['metr'], obj['etazh'], obj['etazhnost'] = [int(matches[0]), int(matches[1]), int(matches[2])];
					else:
						obj['metr'], obj['etazh'], obj['etazhnost'] = [float(matches[0]+0.1*int(matches[1])), int(matches[2]), int(matches[3])];
				else:
					obj['rooms'] = matches[0]
					if len(matches) == 4:
						obj['metr'], obj['etazh'], obj['etazhnost'] = [int(matches[1]), int(matches[2]), int(matches[3])];
					else:
						obj['metr'], obj['etazh'], obj['etazhnost'] = [float(int(matches[1])+0.1*int(matches[2])), int(matches[3]), int(matches[4])];

				if webpage.find(class_="b-zoom-gallery"):
					for image in webpage.find(class_="b-zoom-gallery").find_all(class_="gallery-link"):
						s = "http:"+image.get('href')
						obj['images'].append(s)

				while True:
					r = requests.get(url.replace('http://', 'http://m.'), proxies=proxies, headers={'User-Agent': 'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3B48b Safari/419.3'})
					if r.status_code != 403:
						break
					else:
						print("403, когда пытался взять телефон.", end=" ")
						change_proxy()
				webpage = BeautifulSoup(r.text, 'html.parser')
				phone_url = 'http://m.avito.ru'+webpage.find(class_="action-show-number").get('href')+'?async'

				while True:
					r   = requests.get(phone_url, proxies=proxies, cookies=r.cookies, headers={'User-Agent': 'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3B48b Safari/419.3', 'Referer': url.replace('http://', 'http://m.')})
					print (r.text)
					if r.status_code != 403:
						break
					else:
						print("403, когда почти удалось взять телефон.", end=" ")
						change_proxy()
				obj['phone'] = r.json()['phone']

				print (obj)
				break
			else:
				print('Авито возвращает статус: {}'.format(r.status_code))
				change_proxy()
				break

def analyze (page):
	percentage = step = 0
	while True:
		try:
			r = requests.get(config['url'], params={"p": page}, proxies=proxies, headers=headers, timeout=config['timeout'])
		except:
			print("in f analyze() ", end="")
			change_proxy()
		else:
			if (r.status_code == 200):
				break
			else:
				change_proxy()
	print ("\n{}".format(r.status_code))
	webpage = BeautifulSoup(r.text, 'html.parser')
	items = webpage.find_all(class_='item-description-title-link')
	for item in items:
		parse('http://avito.ru'+item.get('href'))
		step = step+1
		percentage = round(100*step / len(items))
		print("\rСтраница {}. Выполнено: {}%".format(page, percentage), end=" ")

#ВЫПОЛНЕНИЕ САМОГО СКРИПТА
print("Парсер объявлений о недвижимости с Авито.\n")

with open('config.json') as data_file:
    config = json.load(data_file)
print("Получено содержимое файла config.json. \nСсылка: %(url)s \nКол-во страниц: %(pages)s \nТаймаут ожидания: %(timeout)sсек.\n" % config)

change_proxy()

while True:
	try:
		r = requests.get(config['url'], proxies=proxies, headers=headers, timeout=config['timeout'])
	except Exception:
		print("in initial ", end="")
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
    analyze(page)
    page = page + 1