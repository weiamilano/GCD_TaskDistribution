import PyInstaller.__main__
import os

def build_exe():
    PyInstaller.__main__.run([
        'run.py',
        '--name=仓库管理系统',
        '--onefile',
        '--windowed',
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--icon=icon.ico',
        '--hidden-import=flask',
        '--hidden-import=flask_cors',
        '--hidden-import=pandas',
    ])

if __name__ == '__main__':
    build_exe() 