# 修复摘要

## 修复的问题
将 Dockerfile 中第28-35行的单体 RUN 指令（串联 npm 构建 + pip 安装 5 个子步骤）拆分为 4 个独立 RUN，并为重型 pip 依赖安装添加 `--retries 5`，利用 Docker 层缓存使网络波动导致的重试无需重建已成功的子步骤。

## 修改的文件
- `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile`: 拆分单条 RUN 为 4 条独立 RUN，并为 `backend/requirements.txt` 和 `fastapi_sso/transformers/accelerate` 的安装添加 `--retries 5`

## 修复逻辑
分析报告指出根因是：从 `mirrors.aliyun.com` 下载 `nvidia_cudnn_cu13`（366 MB）至 96% 时 HTTP 读取超时，导致整条 RUN 失败。由于 npm 构建（约 228s）和 pip 安装串行在同一层中，失败后必须重建所有前端产物。

修复方案：
1. 将 npm 构建独立为单条 RUN（第28-30行），成功后可被 Docker 缓存复用
2. 将 `pip install pydantic` 独立为单条 RUN（第32行），轻量级依赖快速缓存
3. 将 `pip install -r backend/requirements.txt` 独立为单条 RUN（第34行），添加 `--retries 5` 提高大文件下载成功率
4. 将 `pip install fastapi_sso transformers accelerate` 独立为单条 RUN（第36-39行），添加 `--retries 5`

这样即使 nvidia-cudnn 下载超时，npm 构建层和 pydantic 层仍可复用缓存，无需从头重建。

## 潜在风险
无。拆分后的 RUN 层与原来单层 RUN 的行为完全等价，只是增加了 Docker 镜像层数（对最终镜像大小和运行行为无影响）。其他文件（README.md、image-info.yml、meta.yml）无需修改。