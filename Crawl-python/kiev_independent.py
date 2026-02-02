import requests
from bs4 import BeautifulSoup
import json
import time
import random
import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator
from openpyxl.styles import Alignment
import sys  # ### 修改: 加入 sys
import os   # ### 修改: 加入 os

# ================= 設定區 =================
BASE_URL = "https://kyivindependent.com"
# 您指定的六個欄目
SECTIONS = ["war", "politics", "business", "russia", "europe", "opinion"]

# 模擬人類 Headers 避免被封鎖
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://kyivindependent.com/"
}

translator = GoogleTranslator(source='auto', target='zh-TW')

# ================= 工具函式 =================

def translate_text(text):
    if not text: return ""
    try:
        # 避免翻譯請求過快導致 IP 被鎖
        time.sleep(random.uniform(0.5, 1.2))
        if len(text) > 4500:
            return translator.translate(text[:4500]) + translator.translate(text[4500:9000])
        return translator.translate(text)
    except Exception as e:
        print(f"  [翻譯失敗] {e}")
        return text

def parse_article_content(url):
    """解析文章內文頁面"""
    print(f"  └─ 正在讀取內文: {url}")
    time.sleep(random.uniform(1.5, 3.5)) 
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. 抓取日期
        date_tag = soup.select_one('time')
        date_str = date_tag.get_text(strip=True) if date_tag else "未知日期"
        
        # 2. 抓取作者
        author_tag = soup.select_one('a[href*="/author/"]')
        author = author_tag.get_text(strip=True) if author_tag else "Kyiv Independent Staff"
        
        # 3. 抓取正文 (Kyiv Independent 常用的正文容器)
        content_div = soup.select_one('.article-body') or soup.select_one('.post-content') or soup.select_one('article')
        if not content_div:
            # 備用方案：抓取所有段落，過濾掉短句
            paragraphs = soup.find_all('p')
            content_en = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text()) > 50])
        else:
            # 去除雜訊
            for garbage in content_div(["script", "style", "aside", "div.ad-slot", "figure"]):
                garbage.decompose()
            content_en = content_div.get_text(separator="\n", strip=True)

        # --- 翻譯內文 ---
        content_tw = translate_text(content_en)
        
        return date_str, author, content_en, content_tw
    except Exception as e:
        print(f"  [內容解析錯誤] {e}")
        return "", "", "", ""

def save_to_excel_optimized(df, filename):
    """儲存並優化 Excel 格式"""
    # filename 若包含完整路徑，pandas 也能處理
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    df.to_excel(writer, index=False)
    worksheet = writer.sheets['Sheet1']
    
    column_settings = {
        'A': 12, 'B': 20, 'C': 15, 'D': 40, 
        'E': 40, 'F': 60, 'G': 40
    }
    for col_letter, width in column_settings.items():
        worksheet.column_dimensions[col_letter].width = width
    
    for row in range(2, len(df) + 2):
        for col in range(1, 8):
            worksheet.cell(row=row, column=col).alignment = Alignment(wrap_text=True, vertical='top')

    writer.close()

# ================= 主程式 =================

def main():
    print(f"【啟動 Kyiv Independent 全功能爬蟲】任務時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    all_final_data = []
    seen_urls = set() 

    for section in SECTIONS:
        section_url = f"{BASE_URL}/tag/{section}/"
        print(f"\n▶ 正在爬取欄目: {section.upper()} (網址: {section_url})")
        
        try:
            res = requests.get(section_url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                print(f"  [跳過] 欄目頁面存取失敗 (Code: {res.status_code})")
                continue
                
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a')
            
            count = 0
            exclude_keywords = ['/tag/', '/author/', '/category/', '/store/', '/jobs/', '/advertising/', '/membership/', '/privacy/', '/cookie/', '/team/', '/contact/', '/about/']

            for link in links:
                title_en = link.get_text(strip=True)
                href = link.get('href', '')
                
                if href and len(title_en) > 20 and href.count('-') >= 3:
                    if not any(k in href for k in exclude_keywords):
                        full_url = href if href.startswith('http') else BASE_URL + href
                        
                        if full_url in seen_urls:
                            continue
                        
                        print(f"  [{count+1}] 發現標題: {title_en[:35]}...")
                        
                        title_tw = translate_text(title_en)
                        date, author, text_en, text_tw = parse_article_content(full_url)
                        
                        if text_tw: 
                            all_final_data.append({
                                "欄目": section.upper(),
                                "日期": date,
                                "作者": author,
                                "標題_英文": title_en,
                                "標題_中文": title_tw,
                                "內文_中文": text_tw,
                                "網址": full_url
                            })
                            seen_urls.add(full_url)
                            count += 1
                
                if count >= 10: break
                    
        except Exception as e:
            print(f"  [欄目錯誤] {section}: {e}")

    # --- 儲存資料 ---
    if all_final_data:
        df = pd.DataFrame(all_final_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"KyivIndependent_Report_{timestamp}.xlsx"
        
        # ### 修改: 判斷儲存路徑
        if len(sys.argv) > 1:
            save_dir = sys.argv[1]
        else:
            save_dir = "."
            
        full_path = os.path.join(save_dir, filename)
        
        save_to_excel_optimized(df, full_path) # 傳入完整路徑
        print(f"\n✅ 任務完成！已成功儲存 {len(all_final_data)} 筆新聞至 {full_path}")
    else:
        print("\n❌ 失敗：未抓取到任何資料。請確認網路環境或網址是否可存取。")

if __name__ == "__main__":
    main()