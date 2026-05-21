from pathlib import Path

import chromadb

# 1. 初始化本地向量数据库
# 它会在你的当前目录下生成一个名为 "my_vector_db" 的文件夹来持久化保存数据
PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "my_vector_db"

DB_PATH.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(DB_PATH))

# 2. 创建一个“集合”（相当于关系型数据库里的一张 Table 表）
# 注意：第一次运行这段代码时，ChromaDB 会自动从网上下载一个极轻量级的开源大模型（用来将文本变成数字向量），大概需要等 1-2 分钟。
collection = client.get_or_create_collection(name="company_rules")

# 3. 数据写入：把我们的规章制度“切片”存进去
# ChromaDB 底层会默默把这三句话翻译成几百维的数字坐标！
collection.upsert(
    documents=[
        "员工每月交通补助上限为 800 元，超出部分需由部门总监审批。",
        "购买办公用品必须在指定的“星辰采购网”进行，否则不予报销。",
        "报销单提交截止时间为每月 25 号下午 5 点，逾期顺延至次月。"
    ],
    ids=["rule_1", "rule_2", "rule_3"] # 必须给每条知识发一个身份证号
)

print("✅ 知识切片已成功向量化并存入本地数据库！\n")

# =========================================================
# 4. 魔法时刻：让数据库根据语义进行“相似度检索”
# =========================================================
query_text = "我昨天在淘宝买了一把人体工学椅，花了 300 块钱，可以找财务报销吗？"
print(f"🧐 用户提问: {query_text}")
print("🔍 正在多维向量空间中计算距离...\n")

# 执行搜索：找出和这句提问在数学空间上“距离最近”的 1 条规定
results = collection.query(
    query_texts=[query_text],
    n_results=1 
)

print("🎯 检索完成！系统匹配到的最相关规定是：")
# results 返回的是一个嵌套的字典和列表结构，我们把它剥洋葱拿出来
print(results['documents'][0][0])
