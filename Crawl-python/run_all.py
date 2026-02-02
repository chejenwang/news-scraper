import os
import glob
import subprocess
import time
import sys

# ================= 設定區 (自動偵測環境) =================
# 取得目前 run_all.py 所在的絕對路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 爬蟲程式所在的資料夾 (設為與 run_all.py 同一個目錄)
SCRIPTS_DIR = BASE_DIR 

# 資料儲存路徑：優先接收 GitHub 傳入的參數，若無則在本地建立 data 資料夾
if len(sys.argv) > 1:
    DATA_OUTPUT_DIR = sys.argv[1]
else:
    DATA_OUTPUT_DIR = os.path.join(BASE_DIR, "data")

MASTER_SCRIPT_NAME = 'run_all.py' 
# =======================================================

def run_crawlers():
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
        print(f"✅ 已確認儲存資料夾: {DATA_OUTPUT_DIR}")

    # 搜尋該目錄下所有 .py 檔案
    search_path = os.path.join(SCRIPTS_DIR, "*.py")
    files = glob.glob(search_path)

    print(f"🚀 開始執行任務，偵測到 {len(files)-1} 個爬蟲腳本...")

    for file_path in files:
        file_name = os.path.basename(file_path)
        if file_name == MASTER_SCRIPT_NAME:
            continue

        print(f"\n>>> 正在執行: {file_name}")
        start_time = time.time()
        
        try:
            # 關鍵修正：在 GitHub (Linux) 使用 python3，在 Windows 使用 python
            python_cmd = 'python3' if sys.platform != 'win32' else 'python'
            
            # 執行爬蟲並傳入儲存路徑參數
            subprocess.run(
                [python_cmd, file_path, DATA_OUTPUT_DIR], 
                check=True
            )
            print(f"✅ {file_name} 成功！(耗時: {time.time() - start_time:.1f}秒)")
        except subprocess.CalledProcessError:
            print(f"❌ {file_name} 執行出錯 (回傳非零狀態碼)")
        except Exception as e:
            print(f"⚠️ 發生意外錯誤: {e}")

if __name__ == "__main__":
    run_crawlers()
