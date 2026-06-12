# CI 失败分析报告

## 基本信息
- PR: #2579 — 【自动升级】sglang容器镜像升级至0.5.13版本.
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: pip大文件下载中断
- 新模式症状关键词: IncompleteRead, Connection broken, ProtocolError, pip install, 下载中断

## 根因分析

### 直接错误
```
#12 453.1 ERROR: Exception:
#12 453.1 Traceback (most recent call last):
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 897, in _error_catcher
#12 453.1     yield
#12 453.1   ...
#12 453.1 pip._vendor.urllib3.exceptions.IncompleteRead: IncompleteRead(64337044 bytes read, 81605893 more expected)
#12 453.1 ...
#12 453.1 pip._vendor.urllib3.exceptions.ProtocolError: ('Connection broken: IncompleteRead(64337044 bytes read, 81605893 more expected)', IncompleteRead(64337044 bytes read, 81605893 more expected))
#12 ERROR: process "/bin/sh -c pip3 install --no-cache-dir --break-system-packages         --upgrade pip setuptools wheel &&     pip3 install --no-cache-dir --break-system-packages         sglang" did not complete successfully: exit code: 2
------
Dockerfile:49
--------------------
  49 | >>> RUN pip3 install --no-cache-dir --break-system-packages \
  50 | >>>         --upgrade pip setuptools wheel && \
  51 | >>>     pip3 install --no-cache-dir --break-system-packages \
  52 | >>>         sglang
```

### 根因定位
- 失败位置: Dockerfile:49 (`pip3 install sglang`)
- 失败原因: 在下载 `nvidia_cusparse-12.6.3.3`（145.9 MB 的 wheel 包）时网络连接中断，仅下载了 64.3 MB（44%），导致 `IncompleteRead` / `ProtocolError`，pip 安装退出码为 2

### 与 PR 变更的关联
PR 新增了 sglang 0.5.13 的 Dockerfile（`AI/sglang/0.5.13/24.03-lts-sp3/Dockerfile`，90 行新文件），该 Dockerfile 在编译阶段通过 `pip3 install sglang` 安装 sglang 及其所有依赖。sglang 0.5.13 依赖链极重，涉及多个超大 wheel 包（`nvidia_cublas` 423 MB、`nvidia_cudnn_cu13` 366 MB、`sglang_kernel` 323 MB、`flashinfer_cubin` 448 MB、`torch` 531 MB 等），总下载量超过 2 GB。本次失败与 PR 代码逻辑无直接因果关系，属于构建过程中 PyPI/CDN 网络传输的偶发性中断。但 Dockerfile 中 `--no-cache-dir` 的使用导致每次构建都必须从零下载全部依赖，放大了网络不稳定带来的失败风险。

### 附加发现：Dockerfile 存在 Shell 语法错误
在 PR diff 的第 7 步 `find` 命令中存在多余的 `$` 字符：
```
find ${SGL_HOME} -type f $ -name "*.so" -o -name "*.a" $ \
```
`$` 在 shell 中不是有效的 find 谓词或路径参数，会导致 `find` 报错。此错误在当前失败点（第 6 步 `pip3 install`）之后，本次构建未执行到该步骤，但即使网络问题修复后，该行也会导致后续构建失败。正确的写法应为 `\( -name "*.so" -o -name "*.a" \)` 或去掉多余的 `$`。

## 修复方向

### 方向 1（置信度: 中）
**重试即可**。`IncompleteRead` / `Connection broken` 是典型的 transient network error（暂时性网络故障），重新触发 CI 构建大概率可以通过。pypi.org 及 CDN 的偶发连接中断不属于代码层面的问题。Code Fixer 无需处理此类 infra-error，但建议 re-run CI。

### 方向 2（置信度: 中）
**提高 pip 下载可靠性**。可为 pip install 添加 `--retries 5 --timeout 120` 参数，利用 pip 内置的重试机制对抗短暂网络波动：
```
pip3 install --no-cache-dir --retries 5 --timeout 120 --break-system-packages sglang
```

### 方向 3（置信度: 高）
**修复 Dockerfile 中 `find` 命令的 `$` 语法错误**。将：
```
find ${SGL_HOME} -type f $ -name "*.so" -o -name "*.a" $ \
```
修正为：
```
find ${SGL_HOME} -type f \( -name "*.so" -o -name "*.a" \) \
```

## 需要进一步确认的点
- 由于 pip 下载失败，构建未执行到 `find` 收集 .so/.a 产物的步骤。网络问题解决后，该步骤的 shell 语法错误（多余 `$`）会成为新的失败点，需一并修复。
- 若多次重试 CI 后仍然在下载大文件（特别是 100 MB+ 的 nvidia wheel 包）时失败，可能需要排查 CI Runner 所在网络环境对 PyPI/CDN 的连接稳定性，或考虑引入本地 PyPI 镜像/代理缓存。
