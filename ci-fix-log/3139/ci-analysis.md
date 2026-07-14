# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: pip镜像站下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, pip install, nvidia_cudnn_cu13

## 根因分析

### 直接错误
```
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
#12 257.5   ...
#12 257.5 TimeoutError: The read operation timed out
#12 257.5 ...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry ... && pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ && pip install fastapi_sso ... did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（pip install 阶段）
- 失败原因: pip 从 `mirrors.aliyun.com` 下载 `nvidia_cudnn_cu13-9.20.0.48`（366 MB）时发生读取超时，已传输 353.4 MB（96.5%）时连接中断。`npm i` 和 `npm run build` 均已完成成功，仅 pip 下载阶段失败。

### 与 PR 变更的关联
PR 新增了 AI/open-webui 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，该 Dockerfile 将 `npm i`、`npm run build` 和 `pip install -r backend/requirements.txt` 合并为单个 RUN 指令（Dockerfile:28-35），且所有 pip 安装均指向 `mirrors.aliyun.com`。失败发生在 `pip install -r backend/requirements.txt` 尝试下载 `nvidia_cudnn_cu13` 依赖时（该依赖由 `torch` → `sentence_transformers` 链条引入），属于远端镜像站网络超时，**非代码逻辑错误**。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该超时发生于大文件（366 MB）下载至 96.5% 时，极有可能为阿里云镜像站临时网络波动所致。在没有修改任何代码的情况下，重新触发 CI 构建大概率可以通过。（若多次重试均在同一包、同一位置超时，则需考虑方向 2。）

### 方向 2（置信度: 低）
**增加 pip 下载超时 + 拆分 RUN 指令**。
- 在 pip install 命令中增加 `--default-timeout=300`（或更大值），延长每次 HTTP 读取的超时阈值。
- 将 `npm i && npm run build` 与 `pip install` 拆分为两个独立的 RUN 指令，利用 Docker 层缓存：npm 阶段成功后下次重试可直接复用缓存，避免每次失败都从头执行 npm。

## 需要进一步确认的点
1. **是否为可复现问题**：重试构建是否仍然在同一包（`nvidia_cudnn_cu13`）超时？若多次重试均在同一文件同一进度附近超时，可能是阿里云镜像站对该特定大文件存在服务端侧限制或 CDN 节点问题，需考虑换用其他镜像源（如 `pypi.tuna.tsinghua.edu.cn`）或直接从 PyPI 官方源下载该包。
2. **SP4 基础镜像的网络环境**：`openEuler 24.03-LTS-SP4` 基础镜像中的 Python 3.11 / pip 默认超时配置是否与其他版本（SP1、SP3）一致，是否存在更短默认超时的可能性。
3. **Dockerfile 中 tab 字符**：第 34-35 行 `\ttransformers` 和 `\taccelerate` 使用了 tab 而非空格作为续行前导，虽未导致本次失败，建议统一为空格以避免潜在 shell 解析问题。

## 修复验证要求
若修复方向涉及修改 pip 命令行参数或更换镜像源，code-fixer 必须在修改后验证以下几点：
- 从 `mirrors.aliyun.com`（或更换后的镜像源）确实能完整下载 `nvidia_cudnn_cu13-9.20.0.48` 这个 366 MB 的 wheel 包。
- 新超时值（如 `--default-timeout=300`）在 CI 环境中生效，且不会无限挂起。
