# 请在代码编辑器中，新建一个 Python 文件，综合运用这两组知识：
# 导入 os 模块。
# 使用 os.getenv("MY_SECRET_PASSWORD") 尝试获取一个密码。如果你没有在电脑上配置过这个环境变量，它目前应该是 None。
# 写一个 if/else 判断：
# 如果拿到的值是 None，请使用 with open() 和 "w" 模式，在当前目录下新建一个名为 error.log 的文件，并在里面写入一句话："缺少必要的环境变量配置！"。
# 如果不为 None，则打印 "系统启动成功！"。
import os
os.getenv("MY_SECRET_PASSWORD")
if os.getenv("MY_SECRET_PASSWORD") is None:
    with open("error.log", "w", encoding="utf-8") as f:
        f.write("缺少必要的环境变量配置！")
else:    print("系统启动成功！")
# 数据类型 / 特征	        JSON 语法 (严格)	                    Python 对应概念
# 字符串	                必须使用双引号 ""	                    单双引号皆可 '' 或 ""
# 布尔值 (真/假)	        全小写 true / false	                    首字母大写 True / False
# 空值	                        null	                                 None
# 尾部逗号	               绝对禁止最后一个元素后有逗号	                    允许