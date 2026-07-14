# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: timeout
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: pip镜像下载超时
- 新模式症状关键词: Read timed out, HTTPSConnectionPool, mirrors.aliyun.com, nvidia_cudnn, pip install

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
#12 257.5 TimeoutError: The read operation timed out
#12 257.5
#12 257.5 During handling of the above exception, another exception occurred:
#12 257.5 ...
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 457, in _error_catcher
#12 257.5     raise ReadTimeoutError(self._pool, None, "Read timed out.")
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

下载中断时的进度上下文：
```
#12 227.3   Downloading nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl (366.2 MB)
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28`（`RUN pip install -r backend/requirements.txt ...` 步骤）
- 失败原因: pip 从 `mirrors.aliyun.com` 下载 `nvidia_cudnn_cu13`（366 MB）至 96% 时 HTTP 读取超时，整个 RUN 命令失败（exit code: 2）。该 RUN 命令将 npm 构建、npm 安装和大量 pip 包安装串行放在一个 Docker 层中，一旦任何一个子步骤因网络波动失败，整层都需重建。

### 与 PR 变更的关联
- PR 新增了一个全新的 Dockerfile，该 Dockerfile 在单条 RUN 指令中串联了 `npm i`、`npm run build`、`pip install pydantic`、`pip install -r backend/requirements.txt`（含 torch、nvidia-cudnn 等巨型包）、`pip install fastapi_sso transformers accelerate` 共 5 个子步骤。
- 失败与代码逻辑无关，属于网络基础设施问题。但单层串行设计放大了网络波动的影响——npm 阶段已成功完成（日志中出现 `.svelte-kit` 构建产物），但后续 pip 下载大文件时遭遇瞬断导致整层失败，无法复用前序成功步骤的缓存。
- 不存在 `meta.yml` 架构约束缺失问题——Dockerfile 同时支持 amd64 和 arm64，且 CI 日志显示本次构建在 x86_64 runner 上运行。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 中的大单体 RUN 指令拆分为多个独立的 RUN 步骤（如分别执行前端构建、pip 安装基础依赖、pip 安装重型 ML 依赖），利用 Docker 层缓存机制使网络重试不需要重复已成功的子步骤。同时为重型下载添加 pip `--retries` 参数增加重试次数，或在失败时通过 bash 循环重试。

### 方向 2（置信度: 中）
将 pip 镜像源从 `mirrors.aliyun.com` 替换为其他在国内 CI 环境中更稳定的镜像（如 `mirrors.huaweicloud.com`、`pypi.tuna.tsinghua.edu.cn`），规避阿里云镜像站在特定时段对大文件传输的连接稳定问题。

## 需要进一步确认的点
1. 该镜像站超时是个别时段偶发还是持续性问题——需要重试一次 CI 构建确认是否可复现。
2. 同仓库中其他使用 `mirrors.aliyun.com` 的 Dockerfile（如 `AI/open-webui/0.1.108/24.03-lts-sp1/Dockerfile`）是否能稳定构建，以判断是镜像站稳定性问题还是特定时段网络波动。
3. open-webui 的 `backend/requirements.txt` 依赖树是否包含可裁剪的重型依赖（如 `nvidia-cudnn-cu13` 366 MB），上游是否有更轻量的依赖方案。
