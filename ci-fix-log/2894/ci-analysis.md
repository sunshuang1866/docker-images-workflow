# CI 失败分析报告

## 基本信息
- PR: #2894 — chore(bisheng-jdk): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: eulerpublisher缺distroless模块
- 新模式症状关键词: ModuleNotFoundError, eulerpublisher.container.distroless, cli.py

## 根因分析

### 直接错误
```
2026-07-09 20:31:20,936 - DEBUG - Shutting down executor...
Traceback (most recent call last):
  File "/usr/local/bin/eulerpublisher", line 6, in <module>
  File "/usr/local/lib/python3.9/site-packages/eulerpublisher/eulerpublisher.py", line 4, in <module>
  File "/usr/local/lib/python3.9/site-packages/eulerpublisher/container/cli.py", line 5, in <module>
ModuleNotFoundError: No module named 'eulerpublisher.container.distroless'
```

### 根因定位
- 失败位置: /usr/local/lib/python3.9/site-packages/eulerpublisher/container/cli.py:5
- 失败原因: CI 运行器上的 eulerpublisher 工具缺少 `distroless` 子模块，导致 shutdown 阶段崩溃

### 与 PR 变更的关联
PR 变更（新增 Dockerfile、更新 README.md/image-info.yml/meta.yml）**不是**此次失败的原因。Docker 镜像构建、Java 版本验证、镜像导出和推送均成功完成。失败发生在 CI 的后处理工具 eulerpublisher 在 shutdown 时因缺少 `eulerpublisher.container.distroless` Python 模块而崩溃，这是一个纯粹的 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI 运行器上更新 eulerpublisher Python 包，确保包含 `distroless` 子模块。可通过 `pip install --upgrade eulerpublisher` 或从源码重新安装完整版本来修复。

## 需要进一步确认的点
- 确认 CI 运行器上 eulerpublisher 包的安装源和版本
- 确认 `distroless` 模块是否为 eulerpublisher 新版本中新增的模块，旧版本可能不包含此模块

## 修复验证要求
（不涉及正则 patch 外部源文件）
