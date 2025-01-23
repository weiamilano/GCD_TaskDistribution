#!/bin/bash

# 启动后端
cd backend
python app.py &

# 启动前端
cd ../frontend
npm start 