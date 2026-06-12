# CI 失败分析报告

## 基本信息
- PR: #2579 — 【自动升级】sglang容器镜像升级至0.5.13版本.
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: pip下载网络中断
- 新模式症状关键词: IncompleteRead, Connection broken, ProtocolError, pip install, nvidia_cusparse

## 根因分析

### 直接错误
```
#12 453.1 ERROR: Exception:
#12 453.1 Traceback (most recent call last):
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 897, in _error_catcher
#12 453.1     yield
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 1043, in _raw_read
#12 453.1     raise IncompleteRead(self._fp_bytes_read, self.length_remaining)
#12 453.1 pip._vendor.urllib3.exceptions.IncompleteRead: IncompleteRead(64337044 bytes read, 81605893 more expected)
#12 453.1 ...
#12 453.1 pip._vendor.urllib3.exceptions.ProtocolError: ('Connection broken: IncompleteRead(64337044 bytes read, 81605893 more expected)', IncompleteRead(64337044 bytes read, 81605893 more expected))
#12 ERROR: process "/bin/sh -c pip3 install --no-cache-dir --break-system-packages ..." did not complete successfully: exit code: 2
------
Dockerfile:49
--------------------
  49 | >>> RUN pip3 install --no-cache-dir --break-system-packages \
  50 | >>>         --upgrade pip setuptools wheel && \
  51 | >>>     pip3 install --no-cache-dir --break-system-packages \
  52 | >>>         sglang
```

### 根因定位
- 失败位置: Dockerfile:49 — `pip3 install sglang` 步骤
- 失败原因: 在下载 `nvidia_cusparse-12.6.3.3`（约 145.9 MB）时 TCP 连接中断，仅读取了 64.3 MB，剩余 81.6 MB 未完成下载，导致 pip 抛出 `IncompleteRead` / `ProtocolError`。

### 与 PR 变更的关联
与 PR 变更**无直接关联**。PR 仅新增了 sglang 0.5.13 的 Dockerfile 及配套元数据文件，Dockerfile 本身的结构和指令语法正确。失败是由于 `pip install sglang` 拉取的大量 CUDA 相关二进制包（torch、nvidia-cublas、nvidia-cusparse 等，总计数 GB）在下载过程中遭遇网络抖动，属于 CI 构建环境的临时性网络故障。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建即可。此失败为临时性网络中断（pip 下载大文件时 TCP 连接断开），不是代码或配置问题。`sglang` 的依赖链包含多个大体积 CUDA wheel 包，对网络稳定性要求较高，偶发性中断属于常见的 CI 基础设施问题。

### 方向 2（置信度: 中）
如果重复构建仍失败，可考虑在 Dockerfile 的 `pip install` 命令中添加 `--retries 5`（或更高）参数以提高下载容错性，或在 CI 环境中配置 PyPI 镜像源（如清华镜像站）以减少对外网的依赖。

## 需要进一步确认的点
- 确认 CI Runner 的网络状况是否稳定（是否有代理、防火墙限制或带宽瓶颈）。
- 如果该问题在同一 PR 中多次复现，可能需要检查 PyPI 仓库是否对 `nvidia_cusparse` 等 CUDA 包的 CDN 分发存在区域性故障。
