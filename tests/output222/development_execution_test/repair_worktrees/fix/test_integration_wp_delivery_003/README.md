# 项目代码

## 环境准备
```bash
pip install -r requirements.txt
```

## 启动服务
```bash
uvicorn app.main:app --reload --port 8000
# 健康检查
curl http://localhost:8000/health
```

## API 文档
- 访问 FastAPI Swagger: http://localhost:8000/docs
- OpenAPI 规范文件: openapi.json

## 运行测试
```bash
pytest -q
```

## CI (GitHub Actions)
- 工作流文件: .github/workflows/ci.yml
- 默认执行：安装依赖并运行 pytest

## 前端界面
- 访问界面: http://localhost:8000/ui/
- 静态资源目录: frontend
