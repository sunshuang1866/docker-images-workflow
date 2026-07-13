# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: pip镜像站下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, pip install timeout, nvidia_cudnn, HTTPSConnectionPool

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
#12 257.5   ...
#12 257.5   File "/usr/lib64/python3.11/ssl.py", line 1167, in read
#12 257.5     return self._sslobj.read(len, buffer)
#12 257.5 TimeoutError: The read operation timed out
#12 257.5 ...
#12 257.5     raise ReadTimeoutError(self._pool, None, "Read timed out.")
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

构建 log 显示，正在下载 `nvidia_cudnn_cu13-9.20.0.48`（366.2 MB）时连接超时：
```
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（合并的 RUN 指令中的 `pip install -r backend/requirements.txt` 步骤）
- 失败原因: `pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/` 在下载 `nvidia_cudnn_cu13`（366 MB）时，与 `mirrors.aliyun.com` 的 HTTPS 连接发生读取超时，pip 未配置重试机制，导致整个 RUN 层构建失败。

### 与 PR 变更的关联
PR 新增了 `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile`，该 Dockerfile 中硬编码了阿里云镜像站作为 pip 源。npm 构建部分（`npm i && npm run build`）已成功完成，失败仅发生在后续的 pip install 阶段。问题本质是镜像站网络可靠性问题，非 PR 代码逻辑错误，但 Dockerfile 中大型 RUN 指令的设计（将 npm 和 pip 操作合并在一个 RUN 层）加剧了失败成本——每次重试都需要重新执行 npm 构建。

## 修复方向

### 方向 1（置信度: 中）
在 Dockerfile 的 pip install 命令中添加 `--retries 5 --timeout 120` 参数，提高对偶发网络超时的容忍度。同时将大型 RUN 指令拆分为独立的 npm 构建层和 pip 安装层，使 pip 重试时无需重新执行 npm 构建。

### 方向 2（置信度: 低）
将 pip 镜像源从 `mirrors.aliyun.com` 更换为其他更可靠的中国镜像站（如清华大学 TUNA `https://pypi.tuna.tsinghua.edu.cn/simple/`），或使用官方 PyPI 源但配置代理/重试。需要确认 CI 环境对目标镜像站的网络可达性。

### 方向 3（置信度: 低）
对超大包（如 `nvidia_cudnn_cu13` 366 MB、`llvmlite` 59.9 MB 等）进行预下载或使用 `--no-deps` 分批安装，降低单次下载失败导致全局回滚的概率。

## 需要进一步确认的点
1. 需要确认 CI 构建节点到 `mirrors.aliyun.com` 的网络稳定性——是否存在间歇性丢包或带宽限制导致大文件下载超时。
2. 需要对比同类型镜像（如 `AI/open-webui/0.1.108/22.03-lts-sp4/Dockerfile`、`AI/open-webui/0.1.108/24.03-lts-sp1/Dockerfile`）是否也使用相同的 pip 源和类似的 RUN 结构，确认本次失败是首次出现还是已知模式。
3. 需确认 `nvidia_cudnn_cu13-9.20.0.48` 这个 366 MB 的 wheel 在其他 openEuler Docker 镜像构建中是否也曾导致超时——如果多次出现，应建立统一的 pip 重试规范。

## 修复验证要求
若修复方向为添加 pip retries 参数或更换镜像源，code-fixer 必须：
- 确认目标镜像源在 CI 构建网络中可达且稳定（不能仅凭书面判断）。
- 验证修改后完整的 Dockerfile 构建流程（包括 npm 和 pip 阶段）可正常完成。
