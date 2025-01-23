// 添加所有JavaScript逻辑 
let employees = JSON.parse(localStorage.getItem('employees') || '{}');
let selectedEmployee = null;
let taskData = null;
let distributionResults = null;

function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');
    event.target.classList.add('active');

    if (tabId === 'tasks') {
        refreshAttendanceList();
        // 重置任务分配状态
        document.getElementById('step2').classList.add('hidden');
        document.getElementById('step3').classList.add('hidden');
        document.getElementById('step1').classList.remove('hidden');
    }
}

function refreshEmployeeList() {
    const list = document.getElementById('employeeList');
    list.innerHTML = '';
    Object.entries(employees).forEach(([name, emp]) => {
        const div = document.createElement('div');
        div.className = 'employee-item';
        div.innerHTML = `
            <span>${name}</span>
            <div>
                <button onclick="editEmployee('${name}')">编辑</button>
                <button onclick="deleteEmployee('${name}')">删除</button>
            </div>
        `;
        list.appendChild(div);
    });
}

function refreshAttendanceList() {
    const list = document.getElementById('attendanceList');
    list.innerHTML = '';
    Object.entries(employees).forEach(([name, emp]) => {
        const div = document.createElement('div');
        div.className = 'attendance-item';
        div.innerHTML = `
            <label>
                <input type="checkbox" 
                       ${emp.isPresent ? 'checked' : ''} 
                       onchange="updateAttendance('${name}', this.checked)">
                ${name}
            </label>
        `;
        list.appendChild(div);
    });
}

function updateAttendance(name, isPresent) {
    if (employees[name]) {
        employees[name].isPresent = isPresent;
        localStorage.setItem('employees', JSON.stringify(employees));
    }
}

function confirmAttendance() {
    const presentEmployees = Object.values(employees).filter(emp => emp.isPresent);
    if (presentEmployees.length === 0) {
        alert('请至少选择一名出勤员工！');
        return;
    }
    document.getElementById('step1').classList.add('hidden');
    document.getElementById('step2').classList.remove('hidden');
}

function uploadAndDistribute() {
    const fileInput = document.getElementById('taskFile');
    if (!fileInput.files[0]) {
        alert('请选择任务文件！');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        taskData = parseCSV(e.target.result);
        distributionResults = distributeTasksToEmployees(taskData);
        displayResults(distributionResults);
        document.getElementById('step2').classList.add('hidden');
        document.getElementById('step3').classList.remove('hidden');
    };
    reader.readAsText(fileInput.files[0]);
}

function parseCSV(csv) {
    const lines = csv.split('\n');
    const headers = lines[0].split(',').map(h => h.trim().replace(/^"/, '').replace(/"$/, ''));
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue;
        const values = lines[i].split(',').map(v => v.trim().replace(/^"/, '').replace(/"$/, ''));
        const row = {};
        headers.forEach((header, index) => {
            row[header] = values[index] || '';
        });
        data.push(row);
    }
    return data;
}

function distributeTasksToEmployees(tasks) {
    const results = {
        employeeTasks: {},
        twoPOrders: [],
        unassigned: []
    };

    // 获取在场员工
    const presentEmployees = Object.entries(employees)
        .filter(([_, emp]) => emp.isPresent)
        .map(([name, emp]) => ({
            name,
            ...emp,
            currentTotal: 0
        }));

    // 初始化每个员工的任务列表
    presentEmployees.forEach(emp => {
        results.employeeTasks[emp.name] = [];
    });

    // 处理任务
    tasks.forEach(order => {
        if (order['Nota (privata)']?.includes('2P')) {
            results.twoPOrders.push(order);
            return;
        }

        const packQty = parseInt(order['Pack Qty']);
        const hasVH = order['Nota (privata)']?.includes('VH');
        const hasEstero = order['Nota (privata)']?.includes('ESTERO');

        let bestEmployee = null;
        let minWorkload = Infinity;

        presentEmployees.forEach(emp => {
            if (packQty > 300 && !emp.canHandleLargeOrders) return;
            if (hasVH && !emp.hasVhSkill) return;
            if (hasEstero && !emp.hasEsteroSkill) return;
            if (emp.currentTotal + packQty > emp.maxPicking) return;

            if (emp.currentTotal < minWorkload) {
                minWorkload = emp.currentTotal;
                bestEmployee = emp;
            }
        });

        if (bestEmployee) {
            results.employeeTasks[bestEmployee.name].push(order);
            bestEmployee.currentTotal += packQty;
        } else {
            results.unassigned.push(order);
        }
    });

    return results;
}

function displayResults(results) {
    const resultsDiv = document.getElementById('distributionResults');
    let html = '';

    // 显示员工任务
    html += '<div class="results-section"><h4>员工任务分配</h4>';
    Object.entries(results.employeeTasks).forEach(([name, tasks]) => {
        const totalQty = tasks.reduce((sum, task) => sum + parseInt(task['Pack Qty']), 0);
        html += `
            <div class="employee-tasks">
                <h5>${name} (总数量: ${totalQty})</h5>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>订单号</th>
                            <th>数量</th>
                            <th>类别</th>
                            <th>备注</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tasks.map(task => `
                            <tr>
                                <td>${task['Rif.']}</td>
                                <td>${task['Pack Qty']}</td>
                                <td>${task['Tag/categoria']}</td>
                                <td>${task['Nota (privata)'] || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    });
    html += '</div>';

    // 显示2P订单
    if (results.twoPOrders.length > 0) {
        html += `
            <div class="results-section">
                <h4>2P订单</h4>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>订单号</th>
                            <th>数量</th>
                            <th>备注</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${results.twoPOrders.map(order => `
                            <tr>
                                <td>${order['Rif.']}</td>
                                <td>${order['Pack Qty']}</td>
                                <td>${order['Nota (privata)'] || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    // 显示未分配订单
    if (results.unassigned.length > 0) {
        html += `
            <div class="results-section">
                <h4>未分配订单</h4>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>订单号</th>
                            <th>数量</th>
                            <th>备注</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${results.unassigned.map(order => `
                            <tr>
                                <td>${order['Rif.']}</td>
                                <td>${order['Pack Qty']}</td>
                                <td>${order['Nota (privata)'] || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    resultsDiv.innerHTML = html;
}

function exportToExcel() {
    if (!distributionResults) {
        alert('没有可导出的数据！');
        return;
    }

    // 创建工作簿
    const wb = XLSX.utils.book_new();
    
    // 处理员工任务
    Object.entries(distributionResults.employeeTasks).forEach(([name, tasks]) => {
        if (tasks.length > 0) {
            const data = tasks.map(task => ({
                '订单号': task['Rif.'],
                '数量': task['Pack Qty'],
                '类别': task['Tag/categoria'],
                '备注': task['Nota (privata)'] || ''
            }));
            const ws = XLSX.utils.json_to_sheet(data);
            XLSX.utils.book_append_sheet(wb, ws, name);
        }
    });

    // 处理2P订单
    if (distributionResults.twoPOrders.length > 0) {
        const data = distributionResults.twoPOrders.map(order => ({
            '订单号': order['Rif.'],
            '数量': order['Pack Qty'],
            '备注': order['Nota (privata)'] || ''
        }));
        const ws = XLSX.utils.json_to_sheet(data);
        XLSX.utils.book_append_sheet(wb, ws, '2P订单');
    }

    // 处理未分配订单
    if (distributionResults.unassigned.length > 0) {
        const data = distributionResults.unassigned.map(order => ({
            '订单号': order['Rif.'],
            '数量': order['Pack Qty'],
            '备注': order['Nota (privata)'] || ''
        }));
        const ws = XLSX.utils.json_to_sheet(data);
        XLSX.utils.book_append_sheet(wb, ws, '未分配订单');
    }

    // 生成并下载文件
    const date = new Date().toISOString().split('T')[0];
    XLSX.writeFile(wb, `任务分配结果_${date}.xlsx`);
}

function exportToPDF() {
    if (!distributionResults) {
        alert('没有可导出的数据！');
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    let yPos = 20;

    // 添加标题
    doc.setFontSize(16);
    doc.text('任务分配结果', 14, yPos);
    yPos += 10;

    // 添加员工任务
    doc.setFontSize(12);
    Object.entries(distributionResults.employeeTasks).forEach(([name, tasks]) => {
        if (tasks.length === 0) return;

        if (yPos > 250) {
            doc.addPage();
            yPos = 20;
        }

        doc.text(`${name} 的任务:`, 14, yPos);
        yPos += 5;

        const tableData = tasks.map(task => [
            task['Rif.'],
            task['Pack Qty'],
            task['Tag/categoria'],
            task['Nota (privata)'] || ''
        ]);

        doc.autoTable({
            startY: yPos,
            head: [['订单号', '数量', '类别', '备注']],
            body: tableData,
            margin: { left: 14 }
        });

        yPos = doc.lastAutoTable.finalY + 10;
    });

    // 生成并下载文件
    const date = new Date().toISOString().split('T')[0];
    doc.save(`任务分配结果_${date}.pdf`);
}

function saveEmployee(event) {
    event.preventDefault();
    const name = document.getElementById('name').value;
    const employee = {
        name: name,
        maxPicking: parseInt(document.getElementById('maxPicking').value),
        canHandleLargeOrders: document.getElementById('largeOrders').checked,
        hasVhSkill: document.getElementById('vhSkill').checked,
        hasEsteroSkill: document.getElementById('esteroSkill').checked,
        isPresent: document.getElementById('isPresent').checked
    };
    
    employees[name] = employee;
    localStorage.setItem('employees', JSON.stringify(employees));
    refreshEmployeeList();
    resetForm();
}

function editEmployee(name) {
    selectedEmployee = name;
    const emp = employees[name];
    document.getElementById('name').value = emp.name;
    document.getElementById('name').disabled = true;
    document.getElementById('maxPicking').value = emp.maxPicking;
    document.getElementById('largeOrders').checked = emp.canHandleLargeOrders;
    document.getElementById('vhSkill').checked = emp.hasVhSkill;
    document.getElementById('esteroSkill').checked = emp.hasEsteroSkill;
    document.getElementById('isPresent').checked = emp.isPresent;
}

function deleteEmployee(name) {
    if (confirm(`确定要删除员工 ${name} 吗？`)) {
        delete employees[name];
        localStorage.setItem('employees', JSON.stringify(employees));
        refreshEmployeeList();
    }
}

function resetForm() {
    document.getElementById('employeeForm').reset();
    document.getElementById('name').disabled = false;
    selectedEmployee = null;
}

// 初始化
refreshEmployeeList(); 