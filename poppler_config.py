# Poppler配置
# 此文件由install_poppler.py自动生成

import os
import sys

# Poppler路径
POPPLER_PATH = r"D:\hello_ai\zsSystem\poppler\Library\bin"

# 添加到PATH
if POPPLER_PATH not in os.environ.get('PATH', ''):
    os.environ['PATH'] = POPPLER_PATH + os.pathsep + os.environ.get('PATH', '')
    print(f"已添加Poppler到PATH: {POPPLER_PATH}")
