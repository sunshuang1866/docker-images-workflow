# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: "镜像站下载超时"
- 新模式症状关键词: "ReadTimeoutError, HTTPSConnectionPool, Read timed out, mirrors.aliyun.com, pip install, nvidia_cudnn_cu13"

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry https://registry.npmmirror.com/ &&     npm i &&     npm run build &&     pip install pydantic -i https://mirrors.aliyun.com/pypi/simple/ &&     pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ &&     pip install fastapi_sso \ttransformers \taccelerate -i https://mirrors.aliyun.com/pypi/simple/" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（`pip install -r backend/requirements.txt` 步骤）
- 失败原因: pip 从 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13`（366.2 MB）时遭遇 TCP 读超时，下载进度到达 353.4/366.2 MB（96.5%）时连接中断，`urllib3` 抛出 `ReadTimeoutError`。npm 构建阶段（`npm i && npm run build`）已成功完成，日志中可见 `.svelte-kit/output/` 产物输出，说明失败仅发生在 pip 下载大型依赖包阶段。

### 与 PR 变更的关联
PR 新增了 `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile`，该 Dockerfile 从零开始创建，其中第 28-35 行使用 `mirrors.aliyun.com` 作为 pip 安装源。`backend/requirements.txt` 间接依赖 PyTorch，后者依赖 `nvidia-cudnn-cu13`（366 MB 超大型 wheel）。阿里云镜像站在传输该大文件时发生网络中断（非连接超时，而是传输中途读超时），导致 `docker build` 失败。

**与 PR 改动的关系**: 直接相关——PR 新增的 Dockerfile 引入了对阿里云镜像站的 pip 依赖，该镜像站在下载超大包时存在稳定性问题。但失败本质是网络/基础设施问题，非代码逻辑错误。

## 修复方向

### 方向 1（置信度: 中）
重试构建。该错误为网络瞬断（TCP 读超时），下载已进行到 96.5%，很可能是临时的 CDN 节点波动，重新触发 CI 大概率可以成功。

### 方向 2（置信度: 中）
引入重试机制或拆分安装步骤。将 Dockerfile 中第 28-35 行的单条 `RUN` 拆分为多条：先执行 `npm i && npm run build`，再单独 `pip install`，并在 pip 命令中添加 `--retries 5 --timeout 300` 参数提高网络容错能力。`nvidia-cudnn-cu13` 这类超大包（366 MB）在网络不稳定时容易超时。

### 方向 3（置信度: 低）
为超大依赖包换用其他镜像源或预下载。如果 `mirrors.aliyun.com` 对 `nvidia-cudnn-cu13` 持续不稳定，可考虑对 PyTorch 相关依赖使用官方 PyPI 或 `mirrors.tuna.tsinghua.edu.cn` 作为备选源。

## 需要进一步确认的点
1. 重试 CI 后是否仍然失败——如果多次重试均在同一位置（`nvidia-cudnn-cu13` 96.5% 处）超时，说明阿里云镜像站对该包的缓存/传输存在系统性问题，需换源。
2. 是否存在 aarch64 架构的独立构建日志——当前日志仅为 x86_64 构建，若 aarch64 也失败且报错相同，则问题面更广。
3. Dockerfile 中第 33-35 行 `pip install fastapi_sso \ttransformers \taccelerate` 使用了制表符（`\t`）且 `fastapi_sso` 后缺少 `-i` 镜像源参数，虽然当前错误不在此处，但这是潜在的语法/安装源不一致问题，应在修复时一并修正。

## 修复验证要求
若修复方向涉及拆分 RUN 命令或添加 pip 重试参数，code-fixer 需确认：
- 修改后的 Dockerfile 需要在 CI 环境中至少成功构建一次，以排除网络问题非偶然性。
- 验证 `pip install` 拆分后各步骤之间无依赖传递问题（如 `pydantic` 先装后被 `requirements.txt` 覆盖）。
