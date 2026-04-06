# 测试脚本说明

仓库根目录保留了几个独立测试脚本，主要用于本地调试摄像头、人脸检测、活体检测和人脸比对能力。

## 文件用途

- `test_detection.py`
  用于测试摄像头画面中的人脸检测和计数。

- `test_liveness.py`
  用于测试活体检测流程，按键抓拍后输出活体分数。

- `test_recognition.py`
  用于测试人脸特征提取与相似度比对。

- `test_t.py`
  调试版活体检测脚本，输出更详细的环境信息、摄像头信息、边界框信息和异常堆栈，适合定位本地模型或 OpenCV 环境问题。

## 运行前提

- 已安装 `backend/requirements.txt` 中的后端依赖
- 本机可正常访问摄像头
- `backend/resources/` 下模型文件存在

## 运行方式

在项目根目录执行，例如：

```bash
python test_detection.py
python test_liveness.py
python test_recognition.py
python test_t.py
```

## 说明

这些脚本偏向研发调试用途，不属于前后端正式业务入口，因此保留在根目录而不是集成到应用页面中。
