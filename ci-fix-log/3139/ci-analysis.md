# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, Read timed out, nvidia-cudnn-cu13, pip install

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

下载进度停留于 353.4/366.2 MB：
```
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28`（`pip install -r backend/requirements.txt` 步骤）
- 失败原因: `pip install` 从 `mirrors.aliyun.com` 下载 PyTorch 的依赖包 `nvidia-cudnn-cu13`（366.2 MB）时，在下载到 353.4 MB 处发生 TCP 读超时（`Read timed out`），导致整个 `RUN` 步骤失败。

### 与 PR 变更的关联
PR 新增的 Dockerfile 在 `pip install` 步骤中指定了 `-i https://mirrors.aliyun.com/pypi/simple/` 作为 pip 镜像源。`backend/requirements.txt` 中的 `sentence_transformers` 间接依赖 `torch`，后者又依赖 `nvidia-cudnn-cu13`（366 MB）。CI 构建环境中与该 Aliyun 镜像之间的网络连接在传输大文件时不稳定，导致超时。

该失败与 PR 的代码逻辑无关，属于网络基础设施问题。npm 安装与构建阶段均已成功完成，超时仅发生在 pip 下载大型 CUDA 依赖包时。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。Aliyun 镜像站的连接超时很可能是暂时性网络波动。如果同一 Dockerfile 在其他时间段或另一次重试中构建成功，说明问题确实为瞬时网络故障，无需修改代码。

### 方向 2（置信度: 中）
**为 pip 增加超时容忍度或下载重试**。在 Dockerfile 的 `pip install` 命令中添加 `--timeout 300`（默认 15 秒可能不足以下载 366 MB 文件），或使用 `pip install --retries 5` 增加重试次数，降低大文件下载超时的概率。

### 方向 3（置信度: 低）
**切换 pip 镜像源**。将 `mirrors.aliyun.com` 替换为从 CI 构建环境连接更稳定的镜像站（如 `mirrors.tuna.tsinghua.edu.cn` 或 `pypi.org`）。需注意：切换到其他镜像站也可能遇到类似超时问题，且与同应用已有 SP1 版本的 Dockerfile 使用的镜像源不一致。

## 需要进一步确认的点
1. 同一 CI 环境下，`AI/open-webui/0.1.108/24.03-lts-sp1/Dockerfile`（已存在的 SP1 版本）是否也使用 `mirrors.aliyun.com` 并能正常构建？如果 SP1 版本近期构建也超时，说明镜像站本身存在问题。
2. `backend/requirements.txt` 中 `sentence_transformers` 的依赖链是否必须包含 `nvidia-cudnn-cu13`？如果 open-webui 容器仅需 CPU 推理，可考虑安装 CPU-only 版本的 PyTorch（`--index-url https://download.pytorch.org/whl/cpu`），避免下载 366 MB 的 CUDA 工具包。

## 修复验证要求
若采用方向 2 或方向 3，code-fixer 必须：
1. 确认修改后的 Dockerfile 能在 CI 环境中完成 `pip install` 步骤（尤其是 `nvidia-cudnn-cu13` 或其他大型依赖的下载）。
2. 验证最终镜像能正常启动 open-webui 服务（`/root/open-webui/backend/start.sh` 无报错）。
