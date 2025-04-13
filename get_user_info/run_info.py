import os
import subprocess
import time
import webbrowser
import requests
import pandas as pd

# Step 0: 切换到当前脚本所在的目录（确保路径正确）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# 设置你的虚拟环境解释器路径（替换为你自己的路径！）
venv_python = r"D:\PycharmProjects\Encode_AI\.encodeaivenv\Scripts\python.exe"
backend_dir = "D:/PycharmProjects/Encode_AI/get_user_info/backend"
survey_url = "http://localhost:8080"
submit_url = "http://localhost:5000/api/submit"
recommend_url = "http://localhost:5000/api/recommend"
# 等待 Flask 启动
def wait_for_backend(url=submit_url, timeout=10):
    print("🕐 Waiting for backend to be ready...")
    for i in range(timeout):
        try:
            response = requests.options(url)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return
        except:
            pass
        time.sleep(1)
    print("❌ Backend not responding after waiting.")
    exit(1)

# Step 1: 启动 Flask 后端
backend_process = subprocess.Popen([venv_python, "app.py"], cwd="backend")

# Step 2: 等待 Flask 启动完成
wait_for_backend()

# Step 3: 启动前端本地 HTTP 服务
frontend_process = subprocess.Popen([venv_python, "-m", "http.server", "8080"], cwd="frontend")

# Step 4: 打开浏览器
print("🌐 Opening questionnaire in browser...")
webbrowser.open(survey_url)

# Step 5: 等待用户填写完毕
input("📋 Press Enter when you finish filling the form...\n")

# Step 6: 显示保存的 CSV 文件

csv_files = [f for f in os.listdir(backend_dir) if f.startswith("user_answer") and f.endswith(".csv")]
csv_files.sort(reverse=True)

# Step 6: 显示保存的 CSV 文件 + 推荐用户
if csv_files:
    latest_file = csv_files[0]
    filepath = os.path.join(backend_dir, latest_file)
    print(f"\n📄 Latest saved file: {latest_file}")
    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="ISO-8859-1")

    print(df.to_string(index=False))

    # Step 6.1: 发送请求到后端获取推荐
    print("\n🔍 Fetching top match recommendations from backend...")
    try:
        res = requests.post(recommend_url, json={"answers": df.iloc[0].tolist()}, timeout=15)
        result = res.json()
        print(f"\n✅ Recommendations from {latest_file}:")
        for r in result["recommendations"]:
            print(f"• User {r['index'] + 1}: {r['name']} (Score: {r['score']:.4f})")
    except Exception as e:
        print("❌ Failed to fetch recommendations:", e)

else:
    print("⚠️ No saved answer file found.")


# Step 7: 停止服务
backend_process.terminate()
frontend_process.terminate()
