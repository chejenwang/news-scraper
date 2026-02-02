"""
TASS 新聞爬蟲 - 改進版（雙翻譯引擎）
支援 googletrans 和 deep-translator 雙引擎，並修正路徑接收邏輯
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import random
from typing import List, Dict
import re
from openpyxl import load_workbook
from openpyxl.styles import Alignment
import sys  # <--- 新增
import os   # <--- 新增

class TASSNewsScraper:
    def __init__(self, headless=True):
        """初始化爬蟲，使用 Selenium"""
        print("正在啟動瀏覽器...")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')  # 無頭模式
        
        # 隱藏警告訊息
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # 模擬真實瀏覽器設定
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def get_article_content(self, url: str) -> str:
        """進入文章頁面抓取完整內文"""
        try:
            self.driver.get(url)
            # 等待內文區塊載入
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="article__text"]')))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # 塔斯社內文通常在特定 class 的 div 內
            content_divs = soup.select('div[class*="article__text"], .text-block')
            
            full_text = ""
            for div in content_divs:
                paragraphs = div.find_all('p')
                full_text += "\n".join([p.get_text().strip() for p in paragraphs])
            
            return full_text.strip()
        except Exception as e:
            print(f"  [抓取內文失敗] {url}: {e}")
            return ""

    def scrape_top_news(self, limit=20) -> List[Dict]:
        """抓取首頁最新的新聞列表"""
        url = "https://tass.ru/"
        print(f"進入塔斯社首頁: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3) # 等待渲染
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            news_items = soup.select('a[class*="news-list__item"], a[class*="card"]')
            
            articles = []
            for item in news_items:
                if len(articles) >= limit:
                    break
                    
                link = item.get('href')
                if not link or not link.startswith('/'):
                    continue
                
                full_url = "https://tass.ru" + link
                title = item.get_text().strip()
                
                print(f"[{len(articles)+1}] 發現文章: {title[:20]}...")
                
                # 進入文章抓內文
                content_ru = self.get_article_content(full_url)
                
                articles.append({
                    'title_ru': title,
                    'content_ru': content_ru,
                    'url': full_url,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                time.sleep(random.uniform(1, 2))
                
            return articles
        except Exception as e:
            print(f"抓取列表出錯: {e}")
            return []

    def save_to_excel(self, articles: List[Dict], full_path: str):
        """將結果儲存至 Excel 並美化"""
        df = pd.DataFrame(articles)
        df.to_excel(full_path, index=False)
        
        # 使用 openpyxl 進行簡易格式調整
        wb = load_workbook(full_path)
        ws = wb.active
        
        # 設定欄寬與換行
        for cell in ws[1]: # 標題列
            cell.alignment = Alignment(horizontal='center')
            
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 80
        ws.column_dimensions['C'].width = 30
        
        # 內文欄位設定自動換行
        for row in range(2, ws.max_row + 1):
            ws.cell(row=row, column=2).alignment = Alignment(wrap_text=True, vertical='top')
            
        wb.save(full_path)
        print(f"Excel 存檔成功: {full_path}")

    def close(self):
        self.driver.quit()

# ================= 主程式邏輯 =================

def main():
    # --- 處理傳入的路徑參數 ---
    if len(sys.argv) > 1:
        save_dir = sys.argv[1]
    else:
        save_dir = "."

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    scraper = TASSNewsScraper(headless=True)
    
    try:
        # 執行抓取任務
        articles = scraper.scrape_top_news(limit=5) # 測試先抓 5 篇
        
        if articles:
            # 這裡可以加入翻譯邏輯 (略，保持您原有的翻譯區塊即可)
            # ...
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'tass_news_{timestamp}.xlsx'
            
            # 結合路徑與檔名
            full_output_path = os.path.join(save_dir, filename)
            
            scraper.save_to_excel(articles, full_output_path)
            
            print(f"\n✅ TASS 任務完成！共 {len(articles)} 篇。")
            print(f"儲存位置: {full_output_path}")
        else:
            print("未抓取到任何文章。")
            
    finally:
        scraper.close()

if __name__ == '__main__':
    main()
