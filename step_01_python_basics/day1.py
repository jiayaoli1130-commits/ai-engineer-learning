# 实操测试
# 请在代码编辑器中完成以下挑战：
# 创建一个列表，存储你未来想构建的 3 个 AI 相关的项目名称。
# 创建一个字典，代表你的开发者档案。包含三个 Key："username" (字符串), "is_pro" (布尔值), 和 "projects" (把你刚才创建的列表赋值给它)。
# 通过列表操作，给你的项目列表追加第 4 个项目。
# 通过字典操作，把 "is_pro" 的值修改为相反的布尔值。
# 使用 F-strings 打印输出类似这句话：“开发者 [用户名] 的 Pro 状态为 [状态]，目前规划了 [项目总数] 个项目。”（提示：使用 len(列表名) 可以获取列表内的元素数量）。

node=["智能聊天机器人", "图像识别系统", "自动化数据分析工具"]
book={
    "username":"li",
    "is_pro":False,
    "projects":node
}
node.append("语音助手")
book["is_pro"]=True
print(f"开发者 {book['username']} 的 Pro 状态为 {book['is_pro']}，目前规划了 {len(book['projects'])} 个项目。")

# 实操测试（结合前两节内容）
# 请在代码编辑器中完成以下模拟“简易机器人拦截系统”的挑战：
# 定义一个变量 user_input 模拟用户的输入文字（可以随便赋一个字符串值）。
# 写一个 while 循环，条件设置为 True（这是一个无限循环）。
# 在循环内部，使用内置函数 input("请输入：") 让用户从终端输入内容，并将其赋值给 user_input。
# 使用 if/elif/else 判断用户的输入：
# 如果输入是 "退出"，使用 break 关键字打破（退出）循环。
# 如果输入包含在列表 ["你好", "hello", "hi"] 中（提示：使用 if user_input in 列表: 语法），打印返回 "检测到打招呼语法！"。
# 其他情况，打印返回 f"你刚才说：{user_input}"。

user_input = "模拟输入"
while True:
    user_input = input("请输入：")
    if user_input == "退出":
        break
    elif user_input in ["你好", "hello", "hi"]:
        print("检测到打招呼语法！")
    else:
        print(f"你刚才说：{user_input}")

# 请在你的编辑器中完成以下任务（这将为你 Step 3 的项目打下直接基础）：
# 定义一个名为 chat_with_bot 的函数，它接收一个参数 user_message。
# 在函数内部，进行条件判断：
# 如果 user_message 是 "你好"，返回 "你好！我是你的 AI 助手。"
# 如果 user_message 是 "退出"，返回 "SYSTEM_EXIT"
# 其他情况，返回 f"正在思考如何回复：{user_message}"
# 在函数外部，写一个 while True: 的无限循环。
# 在循环内使用 input() 获取用户输入，并把输入传递给你刚刚写好的 chat_with_bot 函数。
# 接收函数的返回值：如果返回值是 "SYSTEM_EXIT"，则打破循环；否则，打印出这个返回值。
def chat_with_bot(user_message):
    if user_message =="你好":
        return "你好！我是你的 AI 助手。"
    elif user_message =="退出":
        return "SYSTEM_EXIT"
    else:
        return f"正在思考如何回复：{user_message}"
while True:
    user_message = input("请输入：")
    response = chat_with_bot(user_message)
    if response == "SYSTEM_EXIT":
        break
    else:
        print(response)

    
# 数据层：定义一个全局字典变量 memory，预先存入两条基础信息，例如：{"名字": "Python助手", "版本": "v1.0"}。
# 逻辑层：定义一个函数 get_response(user_msg)：
# 在函数内判断 user_msg 是否存在于 memory 字典的键 (keys) 中（提示：使用 if user_msg in memory:）。
# 如果存在，return 对应的值。
# 如果不存在，return 字符串 "抱歉，我的记忆里没有这条信息。"
# 交互层：在函数外部构建一个 while True: 的无限循环：
# 通过 input() 接收用户输入。
# 如果输入是 "退出"，则 break 结束程序。
# 否则，将输入传递给 get_response 函数，接收返回值，并使用 F-strings 打印输出格式为：AI: [返回值]。
memory ={"名字": "Python助手", "版本": "v1.0"}
def get_response(user_msg):
    if user_msg in memory:
        return memory[user_msg]
    else:
        return "抱歉，我的记忆里没有这条信息。"
    while True:
        input_msg = input("请输入：")
        if input_msg == "退出":
            break
        else:
            response = get_response(input_msg)
            print(f"AI: {response}")    