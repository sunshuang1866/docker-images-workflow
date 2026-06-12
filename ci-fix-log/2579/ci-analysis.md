# CI 失败分析报告

## 基本信息
- PR: #2579 — 【自动升级】sglang容器镜像升级至0.5.13版本.
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: pip下载连接中断
- 新模式症状关键词: IncompleteRead, ProtocolError, Connection broken, nvidia_cusparse, pip install

## 根因分析

### 直接错误
```
#12 453.1   Downloading nvidia_cusparse-12.6.3.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (145.9 MB)
#12 453.1    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸                       64.3/145.9 MB 7.5 MB/s eta 0:00:11
#12 453.1 ERROR: Exception:
#12 453.1 Traceback (most recent call last):
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 897, in _error_catcher
#12 453.1     yield
#12 453.1   File "/usr/local/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 1043, in _raw_read
#12 453.1     raise IncompleteRead(self._fp_bytes_read, self.length_remaining)
#12 453.1 pip._vendor.urllib3.exceptions.IncompleteRead: IncompleteRead(64337044 bytes read, 81605893 more expected)
...
#12 453.1 pip._vendor.urllib3.exceptions.ProtocolError: ('Connection broken: IncompleteRead(64337044 bytes read, 81605893 more expected)', IncompleteRead(64337044 bytes read, 81605893 more expected))
#12 ERROR: process "/bin/sh -c pip3 install --no-cache-dir --break-system-packages ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/sglang/0.5.13/24.03-lts-sp3/Dockerfile:49`（`pip3 install sglang` 步骤）
- 失败原因: 从 PyPI 下载 `nvidia_cusparse` (145.9 MB wheel) 时网络连接中断，下载到 64.3 MB 时连接断开（`IncompleteRead`），属于 CI 构建环境到 PyPI 的网络传输故障，与代码无关。

### 与 PR 变更的关联
PR 新增了 sglang 0.5.13 的 Dockerfile 及相关元数据文件。Dockerfile 结构本身没有问题（多阶段构建、依赖声明、路径引用均正确）。失败发生在 `pip3 install sglang` 的**依赖下载阶段**——sglang 0.5.13 依赖大量 CUDA 生态的巨型 wheel 包（合计下载量数 GB，仅 `nvidia_cusparse` 即 145.9 MB），构建环境的网络在下载该包时发生中断。**此失败与 PR 变更内容无关**，属于 CI 基础设施层面的暂时性网络故障。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为临时性网络中断（`IncompleteRead`），属于构建环境到 PyPI 的网络连接被意外断开，不是代码或 Dockerfile 缺陷。在下一次构建中，pip 会重新下载该依赖，大概率恢复正常。

### 方向 2（置信度: 低）
如果多次重试均在同一包下载阶段失败，可考虑在 Dockerfile 的 `pip3 install` 步骤中添加 `--retries 5 --timeout 120` 参数增加下载重试次数和超时容忍度，或考虑为大型 PyPI 包配置国内镜像源（如华为云 pypi 镜像）以提高下载稳定性。

## 需要进一步确认的点
- 此构建环境是否配置了 PyPI 代理或镜像源？若有，检查镜像源对 `nvidia_cusparse` 等大型 CUDA 包的缓存/代理是否稳定。
- 若构建环境无 `--no-cache-dir` 之外的下载重试机制，需确认 Buildkit/Podman 层面是否有网络稳定性配置。
- 检查同一时间段是否有其他 PR 的构建也出现了类似的 `IncompleteRead` 错误（可判断是否为 PyPI 服务端暂时性问题）。
