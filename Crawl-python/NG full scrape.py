import requests
from bs4 import BeautifulSoup
import json
import time
import random
import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator
import re  # ★ 修改 1: 新增正則表達式模組，用於過濾非法字符

# ================= 設定區 =================

TARGET_SECTIONS = {
    "news": "https://www.ng.ru/news/",
    "armies": "https://www.ng.ru/armies/",
    "politics": "https://www.ng.ru/politics/",
    "economics": "https://www.ng.ru/economics/",
    "world": "https://www.ng.ru/world/"
}

# 設定每個欄目要抓幾頁
PAGES_TO_SCRAPE = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://www.ng.ru/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

translator = GoogleTranslator(source='auto', target='zh-TW')

# ================= 工具函式 =================

def translate_text(text):
    if not text or len(text) < 2: return ""
    try:
        time.sleep(0.3)
        if len(text) > 4000:
            return translator.translate(text[:4000]) + "..."
        return translator.translate(text)
    except:
        return text

def get_links_from_page(base_url, category_key, page_num):
    """
    抓取特定欄目、特定頁碼的新聞連結
    """
    if page_num == 1:
        url = base_url
    else:
        url = f"{base_url}?PAGEN_1={page_num}" 

    print(f"正在讀取 [{category_key}] 第 {page_num} 頁: {url} ...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            filter_str = f"/{category_key}/"
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # 動態過濾：確保連結包含當前分類且結尾是 .html
                if filter_str in href and href.endswith(".html") and "index.html" not in href:
                    if href.startswith("http"):
                        full_url = href
                    else:
                        full_url = "https://www.ng.ru" + href
                    links.append(full_url)
            
            unique_links = list(dict.fromkeys(links))
            print(f"  -> [{category_key}] 第 {page_num} 頁發現 {len(unique_links)} 篇潛在新聞。")
            return unique_links
        else:
            print(f"  -> 讀取失敗，狀態碼: {response.status_code}")
            return []
    except Exception as e:
        print(f"  -> 連線錯誤: {e}")
        return []

def parse_ng_article(url, category):
    time.sleep(random.uniform(1, 10))
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 標題
        title_tag = soup.find('h1')
        title_ru = title_tag.text.strip() if title_tag else "無標題"
        
        # 2. 副標題
        subtitle_ru = ""
        subtitle_tag = soup.select_one('.subtitle, .w-subtitle')
        if subtitle_tag:
            subtitle_ru = subtitle_tag.text.strip()

        # 3. 日期
        date_str = ""
        date_tag = soup.select_one('.info-date, .date')
        if date_tag:
            raw_date = date_tag.text.strip()
            try:
                dt = datetime.strptime(raw_date, "%d.%m.%Y %H:%M")
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = raw_date
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # 4. 作者
        author = "NG.ru"
        author_tag = soup.select_one('.author-name a, .author')
        if author_tag:
            author = author_tag.text.strip()

        # 5. 內文
        content_ru = ""
        content_div = soup.find('div', class_='content')
        
        if content_div:
            # 移除不必要的標籤
            for garbage in content_div.select('script, style, .banner, .read-more, div[id^="div-gpt"]'):
                garbage.decompose()
            
            paragraphs = content_div.find_all('p')
            content_list = []
            for p in paragraphs:
                text = p.text.strip()
                if text and len(text) > 5:
                    content_list.append(text)
            content_ru = "\n\n".join(content_list)
        
        if not content_ru:
            ps = soup.select('article p')
            if ps:
                content_ru = "\n\n".join([p.text.strip() for p in ps])
            else:
                return None

        # 6. 翻譯
        title_tw = translate_text(title_ru)
        content_tw = translate_text(content_ru[:3000])

        return {
            "分類": category,
            "日期": date_str,
            "作者": author,
            "標題_俄文": title_ru,
            "標題_中文": title_tw,
            "副標題": subtitle_ru,
            "內文_俄文": content_ru,
            "內文_中文": content_tw,
            "網址": url,
            "下載時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        print(f"  解析錯誤: {e}")
        return None

# ================= 主程式 =================

def main():
    print(f"開始執行 NG.ru 全欄目整合爬蟲 (共 {len(TARGET_SECTIONS)} 個欄目, 各 {PAGES_TO_SCRAPE} 頁)...\n")
    all_data = []
    
    tasks = []
    unique_url_check = set()
    
    # --- 步驟 1: 遍歷所有設定的欄目，收集連結 ---
    for category_key, base_url in TARGET_SECTIONS.items():
        print(f"--- 正在掃描分類: {category_key.upper()} ---")
        
        for page in range(1, PAGES_TO_SCRAPE + 1):
            links = get_links_from_page(base_url, category_key, page)
            
            for link in links:
                if link not in unique_url_check:
                    unique_url_check.add(link)
                    tasks.append({
                        "url": link,
                        "category": category_key
                    })
            
            time.sleep(1.5) 
            
    print(f"\n連結收集完成！總共發現 {len(tasks)} 篇不重複新聞。準備下載內容...\n")
    
    # --- 步驟 2: 逐一下載 ---
    count = 0
    total_tasks = len(tasks)
    
    for index, task in enumerate(tasks, 1):
        url = task['url']
        cat = task['category']
        
        print(f"({index}/{total_tasks}) [{cat}] 處理中...", end="\r")
        
        article_data = parse_ng_article(url, cat)
        
        if article_data:
            all_data.append(article_data)
            count += 1
            print(f"({index}/{total_tasks}) [{cat}] ✅ 收錄: {article_data['標題_中文'][:10]}...")
        else:
            print(f"({index}/{total_tasks}) [{cat}] ❌ 失敗")

    print(f"\n全部完成，共收錄 {count} 篇。")

    # --- 步驟 3: 存檔 (★ 修改區塊) ---
    if all_data:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # 定義 Excel 非法字符的正規表達式 (ASCII 0-31, 排除 tab, newline, carriage return)
        ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')

        # 清洗函式
        def clean_text_for_excel(text):
            if isinstance(text, str):
                return ILLEGAL_CHARACTERS_RE.sub("", text)
            return text

        # 1. 優先存 JSON (最安全，防止資料遺失)
        json_filename = f"ng_full_sections_{timestamp}.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print(f"JSON 檔案已儲存: {json_filename}")
        except Exception as e:
            print(f"❌ JSON 儲存失敗: {e}")

        # 2. 再存 Excel (先進行非法字符清洗)
        excel_filename = f"ng_full_sections_{timestamp}.xlsx"
        try:
            df = pd.DataFrame(all_data)
            
            # 調整欄位順序
            cols = ["分類", "日期", "標題_中文", "標題_俄文", "內文_中文", "內文_俄文", "作者", "副標題", "網址", "下載時間"]
            final_cols = [c for c in cols if c in df.columns]
            df = df[final_cols]

            # ★ 關鍵修正：將整個 DataFrame 的字串欄位進行清洗，移除非法字符
            # applymap 會對 DataFrame 中的每一個儲存格執行 clean_text_for_excel
            df = df.applymap(clean_text_for_excel)
            
            df.to_excel(excel_filename, index=False)
            print(f"Excel 檔案已儲存: {excel_filename}")
        except Exception as e:
            print(f"❌ Excel 儲存失敗 (但資料已保留在 JSON 中): {e}")

    else:
        print("未抓取到任何資料。")

if __name__ == "__main__":
    main()