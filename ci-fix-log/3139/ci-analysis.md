# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: pip镜像下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, HTTPSConnectionPool, Read timed out

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 457, in _error_catcher
#12 257.5     raise ReadTimeoutError(self._pool, None, "Read timed out.")
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry https://registry.npmmirror.com/ &&     npm i &&     npm run build &&     pip install pydantic -i https://mirrors.aliyun.com/pypi/simple/ &&     pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ &&     pip install fastapi_sso \ttransformers \taccelerate -i https://mirrors.aliyun.com/pypi/simple/" did not complete successfully: exit code: 2
```

### 上下文（超时发生时的下载进度）
```
#12 227.3   Downloading ... nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl (366.2 MB)
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`
- 失败原因: pip 从 `mirrors.aliyun.com` 下载 `nvidia_cudnn_cu13`（366.2 MB 的大体积 CUDA 依赖包）时发生 `ReadTimeoutError`，下载到 353.4/366.2 MB（约 96.5%）时 TCP 读取超时，导致整个 `pip install -r backend/requirements.txt` 步骤失败。

### 与 PR 变更的关联
**直接关联**。本次 PR 新增的 Dockerfile 中，所有 pip 安装步骤均硬编码使用 `https://mirrors.aliyun.com/pypi/simple/` 镜像源。该镜像源在传输大体积包（>300MB）时出现了 TCP 读取超时，导致构建失败。npm 安装（使用 `registry.npmmirror.com`）和其他较小的 pip 包均下载成功，仅最后的大包超时。

## 修复方向

### 方向 1（置信度: 低）
**重试构建**。`nvidia_cudnn_cu13`（366 MB）下载到 96.5% 时超时，属于典型的瞬时网络波动。如果 CI 提供重试机制，单纯重新触发构建有较大概率通过。需要确认：这是偶发超时还是 aliyun 镜像对该大包持续不可用。

### 方向 2（置信度: 低）
**增加 pip 超时容忍或切换镜像源**。如果重试仍然超时，可考虑：
- 在 pip install 命令中添加 `--timeout` 参数扩大默认超时（如 `--timeout 120`）
- 将该大体积依赖的下载源切换为其他镜像（如 `https://pypi.tuna.tsinghua.edu.cn/simple/`）
- 在 Dockerfile 中为 `nvidia_cudnn_cu13` 之类的大包单独设置下载源或使用 `--default-timeout` 参数

## 需要进一步确认的点
1. 重新触发相同 CI job 是否仍会在同一位置超时？如果是持续复现，说明 aliyun 镜像对该大包存在稳定性问题，需要换源。
2. aliyun 镜像对 `nvidia_cudnn_cu13-9.20.0.48`（366 MB）的 CDN 分发是否完整？其他仓库（如 `pypi.tuna.tsinghua.edu.cn`）是否已缓存该大包？
3. open-webui 上游 `backend/requirements.txt` 是否可以通过配置排除不必要的 CUDA 依赖来缩小下载体积？
4. 其他已存在的镜像（如 `24.03-lts-sp1` 的 open-webui Dockerfile）是否也使用 aliyun 镜像源、是否遇到过同样的大包超时问题？
