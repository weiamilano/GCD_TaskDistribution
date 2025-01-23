import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, 
                            QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QCheckBox, QPushButton, QListWidget, QFileDialog,
                            QTextEdit, QMessageBox, QSpinBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
import pandas as pd
import json
import os
from datetime import datetime
from resources import Icons

class Employee:
    def __init__(self, name: str, max_picking: int = 1000, 
                 can_handle_large_orders: bool = False,
                 has_vh_skill: bool = False,
                 has_estero_skill: bool = False):
        self.name = name
        self.max_picking = max_picking
        self.can_handle_large_orders = can_handle_large_orders
        self.has_vh_skill = has_vh_skill
        self.has_estero_skill = has_estero_skill
        self.is_present = False
        self.current_total_picking = 0
        self.assigned_orders = []

class WarehouseGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.employees = self.load_employees()
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #e1e1e1;
                padding: 8px 20px;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLineEdit, QSpinBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background: white;
            }
            QLabel {
                color: #333333;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('仓库管理系统')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(Icons.MAIN))
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 创建员工管理页面
        self.employee_tab = QWidget()
        self.setup_employee_tab()
        self.tabs.addTab(self.employee_tab, "员工管理")
        
        # 创建任务分配页面
        self.task_tab = QWidget()
        self.setup_task_tab()
        self.tabs.addTab(self.task_tab, "任务分配")
        
    def setup_employee_tab(self):
        layout = QHBoxLayout()
        
        # 左侧员工列表
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        self.employee_list = QListWidget()
        self.employee_list.itemClicked.connect(self.on_employee_select)
        
        add_button = QPushButton('添加员工')
        add_button.clicked.connect(self.add_employee)
        add_button.setIcon(QIcon(Icons.ADD))
        
        delete_button = QPushButton('删除员工')
        delete_button.clicked.connect(self.delete_employee)
        delete_button.setIcon(QIcon(Icons.DELETE))
        
        left_layout.addWidget(QLabel('员工列表'))
        left_layout.addWidget(self.employee_list)
        left_layout.addWidget(add_button)
        left_layout.addWidget(delete_button)
        
        # 添加一些间距和样式
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(10)
        
        # 设置固定宽度
        left_widget.setFixedWidth(300)
        
        # 添加标题样式
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        employee_list_label = QLabel('员工列表')
        employee_list_label.setFont(title_font)
        left_layout.insertWidget(0, employee_list_label)
        
        form_title = QLabel('员工信息')
        form_title.setFont(title_font)
        left_layout.insertWidget(0, form_title)
        
        right_widget = QWidget()
        form_layout = QVBoxLayout()
        
        self.name_input = QLineEdit()
        self.max_picking_input = QSpinBox()
        self.max_picking_input.setMaximum(10000)
        self.max_picking_input.setValue(1000)
        
        self.large_orders_check = QCheckBox('可处理大订单')
        self.vh_skill_check = QCheckBox('VH技能')
        self.estero_skill_check = QCheckBox('ESTERO技能')
        self.is_present_check = QCheckBox('今日出勤')
        
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.save_employee)
        save_button.setIcon(QIcon(Icons.SAVE))
        
        form_layout.addWidget(QLabel('姓名:'))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel('最大picking数量:'))
        form_layout.addWidget(self.max_picking_input)
        form_layout.addWidget(self.large_orders_check)
        form_layout.addWidget(self.vh_skill_check)
        form_layout.addWidget(self.estero_skill_check)
        form_layout.addWidget(self.is_present_check)
        form_layout.addWidget(save_button)
        form_layout.addStretch()
        
        right_widget.setLayout(form_layout)
        
        # 添加到主布局
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        self.employee_tab.setLayout(layout)
        
        self.refresh_employee_list()
        
    def setup_task_tab(self):
        layout = QVBoxLayout()
        
        # 文件选择
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel('未选择文件')
        select_file_btn = QPushButton('选择文件')
        select_file_btn.clicked.connect(self.select_file)
        select_file_btn.setIcon(QIcon(Icons.FILE))
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(select_file_btn)
        
        # 分配按钮
        distribute_btn = QPushButton('开始分配')
        distribute_btn.clicked.connect(self.distribute_tasks)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        
        # 导出按钮
        export_layout = QHBoxLayout()
        excel_btn = QPushButton('导出Excel')
        excel_btn.clicked.connect(self.export_excel)
        excel_btn.setIcon(QIcon(Icons.EXPORT))
        pdf_btn = QPushButton('导出PDF')
        pdf_btn.clicked.connect(self.export_pdf)
        pdf_btn.setIcon(QIcon(Icons.EXPORT))
        export_layout.addWidget(excel_btn)
        export_layout.addWidget(pdf_btn)
        
        # 添加样式和间距
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 美化文件选择区域
        file_frame = QWidget()
        file_frame.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        file_layout.setContentsMargins(10, 10, 10, 10)
        file_frame.setLayout(file_layout)
        
        # 设置结果显示区域样式
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 10px;
                background: white;
            }
        """)
        
        layout.addLayout(file_frame)
        layout.addWidget(distribute_btn)
        layout.addWidget(self.result_text)
        layout.addLayout(export_layout)
        
        self.task_tab.setLayout(layout)
    
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
    
    def refresh_employee_list(self):
        self.employee_list.clear()
        for name in sorted(self.employees.keys()):
            self.employee_list.addItem(name)
    
    def add_employee(self):
        self.name_input.clear()
        self.max_picking_input.setValue(1000)
        self.large_orders_check.setChecked(False)
        self.vh_skill_check.setChecked(False)
        self.estero_skill_check.setChecked(False)
        self.is_present_check.setChecked(False)
        self.name_input.setEnabled(True)
    
    def save_employee(self):
        name = self.name_input.text()
        if not name:
            QMessageBox.warning(self, '警告', '请输入员工姓名')
            return
        
        emp = Employee(
            name=name,
            max_picking=self.max_picking_input.value(),
            can_handle_large_orders=self.large_orders_check.isChecked(),
            has_vh_skill=self.vh_skill_check.isChecked(),
            has_estero_skill=self.estero_skill_check.isChecked()
        )
        emp.is_present = self.is_present_check.isChecked()
        
        self.employees[name] = emp
        self.save_employees()
        self.refresh_employee_list()
        QMessageBox.information(self, '成功', '保存成功')
    
    def delete_employee(self):
        current_item = self.employee_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, '警告', '请先选择要删除的员工')
            return
        
        name = current_item.text()
        if QMessageBox.question(self, '确认', f'确定要删除员工 {name} 吗？') == QMessageBox.Yes:
            del self.employees[name]
            self.save_employees()
            self.refresh_employee_list()
    
    def on_employee_select(self, item):
        name = item.text()
        emp = self.employees[name]
        
        self.name_input.setText(emp.name)
        self.name_input.setEnabled(False)
        self.max_picking_input.setValue(emp.max_picking)
        self.large_orders_check.setChecked(emp.can_handle_large_orders)
        self.vh_skill_check.setChecked(emp.has_vh_skill)
        self.estero_skill_check.setChecked(emp.has_estero_skill)
        self.is_present_check.setChecked(emp.is_present)
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择CSV文件', '', 'CSV files (*.csv)')
        if file_path:
            self.file_path_label.setText(file_path)
    
    def distribute_tasks(self):
        file_path = self.file_path_label.text()
        if file_path == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择文件')
            return
        
        try:
            # 这里添加任务分配的逻辑
            pass
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))
    
    def export_excel(self):
        # 添加Excel导出逻辑
        pass
    
    def export_pdf(self):
        # 添加PDF导出逻辑
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WarehouseGUI()
    ex.show()
    sys.exit(app.exec_()) 