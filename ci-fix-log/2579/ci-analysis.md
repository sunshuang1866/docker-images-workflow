# CI 失败分析报告

## 基本信息
- PR: #2579 — 【自动升级】sglang容器镜像升级至0.5.13版本.
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: pip下载连接中断
- 新模式症状关键词: IncompleteRead, Connection broken, ProtocolError, pip install, nvidia-cusparse

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
#12 ERROR: process "/bin/sh -c pip3 install --no-cache-dir --break-system-packages         --upgrade pip setuptools wheel &&     pip3 install --no-cache-dir --break-system-packages         sglang" did not complete successfully: exit code: 2
------
Dockerfile:49
```

### 根因定位
- 失败位置: `AI/sglang/0.5.13/24.03-lts-sp3/Dockerfile`:49（`pip3 install ... sglang` 命令）
- 失败原因: 在下载 `nvidia-cusparse` (145.9 MB wheel) 过程中网络连接中断，仅下载了 64.3 MB / 145.9 MB (约 44%)，触发 `IncompleteRead` 异常导致 pip 安装失败

### 与 PR 变更的关联
PR 新增了 sglang 0.5.13 的 Dockerfile。该 Dockerfile 中 `pip3 install sglang` 需要从 PyPI 下载大量 NVIDIA CUDA 相关依赖包（单个包可达数百 MB，日志显示已成功下载了 torch 530MB、nvidia-cublas 423MB、flashinfer_cubin 447MB 等大型包），下载过程中网络连接不稳定导致中途断开。此错误与 PR 代码逻辑无关，属于 CI 构建环境网络基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
重试构建。`Connection broken: IncompleteRead` 是典型的网络瞬时故障，通常重试即可成功。如果在 CI 流水线中频繁复现，可考虑：
- 在 pip install 命令中添加 `--retries 5 --timeout 120` 等重试参数
- 引入 PyPI 镜像源（如清华镜像 `https://pypi.tuna.tsinghua.edu.cn/simple`）提高下载稳定性
- 将 pip install 失败后的 retry 逻辑写入 Dockerfile（如 `for i in 1 2 3; do pip install ... && break || sleep 30; done`）

### 方向 2（置信度: 低）
如果重试始终失败且始终卡在同一个包（`nvidia-cusparse`），可能是 PyPI 上该包的分发 CDN 存在区域性问题。此时可考虑临时指定其他 PyPI 镜像源。

## 需要进一步确认的点
- 该构建失败是偶发还是每次触发都复现？需要查看同一 PR 的多次重试结果
- CI 构建环境与 PyPI 之间的网络链路是否存在限速或代理问题
- `nvidia-cusparse-12.6.3.3` 这个特定版本在 PyPI CDN 上是否完整可用（可手动 `curl -I` 验证 Content-Length 头）
