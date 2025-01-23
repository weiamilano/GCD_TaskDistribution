import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
from datetime import datetime
import json
from typing import Dict, List
import openpyxl
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

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

class WarehouseManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("仓库任务分配系统")
        self.employees: Dict[str, Employee] = self.load_employees()
        self.orders_df = None  # 存储当前CSV文件的数据
        self.distribution_results = {
            'employee_tasks': {},  # 每个员工的任务
            '2p_orders': [],      # 2P订单
            'unassigned': []      # 未分配订单
        }
        self.setup_ui()
        
    def load_employees(self) -> Dict[str, Employee]:
        try:
            with open('employees.json', 'r') as f:
                data = json.load(f)
                return {name: Employee(**emp_data) 
                       for name, emp_data in data.items()}
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
        
        with open('employees.json', 'w') as f:
            json.dump(data, f)

    def setup_ui(self):
        # 创建标签页控件
        notebook = ttk.Notebook(self.root)
        notebook.pack(pady=10, expand=True)

        # 员工管理页面
        self.employee_frame = ttk.Frame(notebook)
        notebook.add(self.employee_frame, text="员工管理")
        self.setup_employee_management()

        # 任务分配页面
        self.task_frame = ttk.Frame(notebook)
        notebook.add(self.task_frame, text="任务分配")
        self.setup_task_management()

    def setup_employee_management(self):
        # 创建左侧的员工列表
        list_frame = ttk.Frame(self.employee_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        
        # 员工列表
        self.employee_listbox = tk.Listbox(list_frame, width=30)
        self.employee_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.employee_listbox.bind('<<ListboxSelect>>', self.on_employee_select)
        
        # 添加和删除按钮
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="添加员工", command=self.add_employee).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="删除员工", command=self.delete_employee).pack(side=tk.RIGHT)
        
        # 创建右侧的员工详情编辑区
        edit_frame = ttk.LabelFrame(self.employee_frame, text="员工详情")
        edit_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 员工信息编辑区域
        self.name_var = tk.StringVar()
        self.max_picking_var = tk.StringVar()
        self.large_orders_var = tk.BooleanVar()
        self.vh_skill_var = tk.BooleanVar()
        self.estero_skill_var = tk.BooleanVar()
        self.is_present_var = tk.BooleanVar()
        
        ttk.Label(edit_frame, text="姓名:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(edit_frame, textvariable=self.name_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(edit_frame, text="最大picking数量:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(edit_frame, textvariable=self.max_picking_var).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Checkbutton(edit_frame, text="可处理大订单(>300)", variable=self.large_orders_var).grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        ttk.Checkbutton(edit_frame, text="VH技能", variable=self.vh_skill_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        ttk.Checkbutton(edit_frame, text="ESTERO技能", variable=self.estero_skill_var).grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        ttk.Checkbutton(edit_frame, text="今日出勤", variable=self.is_present_var).grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        ttk.Button(edit_frame, text="保存修改", command=self.save_employee_details).grid(row=6, column=0, columnspan=2, pady=10)
        
        self.refresh_employee_list()

    def setup_task_management(self):
        # 文件上传区域
        upload_frame = ttk.LabelFrame(self.task_frame, text="任务文件上传")
        upload_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(upload_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(upload_frame, text="选择文件", command=self.select_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(upload_frame, text="开始分配", command=self.distribute_tasks).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(self.task_frame, text="分配结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text(result_frame)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 导出按钮
        export_frame = ttk.Frame(self.task_frame)
        export_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(export_frame, text="导出Excel", command=self.export_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="导出PDF", command=self.export_pdf).pack(side=tk.LEFT, padx=5)

    def add_employee(self):
        name = simpledialog.askstring("添加员工", "请输入员工姓名:")
        if name:
            if name in self.employees:
                messagebox.showerror("错误", "该员工已存在!")
                return
            self.employees[name] = Employee(name)
            self.save_employees()
            self.refresh_employee_list()

    def delete_employee(self):
        selection = self.employee_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的员工!")
            return
        name = self.employee_listbox.get(selection[0])
        if messagebox.askyesno("确认", f"确定要删除员工 {name} 吗?"):
            del self.employees[name]
            self.save_employees()
            self.refresh_employee_list()

    def on_employee_select(self, event):
        selection = self.employee_listbox.curselection()
        if not selection:
            return
        name = self.employee_listbox.get(selection[0])
        emp = self.employees[name]
        
        self.name_var.set(emp.name)
        self.max_picking_var.set(str(emp.max_picking))
        self.large_orders_var.set(emp.can_handle_large_orders)
        self.vh_skill_var.set(emp.has_vh_skill)
        self.estero_skill_var.set(emp.has_estero_skill)
        self.is_present_var.set(emp.is_present)

    def save_employee_details(self):
        selection = self.employee_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择员工!")
            return
            
        name = self.employee_listbox.get(selection[0])
        emp = self.employees[name]
        
        try:
            max_picking = int(self.max_picking_var.get())
        except ValueError:
            messagebox.showerror("错误", "最大picking数量必须是数字!")
            return
            
        emp.max_picking = max_picking
        emp.can_handle_large_orders = self.large_orders_var.get()
        emp.has_vh_skill = self.vh_skill_var.get()
        emp.has_estero_skill = self.estero_skill_var.get()
        emp.is_present = self.is_present_var.get()
        
        self.save_employees()
        messagebox.showinfo("成功", "员工信息已更新!")

    def refresh_employee_list(self):
        self.employee_listbox.delete(0, tk.END)
        for name in sorted(self.employees.keys()):
            self.employee_listbox.insert(tk.END, name)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv")]
        )
        if file_path:
            self.file_path_var.set(file_path)

    def distribute_tasks(self):
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "请先选择任务文件!")
            return
            
        try:
            # 读取CSV文件
            self.orders_df = pd.read_csv(file_path, encoding='utf-8')
            
            # 重置分配结果
            self.distribution_results = {
                'employee_tasks': {},
                '2p_orders': [],
                'unassigned': []
            }
            
            # 获取在场员工列表
            present_employees = {name: emp for name, emp in self.employees.items() 
                              if emp.is_present}
            
            if not present_employees:
                messagebox.showwarning("警告", "没有出勤的员工!")
                return
                
            # 首先处理2P订单
            mask_2p = self.orders_df['Nota (privata)'].str.contains('2P', na=False)
            self.distribution_results['2p_orders'] = self.orders_df[mask_2p].to_dict('records')
            
            # 获取需要分配的订单
            remaining_orders = self.orders_df[~mask_2p].copy()
            
            # 按优先级排序：Data ordine日期优先，URGENTE次之
            remaining_orders['Data ordine'] = pd.to_datetime(remaining_orders['Data ordine'], 
                                                          format='%d/%m/%Y')
            remaining_orders['is_urgent'] = remaining_orders['Nota (privata)'].str.contains('URGENTE', 
                                                                                          na=False)
            remaining_orders = remaining_orders.sort_values(['Data ordine', 'is_urgent'], 
                                                         ascending=[True, False])
            
            # 初始化员工任务列表
            for emp_name in present_employees:
                self.distribution_results['employee_tasks'][emp_name] = []
            
            # 分配订单
            for _, order in remaining_orders.iterrows():
                assigned = False
                pack_qty = int(order['Pack Qty'])
                nota = str(order['Nota (privata)'])
                
                # 找到合适的员工
                best_employee = None
                min_workload = float('inf')
                
                for emp_name, emp in present_employees.items():
                    # 检查员工是否满足订单要求
                    if (pack_qty > 300 and not emp.can_handle_large_orders or
                        'VH' in nota and not emp.has_vh_skill or
                        'ESTERO' in nota and not emp.has_estero_skill or
                        emp.current_total_picking + pack_qty > emp.max_picking):
                        continue
                    
                    # 选择工作量最少的合适员工
                    current_workload = emp.current_total_picking
                    if current_workload < min_workload:
                        min_workload = current_workload
                        best_employee = emp_name
                
                if best_employee:
                    self.distribution_results['employee_tasks'][best_employee].append(order.to_dict())
                    present_employees[best_employee].current_total_picking += pack_qty
                    assigned = True
                
                if not assigned:
                    self.distribution_results['unassigned'].append(order.to_dict())
            
            # 显示分配结果
            self.display_results()
            
        except Exception as e:
            messagebox.showerror("错误", f"任务分配失败: {str(e)}")

    def display_results(self):
        self.result_text.delete(1.0, tk.END)
        
        # 显示员工任务
        self.result_text.insert(tk.END, "=== 员工任务分配 ===\n\n")
        for emp_name, tasks in self.distribution_results['employee_tasks'].items():
            total_qty = sum(int(task['Pack Qty']) for task in tasks)
            self.result_text.insert(tk.END, f"{emp_name} (总数量: {total_qty}):\n")
            for task in tasks:
                self.result_text.insert(tk.END, 
                    f"  - 订单号: {task['Rif.']} | 数量: {task['Pack Qty']} | "
                    f"类别: {task['Tag/categoria']}\n")
            self.result_text.insert(tk.END, "\n")
        
        # 显示2P订单
        self.result_text.insert(tk.END, "=== 2P订单 ===\n\n")
        for order in self.distribution_results['2p_orders']:
            self.result_text.insert(tk.END, 
                f"订单号: {order['Rif.']} | 数量: {order['Pack Qty']}\n")
        
        # 显示未分配订单
        self.result_text.insert(tk.END, "\n=== 未分配订单 ===\n\n")
        for order in self.distribution_results['unassigned']:
            self.result_text.insert(tk.END, 
                f"订单号: {order['Rif.']} | 数量: {order['Pack Qty']} | "
                f"备注: {order['Nota (privata)']}\n")

    def export_excel(self):
        if not self.distribution_results['employee_tasks']:
            messagebox.showwarning("警告", "没有可导出的分配结果!")
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx")]
            )
            
            if not file_path:
                return
                
            with pd.ExcelWriter(file_path) as writer:
                # 导出员工任务
                for emp_name, tasks in self.distribution_results['employee_tasks'].items():
                    if tasks:
                        df = pd.DataFrame(tasks)
                        df.to_excel(writer, sheet_name=emp_name, index=False)
                
                # 导出2P订单
                if self.distribution_results['2p_orders']:
                    df = pd.DataFrame(self.distribution_results['2p_orders'])
                    df.to_excel(writer, sheet_name='2P订单', index=False)
                
                # 导出未分配订单
                if self.distribution_results['unassigned']:
                    df = pd.DataFrame(self.distribution_results['unassigned'])
                    df.to_excel(writer, sheet_name='未分配订单', index=False)
            
            messagebox.showinfo("成功", "Excel文件导出成功!")
            
        except Exception as e:
            messagebox.showerror("错误", f"Excel导出失败: {str(e)}")

    def export_pdf(self):
        if not self.distribution_results['employee_tasks']:
            messagebox.showwarning("警告", "没有可导出的分配结果!")
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF文件", "*.pdf")]
            )
            
            if not file_path:
                return
                
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            
            # 定义表格样式
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            
            # 为每个员工创建表格
            for emp_name, tasks in self.distribution_results['employee_tasks'].items():
                if tasks:
                    elements.append(Paragraph(f"员工: {emp_name}"))
                    data = [['订单号', '数量', '类别']]
                    for task in tasks:
                        data.append([
                            task['Rif.'],
                            task['Pack Qty'],
                            task['Tag/categoria'][:50]  # 限制长度
                        ])
                    table = Table(data)
                    table.setStyle(style)
                    elements.append(table)
                    elements.append(Spacer(1, 20))
            
            # 创建2P订单表格
            if self.distribution_results['2p_orders']:
                elements.append(Paragraph("2P订单"))
                data = [['订单号', '数量']]
                for order in self.distribution_results['2p_orders']:
                    data.append([order['Rif.'], order['Pack Qty']])
                table = Table(data)
                table.setStyle(style)
                elements.append(table)
                elements.append(Spacer(1, 20))
            
            # 创建未分配订单表格
            if self.distribution_results['unassigned']:
                elements.append(Paragraph("未分配订单"))
                data = [['订单号', '数量', '备注']]
                for order in self.distribution_results['unassigned']:
                    data.append([
                        order['Rif.'],
                        order['Pack Qty'],
                        order['Nota (privata)'][:50]  # 限制长度
                    ])
                table = Table(data)
                table.setStyle(style)
                elements.append(table)
            
            # 生成PDF
            doc.build(elements)
            messagebox.showinfo("成功", "PDF文件导出成功!")
            
        except Exception as e:
            messagebox.showerror("错误", f"PDF导出失败: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = WarehouseManager()
    app.run() 