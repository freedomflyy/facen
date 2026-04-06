# Facen

基于人脸识别的课堂签到系统，包含学生签到、教师发布签到、管理员管理、活体检测和地理围栏校验等能力。

这个仓库已经按公开展示场景做过整理：

- 不提交本地数据库、上传的人脸照片、IDE 配置、`node_modules`、实习报告和演示材料
- JWT 密钥和数据库路径支持通过环境变量覆盖
- 初始化演示数据已替换为通用示例账号，避免暴露具体个人或校内信息

## 项目功能

- 学生端：注册、拍照录入、签到码校验、活体检测、人脸比对、签到历史查询
- 教师端：创建签到、按班级发布、查看签到情况、手动补签
- 管理端：教师管理、学生管理、班级管理、班级分配、签到记录修正
- 校验能力：签到时效控制、地理围栏校验、人脸特征比对

## 技术栈

- 前端：Vue 3、Vite、Element Plus、Axios、face-api.js
- 后端：FastAPI、SQLModel、SQLite、JWT
- 视觉能力：InsightFace、OpenCV、ONNX Runtime、MiniFASNet

## 项目结构

```text
.
- backend/
  - main.py
  - models.py
  - auth.py
  - database.py
  - init_data.py
  - resources/
- frontend/
  - src/views/
  - src/components/
  - public/models/
- README.md
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

初始化脚本会生成以下本地演示账号：

- 管理员：`root / root`
- 教师：`teacher_a / 123456`
- 教师：`teacher_b / 123456`
- 学生：`student_01` 到 `student_04`，密码均为 `123456`

这些账号仅用于本地演示，公开部署前应全部更换。

## 环境变量

参考 `backend/.env.example`：

```env
FACEN_SECRET_KEY=replace-with-a-random-secret
FACEN_JWT_ALGORITHM=HS256
FACEN_ACCESS_TOKEN_EXPIRE_MINUTES=30
FACEN_DB_PATH=database.db
```

## GitHub 展示说明

- 不要提交真实人脸照片、本地数据库文件，或包含真实姓名和学号的截图
- 当前仓库保留了模型文件，方便本地直接复现
- 后端代码里仍有少量历史中文注释乱码，但不影响运行

## 补充文档

- 测试脚本说明：`docs/TESTING.md`
- 仓库展示配置建议：`docs/SHOWCASE.md`

## 仓库简介建议

基于 Vue 3 和 FastAPI 的人脸识别课堂签到系统，支持活体检测与地理围栏签到。

## 截图建议

- 登录页：只展示通用演示账号
- 教师端：展示一个示例签到会话和签到统计
- 学生端：展示签到流程，但避免出现真实人脸原图
- 管理端：展示匿名化后的班级、学生和教师数据
