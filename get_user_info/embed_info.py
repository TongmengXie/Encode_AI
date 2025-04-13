import pandas as pd
import numpy as np
import os
from openai import OpenAI  # ✅ 新 SDK
from dotenv import load_dotenv


# Step 0: set API key
load_dotenv('D:/PycharmProjects/pythonProject/.env')
# read os environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# print(OPENAI_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)
print("OpenAI API key loaded successfully.")


# Step 1: read data

backend_dir = "D:/PycharmProjects/pythonProject/Encode_AI/get_user_info/backend"
latest_file = "user_answer_20250412_175045.csv" # here you can change the file name based on your needs
user_answer = pd.read_csv(os.path.join(backend_dir, latest_file) )
print(user_answer.info())
user_ts = latest_file.split("_")[2] + latest_file.split("_")[3].split(".")[0]
sample_user_answer = user_answer.iloc[0].to_list()

user_pool = pd.read_csv("../user_pool.csv", encoding="ISO-8859-1")
print(user_pool.info())

# Step 2: embed user_answer and user_pool
def embed_answer_list(answer_list):
    response = client.embeddings.create(
        input=answer_list,
        model="text-embedding-ada-002"  # 新 SDK 用 model 而不是 engine
    )
    return [r.embedding for r in response.data]


sample_embeded_list = []
for value in sample_user_answer:
    if isinstance(value, str):
        sample_embeded = embed_answer_list([value])
        sample_embeded_list.append(sample_embeded[0])
    else:
        print(f"Value is not a string: {value}")
print(sample_embeded_list)

pool_embeded_lists = []
for idx in range(len(user_pool)):
    print(f"Embed old user {idx+1}/{len(user_pool)}")
    old_user_answer = user_pool.iloc[idx].to_list()
    embed_old_user_answer = []
    for col_idx, value in enumerate(old_user_answer):
        column_name = user_pool.columns[col_idx]  # 获取列名
        if isinstance(value, str):
            pool_embeded = embed_answer_list([value])
            embed_old_user_answer.append(pool_embeded[0])
        elif pd.isna(value):
            print(f"[ℹ️ Fixing NaN] User {idx+1}, Column '{column_name}' → 'N/A'")
            pool_embeded = embed_answer_list(["N/A"])
            embed_old_user_answer.append(pool_embeded[0])
        else:
            print(f"[⚠️ Warning] User {idx+1}, Column '{column_name}' has unsupported value: {value}")
            # 你也可以选择替换为 'N/A' 或直接跳过
            pool_embeded = embed_answer_list([str(value)])
            embed_old_user_answer.append(pool_embeded[0])
    pool_embeded_lists.append(embed_old_user_answer)


# Step 3: calculate cosine similarity
def cosine_similarity(a, b):
    return np.dot(a, b)  # OpenAI 向量已单位归一化

similarity_matrix = []

for pool_user_embeds in pool_embeded_lists:
    row_similarity = []
    for i in range(len(sample_embeded_list)):
        sim = cosine_similarity(sample_embeded_list[i], pool_user_embeds[i])
        row_similarity.append(sim)
    similarity_matrix.append(row_similarity)

def save_similarity_matrix(similarity_matrix, output_path="similarity_matrix.csv"):
    """
    Save the similarity matrix to a CSV file.

    Args:
        similarity_matrix (list of list of float): Matrix of per-question similarities.
        output_path (str): File path to save the matrix.
    """
    df = pd.DataFrame(similarity_matrix)
    df.index = [f"User {i+1}" for i in range(len(df))]
    df.columns = [f"Q{j+1}" for j in range(len(df.columns))]
    df.to_csv(output_path)
    return output_path

save_similarity_matrix(similarity_matrix, "backend/similarity_matrix.csv")

print("Similarity matrix saved successfully. Check backend/similarity_matrix.csv.")

# Step 4: get top matches

weights = [0.0, 0.2, 0.1, 0.3,
           0.1, 0.3, 0.3, 0.1,
           0.3, 0.1, 0.1, 0.1]

def get_top_matches(similarity_matrix, weights, top_k=3):
    """
    Given a similarity matrix and question weights, return the top-k most similar users.

    Args:
        similarity_matrix (list of list of float): Per-question cosine similarities.
        weights (list of float): Weights for each question (must match question count).
        top_k (int): Number of top users to return.

    Returns:
        list of tuples: [(user_index, weighted_score), ...] sorted by descending similarity.
    """
    weighted_scores = []
    for row in similarity_matrix:
        score = sum([s * w for s, w in zip(row, weights)])
        weighted_scores.append(score)

    top_users = sorted(enumerate(weighted_scores), key=lambda x: x[1], reverse=True)[:top_k]
    return top_users

# save top matches to csv
def save_top_matches(top_matches, user_pool, output_path="top_matches.csv"):
    """
    Save the top matches to a CSV file.

    Args:
        top_matches (list of tuples): [(user_index, weighted_score), ...].
        user_pool (DataFrame): DataFrame containing user data.
        output_path (str): File path to save the top matches.
    """
    top_users = [user_pool.iloc[idx].to_list() for idx, _ in top_matches]
    df = pd.DataFrame(top_users)
    df.index = [f"User {idx+1}" for idx, _ in top_matches]
    df.to_csv(output_path)
    return output_path


# Example use:
top_matches = get_top_matches(similarity_matrix, weights, top_k=3)
for idx, score in top_matches:
    print(f"User {idx+1} → Similarity Score: {score:.4f}")
    print(f"User {idx+1} Answers: {user_pool.iloc[idx].to_list()}")
    print("---")


save_top_matches(top_matches, user_pool, f"backend/top_matches_user_ts_{user_ts}.csv")
print(f"Top matches saved successfully. Check backend/top_matches_user_ts_{user_ts}.csv.")

