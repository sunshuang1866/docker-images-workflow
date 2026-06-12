# CI 失败分析报告

## 基本信息
- PR: #2579 — 【自动升级】sglang容器镜像升级至0.5.13版本.
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: pip下载连接中断
- 新模式症状关键词: IncompleteRead, Connection broken, ProtocolError, pip install, nvidia_cusparse

## 根因分析

### 直接错误
```
#12 444.5 Downloading nvidia_cusparse-12.6.3.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (145.9 MB)
#12 453.1    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸                       64.3/145.9 MB 7.5 MB/s eta 0:00:11
#12 453.1 ERROR: Exception:
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 897, in _error_catcher
#12 453.1     yield
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 1043, in _raw_read
#12 453.1     raise IncompleteRead(self._fp_bytes_read, self.length_remaining)
#12 453.1 pip._vendor.urllib3.exceptions.IncompleteRead: IncompleteRead(64337044 bytes read, 81605893 more expected)
#12 453.1 ...
#12 453.1 pip._vendor.urllib3.exceptions.ProtocolError: ('Connection broken: IncompleteRead(64337044 bytes read, 81605893 more expected)', IncompleteRead(64337044 bytes read, 81605893 more expected))
```

```
Dockerfile:49
--------------------
  49 | >>> RUN pip3 install --no-cache-dir --break-system-packages \
  50 | >>>         --upgrade pip setuptools wheel && \
  51 | >>>     pip3 install --no-cache-dir --break-system-packages \
  52 | >>>         sglang
```

### 根因定位
- 失败位置: `AI/sglang/0.5.13/24.03-lts-sp3/Dockerfile:49`
- 失败原因: `pip install sglang` 下载 `nvidia_cusparse-12.6.3.3` (145.9 MB) 时 PyPI 连接中断，仅完成 64.3/145.9 MB 后发生 `IncompleteRead` 异常，属于临时性网络基础设施故障。

### 与 PR 变更的关联
本次 PR 新增了 sglang 0.5.13 的 Dockerfile，构建过程中首次触发 `pip install sglang`，该命令需要从 PyPI 下载大量 CUDA 相关依赖包（总计数 GB），在下载大型 wheel 包 `nvidia_cusparse` 时遭遇网络连接中断。**CI 失败与 PR 代码质量无关，属于基础设施层临时性网络故障。**

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。`IncompleteRead` 是典型的临时网络中断，通常重试即可成功。无需修改任何代码。

### 方向 2（置信度: 低）
如果反复出现同样的网络中断问题，可考虑在 Dockerfile 的 `pip install` 步骤中增加 `--retries` 参数提高下载容错性，或为 pip 配置国内 PyPI 镜像源加速下载。但当前日志仅显示一次性中断，不建议针对单次网络抖动做出修改。

## 需要进一步确认的点
- 该 CI runner 到 PyPI CDN 的网络稳定性情况（可通过重试确认是否为偶发中断）。
- `nvidia_cusparse` 等 CUDA 专用包被安装到标注"CPU 版本"的 Dockerfile 中。虽然这不是本次失败的直接原因，但建议确认：如果目标是 CPU-only 镜像，`pip install sglang` 应当使用 CPU 版本的 PyTorch 索引（如 `--index-url https://download.pytorch.org/whl/cpu`），否则镜像体积会因引入无用 CUDA 依赖而膨胀；如果确实需要 CUDA 支持，则 Dockerfile 注释中的"CPU 版本"表述需要修正。
