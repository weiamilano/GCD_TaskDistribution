import os
import PyInstaller.__main__

# 确保当前目录是项目目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 运行PyInstaller
PyInstaller.__main__.run([
    'warehouse.spec',
    '--clean',
    '--windowed'
]) 