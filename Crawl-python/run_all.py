import os
import glob
import subprocess
import time

# ================= 設定區 (使用相對路徑) =================
# 獲取目前 run_all.py 所在的資料夾路徑 (即 Crawl-python 資料夾)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 爬蟲程式所在的資料夾 (就是目前這個資料夾)
SCRIPTS_DIR = BASE_DIR

# 資料要儲存的目標資料夾 (news-scraper/data)
# .. 代表回上一層，然後進入 data 資料夾
DATA_OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'data'))

# 主程式名稱，避免重複執行
MASTER_SCRIPT_NAME = 'run_all.py' 
# ==========================================

def run_crawlers():
    # 1. 確保 news-scraper/data 資料夾存在
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
        print(f"已建立輸出資料夾: {DATA_OUTPUT_DIR}")

    # 2. 抓取 Crawl-python 內所有的 .py 檔案
    search_path = os.path.join(SCRIPTS_DIR, "*.py")
    files = glob.glob(search_path)

    print(f"=== 偵測到 {len(files)} 個 Python 檔案，準備依序執行 ===")
    print(f"輸出儲存路徑: {DATA_OUTPUT_DIR}\n")

    for file_path in files:
        file_name = os.path.basename(file_path)

        # 跳過主程式自己
        if file_name == MASTER_SCRIPT_NAME:
            continue

        print(f"--------------------------------------------------")
        print(f"正在執行爬蟲: {file_name} ...")
        
        start_time = time.time()
        
        try:
            # 3. 執行爬蟲，並將輸出路徑傳給子程式
            # 確保子程式 (如 Interfax-Ukraine.py) 會讀取 sys.argv[1] 作為儲存路徑
            subprocess.run(
                ['python', file_path, DATA_OUTPUT_DIR], 
                cwd=SCRIPTS_DIR,
                check=True
            )
            
            elapsed_time = time.time() - start_time
            print(f"✅ 執行成功: {file_name} (耗時: {elapsed_time:.2f} 秒)")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 執行失敗: {file_name} (錯誤代碼: {e.returncode})")
        except Exception as e:
            print(f"❌ 發生未預期錯誤: {e}")

        # 間隔休息，避免被網站封鎖
        time.sleep(2)

    print("\n==================================================")
    print("所有爬蟲任務已執行完畢。")

if __name__ == '__main__':
    run_crawlers()
