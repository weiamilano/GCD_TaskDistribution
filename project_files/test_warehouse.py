import tkinter as tk
from warehouse_manager import WarehouseManager
import pandas as pd
import os

def create_test_data():
    """创建测试用的员工数据和CSV文件"""
    # 创建测试员工数据
    test_employees = {
        "张三": {
            "name": "张三",
            "max_picking": 800,
            "can_handle_large_orders": True,
            "has_vh_skill": True,
            "has_estero_skill": False
        },
        "李四": {
            "name": "李四",
            "max_picking": 1200,
            "can_handle_large_orders": True,
            "has_vh_skill": True,
            "has_estero_skill": True
        },
        "王五": {
            "name": "王五",
            "max_picking": 500,
            "can_handle_large_orders": False,
            "has_vh_skill": False,
            "has_estero_skill": True
        }
    }
    
    # 保存测试员工数据
    import json
    with open('employees.json', 'w', encoding='utf-8') as f:
        json.dump(test_employees, f, ensure_ascii=False, indent=2)
    
    # 创建测试订单数据
    test_orders = {
        'Rif.': [
            'ORD2412090092',
            'ORD2412090093',
            'ORD2412090094',
            'ORD2412090095',
            'ORD2412090096'
        ],
        'Data ordine': [
            '09/12/2024',
            '09/12/2024',
            '10/12/2024',
            '10/12/2024',
            '11/12/2024'
        ],
        'Pack Qty': [
            '244',
            '350',
            '150',
            '400',
            '200'
        ],
        'Nota (privata)': [
            'ESTERO + VH',
            'URGENTE',
            '2P',
            'VH',
            'ESTERO'
        ],
        'Tag/categoria': [
            'DECORAZIONE',
            'TRUCCO',
            'FRAGRANZE',
            'STRUMENTI',
            'DECORAZIONE'
        ]
    }
    
    # 创建测试CSV文件
    df = pd.DataFrame(test_orders)
    df.to_csv('test_orders.csv', index=True)
    
    return "测试数据创建成功！\n员工数据保存在 employees.json\n订单数据保存在 test_orders.csv"

def create_test_window():
    """创建测试窗口"""
    test_window = tk.Tk()
    test_window.title("仓库管理系统测试工具")
    test_window.geometry("400x300")
    
    # 创建测试数据按钮
    def on_create_test_data():
        result = create_test_data()
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, result)
    
    create_data_btn = tk.Button(
        test_window, 
        text="1. 创建测试数据", 
        command=on_create_test_data
    )
    create_data_btn.pack(pady=10)
    
    # 启动主程序按钮
    def on_start_main_program():
        test_window.withdraw()  # 隐藏测试窗口
        app = WarehouseManager()
        app.root.protocol("WM_DELETE_WINDOW", 
            lambda: on_main_window_close(test_window, app.root))
        app.run()
    
    start_btn = tk.Button(
        test_window, 
        text="2. 启动主程序", 
        command=on_start_main_program
    )
    start_btn.pack(pady=10)
    
    # 测试说明
    instruction_text = """
测试步骤：

1. 点击"创建测试数据"生成测试用的员工和订单数据

2. 点击"启动主程序"运行仓库管理系统

3. 在员工管理页面：
   - 查看预设的测试员工
   - 可以尝试添加、修改、删除员工
   - 设置员工出勤状态

4. 在任务分配页面：
   - 点击"选择文件"按钮
   - 选择生成的 test_orders.csv
   - 点击"开始分配"进行任务分配
   - 查看分配结果
   - 可以尝试导出Excel和PDF
    """
    
    # 显示结果的文本框
    result_text = tk.Text(test_window, height=10, width=45)
    result_text.pack(pady=10, padx=10)
    result_text.insert(tk.END, instruction_text)
    
    return test_window

def on_main_window_close(test_window, main_window):
    """处理主窗口关闭事件"""
    main_window.destroy()
    test_window.deiconify()  # 显示测试窗口

if __name__ == "__main__":
    test_window = create_test_window()
    test_window.mainloop() 