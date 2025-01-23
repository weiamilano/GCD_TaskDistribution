from flask import Flask, render_template
import webbrowser
import threading
import time

def open_browser():
    """启动后延迟1秒打开浏览器"""
    time.sleep(1)
    webbrowser.open('http://localhost:5000')

def start_app():
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/employees')
    def employees():
        return render_template('employees.html')
    
    @app.route('/tasks')
    def tasks():
        return render_template('tasks.html')
    
    # 启动浏览器线程
    threading.Thread(target=open_browser).start()
    
    # 启动Flask应用
    app.run(debug=False)

if __name__ == '__main__':
    start_app() 