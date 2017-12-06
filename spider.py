from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
from pyquery import PyQuery as pq
from config import *
import pymongo


client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

browser = webdriver.Chrome()
wait = WebDriverWait(browser,10)


#使用webdriver打开chrome，打开淘宝页面，搜索美食关键字，返回总页数
def search():
	try:
		browser.get('https://www.taobao.com')
		input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#q')))
		submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))
		input.send_keys('美食')
		submit.click()	
		total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))
		get_products()
		return total.text
	except TimeoutException:
		print('timeout!')
		return search()



#进行页面的跳转，输入下一页的页号，然后点击确定按钮，在高亮区域判定是否正确跳转
def next_page(page_num):
	try:
		input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > input')))
		submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
		input.clear()
		input.send_keys(page_num)
		submit.click()
		wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_num)))
		get_products()		
	except TimeoutException:
		next_page(page_num)

#获取商品详情
def get_products():
	wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))
	html = browser.page_source
	doc = pq(html)
	items = doc('#mainsrp-itemlist .items .item').items()
	for item in items:
		product = {
			'image':item.find('.pic .img').attr('src'),
			'price':item.find('.price').text(),
			'deal':item.find('.deal-cnt').text()[:-3],
			'title':item.find('.title').text(),
			'shop':item.find('.shop').text(),
			'location':item.find('.location').text(),
		}
		print(product)
		save_to_mongo(product)

def save_to_mongo(result):
	try:
		if db[MONGO_TABLE].insert(result):
			print('存储成功',result)
	except Exception:
		print('存储失败',result)






def main():
	total = search()
	total = int(re.search('(\d+)',total).group(1))   #'\d'表示匹配数字
	for i in range(2,total+1):
		next_page(i)


if __name__ == '__main__':
	main()

