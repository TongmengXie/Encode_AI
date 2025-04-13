from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

app = Flask(__name__)
CORS(app)

# ✅ 自动加载项目根目录 .env 文件
load_dotenv("D:/PycharmProjects/Encode_AI/get_user_info/.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# 路径和设置
BACKEND_DIR = "D:/PycharmProjects/Encode_AI/get_user_info/backend"
USER_POOL_PATH = "D:/PycharmProjects/Encode_AI/get_user_info/user_pool.csv"
WEIGHTS = [0.0, 0.2, 0.1, 0.3, 0.1, 0.3, 0.3, 0.1, 0.3, 0.1, 0.1, 0.1]

# ✅ 嵌入函数
def embed_answer_list(answer_list):
    response = client.embeddings.create(
        input=answer_list,
        model="text-embedding-ada-002"
    )
    return [r.embedding for r in response.data]

# ✅ 计算余弦相似度
def cosine_similarity(a, b):
    return np.dot(a, b)

# ✅ 获取 Top K 匹配
def get_top_matches(similarity_matrix, weights, top_k=3):
    weighted_scores = []
    for row in similarity_matrix:
        score = sum([s * w for s, w in zip(row, weights)])
        weighted_scores.append(score)
    top_users = sorted(enumerate(weighted_scores), key=lambda x: x[1], reverse=True)[:top_k]
    return top_users

# ✅ /api/submit — 仅保存用户答案
@app.route("/api/submit", methods=["POST"])
def submit():
    data = request.json
    answers = data["answers"]

    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_answer_{timestamp}.csv"
    os.makedirs(BACKEND_DIR, exist_ok=True)
    filepath = os.path.join(BACKEND_DIR, filename)
    df = pd.DataFrame([answers])
    df.to_csv(filepath, index=False)

    return jsonify({ "saved_as": filename })

# ✅ /api/recommend — 根据前端传入的 answers 返回推荐用户
@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.json
    answers = data["answers"]

    # 嵌入新用户答案
    sample_embed = [embed_answer_list([str(v)])[0] for v in answers]

    # 嵌入用户池
    user_pool = pd.read_csv(USER_POOL_PATH, encoding="ISO-8859-1")
    pool_embed = []
    for _, row in user_pool.iterrows():
        row_embed = []
        for val in row:
            val_str = str(val) if pd.notna(val) else "N/A"
            row_embed.append(embed_answer_list([val_str])[0])
        pool_embed.append(row_embed)

    # 相似度计算
    similarity_matrix = []
    for row in pool_embed:
        row_sim = [cosine_similarity(sample_embed[i], row[i]) for i in range(len(sample_embed))]
        similarity_matrix.append(row_sim)

    # Top 推荐
    top_matches = get_top_matches(similarity_matrix, WEIGHTS)
    recommendations = []
    for idx, score in top_matches:
        name = user_pool.iloc[idx]['real_name'] if 'real_name' in user_pool.columns else user_pool.iloc[idx][0]
        recommendations.append({ "index": idx, "score": score, "name": name })

    return jsonify({ "recommendations": recommendations })

# ✅ 启动服务器
if __name__ == "__main__":
    app.run(debug=True)