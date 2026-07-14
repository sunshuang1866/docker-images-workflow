# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 镜像站下载超时
- 新模式症状关键词: ReadTimeoutError, Read timed out, mirrors.aliyun.com, pip install, HTTPSConnectionPool

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

关键上下文：超时发生在下载 `nvidia_cudnn_cu13==9.20.0.48`（366.2 MB wheel）时，已下载 353.4/366.2 MB 后连接中断：
```
#12 227.3   Downloading ... nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl (366.2 MB)
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28`（RUN 指令中的 `pip install -r backend/requirements.txt` 步骤）
- 失败原因: CI 构建环境通过 `mirrors.aliyun.com` 镜像站下载 366 MB 的 `nvidia_cudnn_cu13` wheel 包时，TCP 读取超时（约 30 秒后连接中断）。npm 构建阶段（npm i / npm run build）已成功完成，失败仅发生在 pip 安装大文件阶段。

### 与 PR 变更的关联
PR 新增了 `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile`，该 Dockerfile 在 pip install 步骤中指定了 `-i https://mirrors.aliyun.com/pypi/simple/` 镜像源。由于 `nvidia_cudnn_cu13` 包体积巨大（366 MB），在 CI 网络条件下从该镜像站下载时发生读超时。此失败与代码逻辑无直接关联，属于网络基础设施问题，但可能具有可重复性（同一大包每次都可能超时）。

## 修复方向

### 方向 1（置信度: 低）
在 Dockerfile 的 pip install 命令中添加 `--default-timeout=300` 参数，将 pip 默认下载超时从 15 秒延长到 300 秒，给大文件下载留足时间。如果超时仍发生，可进一步加大或改用 `--retries` 参数增加重试次数。

### 方向 2（置信度: 中）
将 nvidia 相关依赖（`nvidia_cudnn_cu13` 等 CUDA toolkit 包）的下载源从 `mirrors.aliyun.com` 切换为 `https://pypi.tuna.tsinghua.edu.cn/simple/`（清华 PyPI 镜像），或直接使用 `https://pypi.org/simple/` 官方源。aliyun 镜像对超大文件的 CDN 回源或带宽可能不稳定。

### 方向 3（置信度: 低）
将 `nvidia_cudnn_cu13` 等超大 CUDA 依赖从 wheel 安装改为使用系统包管理器（dnf）安装 NVIDIA CUDA 仓库中的 RPM 包，避免 pip 下载大文件。

## 需要进一步确认的点
- 是否为瞬态网络故障：触发 CI 重跑后是否能成功通过同一个下载步骤。
- 同仓库中已有 `24.03-lts-sp1` 版本的 open-webui Dockerfile 是否也使用 `mirrors.aliyun.com`，以及其 CI 构建是否成功——若成功，则说明本次失败更可能是瞬态网络问题。
- `nvidia_cudnn_cu13` 在 `mirrors.aliyun.com` 上是否已完整同步（对比 pypi.org 的 MD5/SHA256），排除镜像站缓存不完整的问题。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用。本次失败为网络超时，不涉及正则 patch 外部文件。）
