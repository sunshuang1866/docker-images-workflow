# CI 失败分析报告

## 基本信息
- PR: #2579 — 【自动升级】sglang容器镜像升级至0.5.13版本.
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: pip下载中断
- 新模式症状关键词: IncompleteRead, ProtocolError, Connection broken, pip install, nvidia_cusparse

## 根因分析

### 直接错误
```
#12 444.5 Downloading nvidia_cusparse-12.6.3.3-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (145.9 MB)
#12 453.1    ━━━━━━━━━━━━━━━━━━━━━━━━━━━╸                       64.3/145.9 MB 7.5 MB/s eta 0:00:11
#12 453.1 ERROR: Exception:
#12 453.1 Traceback (most recent call last):
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 897, in _error_catcher
#12 453.1     yield
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 1043, in _raw_read
#12 453.1     raise IncompleteRead(self._fp_bytes_read, self.length_remaining)
#12 453.1 pip._vendor.urllib3.exceptions.IncompleteRead: IncompleteRead(64337044 bytes read, 81605893 more expected)
#12 453.1 ...
#12 453.1 pip._vendor.urllib3.exceptions.ProtocolError: ('Connection broken: IncompleteRead(64337044 bytes read, 81605893 more expected)', IncompleteRead(64337044 bytes read, 81605893 more expected))
#12 ERROR: process "/bin/sh -c pip3 install --no-cache-dir --break-system-packages ... sglang" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/sglang/0.5.13/24.03-lts-sp3/Dockerfile`:49（`pip3 install sglang` 行）
- 失败原因: 在 `pip3 install sglang` 下载依赖包 `nvidia-cusparse`（145.9 MB）时，网络连接在传输 64.3 MB 后中断，导致 `IncompleteRead` 异常，构建失败。

### 与 PR 变更的关联
本 PR 是新增 sglang 0.5.13 容器镜像的 Dockerfile，属于全新文件。失败与 PR 的代码逻辑无关，是 CI 构建环境在从 PyPI 下载大体积 CUDA 相关 Python 包时发生了网络中断。`pip3 install sglang` 默认会拉取完整的 GPU/CUDA 依赖链（torch、nvidia-cublas、nvidia-cusparse 等），总下载量超过 2 GB，单个包 nvidia-cusparse 达 145 MB，在网络不稳定的 CI 环境中容易因传输中断而失败。

## 修复方向

### 方向 1（置信度: 中）
重新触发 CI 构建。此错误本质是瞬时网络故障，不属于代码缺陷。通常情况下重试即可通过。

### 方向 2（置信度: 中）
在 Dockerfile 中为 `pip3 install` 命令添加 `--retries 5 --timeout 300` 等重试参数，增强对不稳定网络的容忍度，减少未来因网络波动导致的偶发失败。

## 需要进一步确认的点
- 无需进一步确认。日志中的 `IncompleteRead` / `ProtocolError` 是典型的下载中断错误，根因明确——CI 运行环境在从 PyPI 下载大型包时网络连接断开。
