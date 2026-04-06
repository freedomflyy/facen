# Facen

基于人脸识别的课堂签到系统，包含学生签到、教师发起签到、管理员管理、活体检测与地理围栏等能力。

这个仓库已按公开展示场景做过整理：

- 不提交本地数据库、上传的人脸照片、IDE 配置、`node_modules`、实习报告/PPT 等非源码材料
- JWT 密钥和数据库路径支持通过环境变量覆盖
- 初始化演示数据改为通用示例账号，避免带出具体个人或校内信息

## 功能概览

- 学生端：注册、拍照录入、签到码校验、活体检测、人脸比对、签到历史
- 教师端：创建签到、按班级发布、查看到课情况、手动补签
- 管理端：教师/学生/班级管理、教师班级分配、签到记录查看与修正
- 校验能力：地理围栏、签到时效控制、人脸特征比对

## 技术栈

- 前端：Vue 3、Vite、Element Plus、Axios、face-api.js
- 后端：FastAPI、SQLModel、SQLite、JWT
- 视觉能力：InsightFace、OpenCV、ONNX Runtime、MiniFASNet

## 项目结构

```text
.
├─ backend/                 # FastAPI 后端
│  ├─ main.py               # 主要接口
│  ├─ models.py             # 数据模型
│  ├─ auth.py               # JWT 与密码处理
│  ├─ database.py           # 数据库连接
│  ├─ init_data.py          # 演示数据初始化脚本
│  └─ resources/            # 人脸 / 活体模型文件
├─ frontend/                # Vue 前端
│  ├─ src/views/            # 学生/教师/管理员页面
│  ├─ src/components/       # 活体检测组件等
│  └─ public/models/        # 前端人脸检测模型
└─ README.md
```

## 快速开始

### 1. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python init_data.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认前端开发服务会把 `/api` 代理到 `http://127.0.0.1:8000`。

## 演示账号

初始化脚本会生成以下演示账号：

- 管理员：`root / root`
- 教师：`teacher_a / 123456`
- 教师：`teacher_b / 123456`
- 学生：`student_01 ~ student_04 / 123456`

这些账号仅用于本地演示，公开部署前应全部更换。

## 环境变量

`backend/.env.example`

```env
FACEN_SECRET_KEY=replace-with-a-random-secret
FACEN_JWT_ALGORITHM=HS256
FACEN_ACCESS_TOKEN_EXPIRE_MINUTES=30
FACEN_DB_PATH=database.db
```

## 发布到 GitHub 的建议

- 首次提交前执行 `git status`，确认没有把 `backend/database.db`、`backend/uploads/`、`.idea/`、`frontend/node_modules/` 等文件带上
- 如果你已经在别处初始化过 Git 历史，先确认历史里没有提交过真实人脸照片或数据库
- 如果后续想做展示图，建议重新截取不含真实姓名、学号、人脸原图的页面截图再上传

## 已知说明

- 仓库中保留了模型文件，方便本地复现；如果你想进一步减小仓库体积，可以改为从发行包或网盘单独提供
- 当前后端代码里有少量历史中文注释乱码，不影响运行，但如果要进一步整理展示，可以后续统一修复
