# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络超时
- 新模式症状关键词: ReadTimeoutError, Read timed out, mirrors.aliyun.com, HTTPSConnectionPool, pip, nvidia-cudnn

## 根因分析

### 直接错误

```
#12 227.3   Downloading .../nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl (366.2 MB)
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c ... pip install ... -i https://mirrors.aliyun.com/pypi/simple/ ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `Dockerfile:28-35`（`pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/` 步骤）
- 失败原因: CI 构建环境在通过 `mirrors.aliyun.com` 下载依赖包 `nvidia-cudnn-cu13-9.20.0.48`（366.2 MB）时发生网络读超时，下载进度到达 353.4/366.2 MB 后 TCP 连接超时中断。

### 与 PR 变更的关联
**与 PR 改动无关**。该 PR 仅新增了 `open-webui` 在 `openEuler:24.03-lts-sp4` 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。失败原因是 pip 从阿里云镜像站下载大型 CUDA 依赖包（`nvidia-cudnn-cu13`，366 MB）时网络超时，属于 CI 基础设施的网络稳定性问题，与 Dockerfile 代码逻辑无直接关联。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。网络超时属于临时性基础设施问题，概率性发生。如果阿里云镜像站到 CI 构建节点的链路恢复稳定，重新触发 CI 流水线即可通过。

### 方向 2（置信度: 低）
**更换 pip 镜像源**。若阿里云镜像站对该 CI 节点持续不稳定，可将 Dockerfile 中所有 `-i https://mirrors.aliyun.com/pypi/simple/` 替换为其他可用镜像源（如清华镜像站 `https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/` 或华为云镜像站）。但需注意：镜像切换仅在其他 pip 依赖下载也受影响的场景下才有意义，当前日志显示其他包下载正常，仅有最后一个大文件超时。

## 需要进一步确认的点
- CI 构建节点到 `mirrors.aliyun.com`（阿里云镜像站）的网络链路质量是否持续拥塞或被限速，建议先在 CI 环境手动测试 `wget https://mirrors.aliyun.com/pypi/packages/.../nvidia_cudnn_cu13-9.20.0.48-...whl` 确认可复现性
- 若重试后仍失败，检查 CI runner 是否有下载大小/超时限制
- `nvidia-cudnn-cu13`（366 MB）是 `torch` → `sentence_transformers` 的依赖链拉入的，属于 GPU/CUDA 相关包。如果可以接受 CPU-only 版本，可考虑安装 `torch` 的 CPU 版本以减小下载体积、降低超时风险
