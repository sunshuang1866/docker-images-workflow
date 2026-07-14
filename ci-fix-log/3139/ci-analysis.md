# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 阿里云镜像超时
- 新模式症状关键词: Read timed out, mirrors.aliyun.com, pip, HTTPSConnectionPool, TimeoutError

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry ... && pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ ..." did not complete successfully: exit code: 2
```

关键上下文：超时发生在下载 `nvidia-cudnn-cu13-9.20.0.48`（366.2 MB 的 .whl）时，已下载 353.4/366.2 MB（约 96.5%）后连接中断。

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28`（`RUN npm ... && pip install -r backend/requirements.txt ...`）
- 失败原因: CI 构建环境中，pip 从 `mirrors.aliyun.com` 下载大型依赖包 `nvidia-cudnn-cu13`（366 MB）时发生网络读超时，导致 `pip install` 命令以 exit code 2 失败。

### 与 PR 变更的关联
**与 PR 改动无关**。该 PR 仅新增了一个标准的 Dockerfile，其中 `pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/` 是合法的依赖安装命令。`npm i` 和 `npm run build` 均已完成（日志中有 svelte-kit 构建产物输出），失败纯粹是阿里云镜像站的网络连接在下载大文件时不稳定导致的临时性基础设施问题。log 末尾显示 `Finished: FAILURE`，且 npm 构建阶段已完成，排除 BuildKit BUILDARCH 变量冲突（模式09）。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施网络问题，非代码缺陷。可尝试以下任一方案提升构建稳定性：
- 为 `pip install` 增加 `--default-timeout=300` 或更高值，容忍大文件慢速下载
- 将 `mirrors.aliyun.com` 替换为其他更稳定的镜像源（如 `mirrors.tuna.tsinghua.edu.cn` 或 PyPI 官方源）
- 将 `pip install -r backend/requirements.txt` 拆分为独立 RUN 层（与 npm 构建分离），便于 Docker Layer Cache 和重试机制
- 在 RUN 中加入 `pip install` 的重试逻辑（如 `for i in 1 2 3; do pip install ... && break || sleep 30; done`）

### 方向 2（置信度: 低）
`nvidia-cudnn-cu13` 是一个 CUDA 相关的 GPU 包（366 MB），该镜像的目标应是 CPU 推理场景。确认 `backend/requirements.txt` 是否因上游 open-webui 的版本依赖链（通过 `sentence_transformers` → `torch` → `nvidia-cudnn-cu13`）引入了不必要的 CUDA 依赖。如果可以确认该镜像不需要 CUDA 支持，可在 `pip install` 前设置 `PIP_EXTRA_INDEX_URL` 使用 CPU-only 的 PyTorch 索引。

## 需要进一步确认的点
- 重新触发 CI 构建是否复现（大概率不复现，因为这是偶发性网络超时）
- 如果多次复现，需检查 CI runner 到 `mirrors.aliyun.com` 的网络链路质量
- 确认 `open-webui` v0.1.108 的 `backend/requirements.txt` 实际内容，以评估 `nvidia-cudnn-cu13` 依赖是否可规避
- 对照同软件其他版本（如 `22.03-lts-sp4`、`24.03-lts-sp1`）的 Dockerfile，确认它们是否使用了相同镜像源以及是否曾遇到类似超时

## 修复验证要求
- 若改用其他镜像源：需在 CI 环境中验证该镜像源对 `nvidia-cudnn-cu13`（366 MB）包下载的稳定性和可达性
- 若增加超时参数：需确保 CI runner 的总构建超时时间足够容纳大文件下载
- 若尝试方向 2（CPU-only PyTorch）：需验证 `sentence_transformers` 等依赖在 CPU-only PyTorch 下功能正常
