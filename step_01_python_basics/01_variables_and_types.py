"""
====================================
📘 Python 基础 - 第1课：变量与数据类型 + F-strings
====================================
📌 规则：看完讲解 → 自己动手敲一遍 → 修改代码试试
"""

# ========== 1. 变量与数据类型 ==========

# Python 是动态类型语言，不需要声明类型
name = "小明"          # 字符串 (str)
age = 25               # 整数 (int)
height = 1.75          # 浮点数 (float)
is_student = True      # 布尔值 (bool)

# 用 print() 打印变量
print(name)            # 输出: 小明
print(age)             # 输出: 25

# 查看变量的类型
print(type(name))      # 输出: <class 'str'>
print(type(age))       # 输出: <class 'int'>

# ========== 2. F-strings (格式化字符串) ==========

# F-strings 是在字符串前加 f，用 {} 插入变量或表达式
print(f"我叫{name}，今年{age}岁，身高{height}米")

# 花括号里可以放任何表达式
print(f"明年我就{age + 1}岁了")
print(f"我是不是学生？{is_student}")

# 控制数字精度
pi = 3.1415926
print(f"圆周率约等于 {pi:.2f}")  # 保留2位小数

# ========== 🧪 现在轮到你了！ ==========
# 1. 创建三个新变量：你的名字、出生年份、喜欢的编程语言
# 2. 用 f-string 打印一句自我介绍
# 3. 计算你今年的年龄（用当前年份2026减去出生年份）

# ---- 在这里写你的代码 ----
my_name = "嘉耀"
birth_year = 2004
favorite_language = "Python"
print(f"大家好，我叫{my_name}，我出生于{birth_year}年，我喜欢的编程语言是{favorite_language}。")
# ...

print("\n✅ 第1课完成！继续到下一个文件学习吧！")
