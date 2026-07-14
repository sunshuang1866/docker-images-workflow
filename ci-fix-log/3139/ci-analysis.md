# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式33（相似）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 227.3   Downloading nvidia_cudnn_cu13-9.20.0.48 (366.2 MB)
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
...
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5     raise ReadTimeoutError(self._pool, None, "Read timed out.")
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（合并的 RUN 指令中 pip install 步骤）
- 失败原因: 从阿里云 PyPI 镜像 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13` (366.2 MB) 时网络读取超时。下载进度到达 353.4/366.2 MB（约 96%）时触发 pip ReadTimeoutError，导致整个 RUN 指令失败。npm 前端构建（npm i && npm run build）在该步骤中已成功完成，仅后端 pip install 阶段失败。

### 与 PR 变更的关联
PR 新增了一个 Dockerfile（`AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile`），将镜像从 `openeuler:24.03-lts-sp1` 适配到 `openeuler:24.03-lts-sp4`。Dockerfile 本身逻辑与已有 sp1 版本一致。失败原因是 pip 下载大文件（366MB 的 cudnn wheel）时网络超时，属于 CI 构建环境的网络基础设施问题，**与 PR 代码变更无直接关联**。

## 修复方向

### 方向 1（置信度: 中）
这是网络超时导致的间歇性失败，重试构建可能直接通过。若确认该镜像站在 CI 环境中频繁超时，有两个思路：
- 将 pip 下载源从 `mirrors.aliyun.com` 更换为更稳定的镜像站（如 `pypi.org` 或 `pypi.tuna.tsinghua.edu.cn`）
- 对于超大依赖包（如 `nvidia-cudnn-cu13`），考虑单独拆分为独立的 RUN 步骤，避免因单个大文件超时导致整个 `npm install + build + pip install` 流水线全部回滚

### 方向 2（置信度: 低）
Dockerfile 将 npm install、npm build、多个 pip install 合并为一个 RUN 指令（Dockerfile:28-35）。虽然复用同一层可减少镜像体积，但一旦 pip 下载超时，已完成的 npm 构建也会废弃。可以考虑将构建步骤拆分为多个 RUN 指令以利用 Docker 层缓存，减少重试成本。但这不解决网络超时本身，仅提升重试效率。

## 需要进一步确认的点
1. 同一 Dockerfile 在 CI 重试后是否能成功（判断是持续性问题还是间歇性问题）
2. 已有的 `24.03-lts-sp1` 版本 Dockerfile 是否也使用相同的阿里云镜像站且存在类似超时问题
3. CI runner 到 `mirrors.aliyun.com` 的网络带宽与稳定性（366MB 文件下载约 16 秒，30 秒后超时，可能拥堵）

## 修复验证要求
无需代码修复验证。若确认重试多次均在同一大文件处超时，code-fixer 需确认替换的镜像站路径正确且 Python 包版本一致。
