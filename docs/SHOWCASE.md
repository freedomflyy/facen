# GitHub 展示配置建议

这份文档用于把仓库页面整理得更适合公开展示和作品集使用。

## About 文案

### 中文版

基于 Vue 3 和 FastAPI 的人脸识别课堂签到系统，支持活体检测与地理围栏签到。

### 英文版

Face recognition classroom attendance system built with Vue 3 and FastAPI, featuring liveness detection and geofence-based check-in.

## Topics 建议

建议在 GitHub 仓库 `About` 区域添加这些 Topics：

- `vue3`
- `vite`
- `fastapi`
- `face-recognition`
- `attendance-system`
- `computer-vision`
- `opencv`
- `onnxruntime`
- `sqlmodel`
- `element-plus`

## 置顶展示建议

如果你准备把这个仓库放到 GitHub 个人主页置顶，建议配合以下内容：

- 一张登录页截图
- 一张教师端签到会话截图
- 一张管理员后台截图
- README 里保留技术栈、功能点和快速启动

## 截图规范

- 不出现真实姓名
- 不出现真实学号
- 不出现真实人脸原图
- 不出现本地磁盘路径、IP、内网地址或学校具体信息
- 演示账号统一使用 README 中的示例账号

## 发布前自检清单

- `git status` 为空
- `backend/database.db` 未提交
- `backend/uploads/` 下真实图片未提交
- `.idea/` 和 `frontend/node_modules/` 未提交
- README 可正常显示
- 仓库首页简介已填写
- 仓库 Topics 已填写
- 仓库可见性符合你的预期
