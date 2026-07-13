# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 阿里云镜像大文件下载超时
- 新模式症状关键词: Read timed out, mirrors.aliyun.com, pip, nvidia-cudnn-cu13, HTTPSConnectionPool

## 根因分析

### 直接错误
```
#12 227.3   Downloading .../nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl (366.2 MB)
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
#12 257.5   ...
#12 257.5   File "/usr/lib64/python3.11/ssl.py", line 1167, in read
#12 257.5     return self._sslobj.read(len, buffer)
#12 257.5 TimeoutError: The read operation timed out
#12 257.5 ...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry ... && pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（合并 RUN 命令中的 `pip install -r backend/requirements.txt` 步骤）
- 失败原因: pip 从 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13` 包（366.2 MB）时，在 353.4 MB（96.5%）处发生 TCP 读超时，网络连接中断。npm install 和 npm build 在此之前均已完成，Python 依赖下载已成功下载了大量其他包（spacy 32.3 MB、ctranslate2 39.4 MB 等），仅该大文件在最后阶段超时。

### 与 PR 变更的关联
**与 PR 改动无直接关联。** 这是 CI 构建环境中 `mirrors.aliyun.com` 阿里云 PyPI 镜像站的网络连接不稳定导致的大文件下载超时，属于基础设施问题。PR 仅新增了一个标准 Dockerfile，其 pip 安装步骤本身没有问题。但是，Dockerfile 将 `npm i && npm run build` 和多个 `pip install` 合并到单个 `RUN` 指令中，导致构建不具备断点续传能力——任何一步失败都需要重跑整个步骤（包括已成功的 npm 构建部分）。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。由于这是网络超时（infra-error），相同的 Dockerfile 在镜像站连接稳定时大概率能直接构建成功。无需修改任何代码，直接触发 CI 重新构建即可。

### 方向 2（置信度: 中）
**拆分 RUN 指令以支持构建缓存**。将当前合并为一个 `RUN` 的 npm 构建与 pip 安装拆分为独立的 `RUN` 指令，这样：
- npm 安装和构建结果可被 Docker 层缓存复用
- pip 安装超时重试时无需重新执行 npm 构建
- 同时也可以考虑换用其他 PyPI 镜像源（如清华镜像站 `pypi.tuna.tsinghua.edu.cn`）作为备选

### 方向 3（置信度: 低）
**为大文件依赖添加 pip 重试机制**。在 pip install 命令中增加 `--retries` 参数或使用 `pip install --timeout` 调整超时阈值。但这只能缓解而不能根除网络不稳定问题。

## 需要进一步确认的点
1. CI 构建环境到 `mirrors.aliyun.com` 的网络质量 —— 本次超时发生在 353.4/366.2 MB 处，下载速率 23 MB/s 正常，属于连接不稳定而非带宽不足。
2. 是否该阿里云镜像站对该特定大文件 (`nvidia-cudnn-cu13`) 的 CDN 节点存在问题 —— 因为其他大文件（llvmlite 59.9 MB、spacy 32.3 MB、scipy 35.3 MB 等）均成功下载。

## 修复验证要求
（infra-error，无代码修复需要验证；若采用方向 2 拆分 RUN 指令，需要在 CI 环境中重新构建验证。）
