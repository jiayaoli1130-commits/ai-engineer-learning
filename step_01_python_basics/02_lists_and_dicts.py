"""
====================================
📘 Python 基础 - 第2课：列表 (Lists) 和 字典 (Dictionaries)
====================================
📌 列表 = 有序的"购物清单"   字典 = 带标签的"名片夹"
"""

# ========== 1. 列表 (List) ==========

# 创建列表：用方括号 []，元素用逗号隔开
fruits = ["苹果", "香蕉", "橙子", "葡萄"]
print(f"水果列表: {fruits}")

# 访问元素：索引从 0 开始
print(f"第一个水果: {fruits[0]}")     # 苹果
print(f"第二个水果: {fruits[1]}")     # 香蕉
print(f"最后一个: {fruits[-1]}")      # 葡萄（负数从末尾数）

# 添加元素
fruits.append("草莓")                 # 在末尾添加
print(f"添加后: {fruits}")

# 删除元素
fruits.remove("香蕉")                 # 删除指定值
print(f"删除后: {fruits}")

# 列表长度
print(f"水果数量: {len(fruits)}")

# 列表切片 [start:end]
print(f"前三个: {fruits[:3]}")
print(f"后两个: {fruits[-2:]}")

# ========== 2. 字典 (Dictionary) ==========

# 创建字典：用花括号 {}，key: value 成对出现
person = {
    "name": "小明",
    "age": 25,
    "city": "北京",
    "skills": ["Python", "数据分析", "AI"]
}
print(f"\n个人信息: {person}")

# 访问字典值
print(f"姓名: {person['name']}")
print(f"城市: {person['city']}")

# 添加/修改键值对
person["job"] = "AI工程师"           # 新增
person["age"] = 26                    # 修改
print(f"更新后: {person}")

# 安全获取（不存在时返回默认值，不会报错）
# print(person["salary"])            # ❌ 会报错！
print(person.get("salary", "未设置"))  # ✅ 安全: 未设置

# 遍历字典
for key, value in person.items():
    print(f"  {key} -> {value}")

# ========== 3. 列表里套字典（AI项目超常用！）==========

# ChatGPT 的对话历史就是这种结构！
chat_history = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    {"role": "user", "content": "Python怎么学？"},
]

print(f"\n📝 对话记录:")
for msg in chat_history:
    print(f"  [{msg['role']}] {msg['content']}")

# ========== 🧪 轮到你了！ ==========
# 1. 创建一个待办事项列表 todo_list，包含3个任务
# 2. 创建一个字典 book，表示一本书（书名、作者、年份）
# 3. 创建一个 books 列表，包含3本不同的书（每本都是字典）
# 4. 用 for 循环遍历 books，打印每本书的信息

# ---- 在这里写你的代码 ----
#

print("\n✅ 第2课完成！继续到下一个文件学习吧！")
