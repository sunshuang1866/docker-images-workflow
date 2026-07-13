# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: PyPI镜像下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, Read timed out, pip install, nvidia-cudnn

## 根因分析

### 直接错误
```
#12 227.3   Downloading https://mirrors.aliyun.com/pypi/packages/6e/5e/.../nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl (366.2 MB)
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
------
ERROR: failed to solve: process "/bin/sh -c npm config set registry ... && pip install ... -i https://mirrors.aliyun.com/pypi/simple/" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28`（`pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/` 步骤）
- 失败原因: pip 从阿里云 PyPI 镜像站下载 `nvidia-cudnn-cu13`（366.2 MB）时，在下载到 353.4 MB（约 96%）处发生 TCP 读超时，阿里云镜像站连接中断。

### 与 PR 变更的关联
PR 新增了 `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile`，该 Dockerfile 第 28 行通过 `pip install -r backend/requirements.txt` 安装大量 Python 依赖，依赖链中包含 PyTorch → `nvidia-cudnn-cu13`（366 MB 超大 wheel 包）。超时本身是网络基础设施问题，与 PR 代码逻辑无关，但依赖包体积过大增加了超时风险。PR 中的 `README.md`、`doc/image-info.yml`、`meta.yml` 均为纯文档/元数据变更，不参与构建。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。**网络超时属于临时性基础设施问题，`mirrors.aliyun.com` 在多数情况下是可用的。重试构建大概率可以成功通过。

### 方向 2（置信度: 中）
**将 pip install 命令拆分为多个独立 RUN 层**，利用 Docker 层缓存减少重试时重复下载的成本。同时可为 pip install 添加 `--retries` 参数增加下载重试次数，或改用其他 PyPI 镜像源（如清华镜像站 `pypi.tuna.tsinghua.edu.cn`）作为备选。

### 方向 3（置信度: 低）
**预先安装 PyTorch 等重依赖的 wheel 文件**，避免在 Docker 构建时从远端下载超大包。可将 nvidia-cudnn-cu13 等超大包提前下载到镜像内或使用本地缓存。

## 需要进一步确认的点
- 阿里云 PyPI 镜像站（`mirrors.aliyun.com`）在 CI 构建时段是否确实存在间歇性网络波动。
- 该 CI runner 的网络超时阈值是多少，是否需要适当调大 pip 的默认超时参数。
- 其他使用 `mirrors.aliyun.com` 作为 pip 源的镜像（如同仓库中已有的 `open-webui/22.03-lts-sp4` 和 `24.03-lts-sp1` 版本）是否也出现过类似超时问题。
