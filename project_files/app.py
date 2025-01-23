from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import pandas as pd
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# 设置模板和静态文件目录
app.template_folder = 'templates'
app.static_folder = 'static'

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class Employee:
    def __init__(self, name, max_picking=1000, 
                 can_handle_large_orders=False,
                 has_vh_skill=False,
                 has_estero_skill=False):
        self.name = name
        self.max_picking = max_picking
        self.can_handle_large_orders = can_handle_large_orders
        self.has_vh_skill = has_vh_skill
        self.has_estero_skill = has_estero_skill
        self.is_present = False
        self.current_total_picking = 0
        self.assigned_orders = []

class WarehouseManager:
    def __init__(self):
        self.employees = self.load_employees()
        
    def load_employees(self):
        try:
            with open('employees.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {name: Employee(**emp_data) for name, emp_data in data.items()}
        except FileNotFoundError:
            return {}
            
    def save_employees(self):
        data = {name: {
            'name': emp.name,
            'max_picking': emp.max_picking,
            'can_handle_large_orders': emp.can_handle_large_orders,
            'has_vh_skill': emp.has_vh_skill,
            'has_estero_skill': emp.has_estero_skill
        } for name, emp in self.employees.items()}
        
        with open('employees.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def distribute_tasks(self, orders_df):
        # ... 保持原有的任务分配逻辑 ...
        pass

warehouse = WarehouseManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/employees')
def employees_page():
    return render_template('employees.html')

@app.route('/tasks')
def tasks_page():
    return render_template('tasks.html')

@app.route('/api/employees', methods=['GET'])
def get_employees():
    return jsonify({
        name: {
            'name': emp.name,
            'max_picking': emp.max_picking,
            'can_handle_large_orders': emp.can_handle_large_orders,
            'has_vh_skill': emp.has_vh_skill,
            'has_estero_skill': emp.has_estero_skill,
            'is_present': emp.is_present
        } for name, emp in warehouse.employees.items()
    })

@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.json
    if data['name'] in warehouse.employees:
        return jsonify({'error': '员工已存在'}), 400
    
    warehouse.employees[data['name']] = Employee(**data)
    warehouse.save_employees()
    return jsonify({'message': '添加成功'})

@app.route('/api/employees/<name>', methods=['PUT'])
def update_employee(name):
    if name not in warehouse.employees:
        return jsonify({'error': '员工不存在'}), 404
    
    data = request.json
    emp = warehouse.employees[name]
    emp.max_picking = data['max_picking']
    emp.can_handle_large_orders = data['can_handle_large_orders']
    emp.has_vh_skill = data['has_vh_skill']
    emp.has_estero_skill = data['has_estero_skill']
    emp.is_present = data['is_present']
    
    warehouse.save_employees()
    return jsonify({'message': '更新成功'})

@app.route('/api/employees/<name>', methods=['DELETE'])
def delete_employee(name):
    if name not in warehouse.employees:
        return jsonify({'error': '员工不存在'}), 404
    
    del warehouse.employees[name]
    warehouse.save_employees()
    return jsonify({'message': '删除成功'})

@app.route('/api/tasks/distribute', methods=['POST'])
def distribute_tasks():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            orders_df = pd.read_csv(filepath)
            results = warehouse.distribute_tasks(orders_df)
            return jsonify(results)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True) 