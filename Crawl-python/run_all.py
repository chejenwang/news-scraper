import os
import glob
import subprocess
import time
import sys

# ================= 設定區 (GitHub Actions 優化版) =================
# 取得目前這個 run_all.py 所在的絕對路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 爬蟲程式所在的資料夾 (假設爬蟲跟 run_all.py 放在一起，或是子資料夾)
# 如果爬蟲在同一個資料夾，就設為 BASE_DIR
SCRIPTS_DIR = BASE_DIR 

# 資料要儲存的目標資料夾 (使用 sys.argv 接收 GitHub 傳入的路徑，否則預設為 ./data)
if len(sys.argv) > 1:
    DATA_OUTPUT_DIR = sys.argv[1]
else:
    DATA_OUTPUT_DIR = os.path.join(BASE_DIR, "data")

MASTER_SCRIPT_NAME = 'run_all.py' 
# ================================================================

def run_crawlers():
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
        print(f"✅ 已建立儲存資料夾: {DATA_OUTPUT_DIR}")

    # 搜尋該目錄下所有 .py 檔案
    search_path = os.path.join(SCRIPTS_DIR, "*.py")
    files = glob.glob(search_path)

    print(f"🚀 偵測到 {len(files)} 個檔案，準備執行...")

    for file_path in files:
        file_name = os.path.basename(file_path)
        if file_name == MASTER_SCRIPT_NAME:
            continue

        print(f"\n--- 正在執行: {file_name} ---")
        start_time = time.time()
        
        try:
            # 關鍵：在 Linux/GitHub 環境下，我們直接調用 python3 執行
            # 並將目標儲存路徑作為第一個參數傳給爬蟲
            subprocess.run(
                ['python3', file_path, DATA_OUTPUT_DIR], 
                check=True
            )
            print(f"✅ {file_name} 執行成功 (耗時: {time.time() - start_time:.1f}s)")
        except subprocess.CalledProcessError as e:
            print(f"❌ {file_name} 執行失敗。錯誤碼: {e.returncode}")
        except Exception as e:
            print(f"⚠️ 發生未知錯誤: {e}")

if __name__ == "__main__":
    run_crawlers()
