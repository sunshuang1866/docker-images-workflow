# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络超时
- 新模式症状关键词: ReadTimeoutError, pip install, mirrors.aliyun.com, Read timed out, large wheel download

## 根因分析

### 直接错误
```
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
...
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
#12 257.5 TimeoutError: The read operation timed out
...
#12 ERROR: process "/bin/sh -c npm config set registry https://registry.npmmirror.com/ && ... pip install -r backend/requirements.txt ... accelerate -i https://mirrors.aliyun.com/pypi/simple/" did not complete successfully: exit code: 2
```

```
------                                              
Dockerfile:28
--------------------
  27 |     
  28 | >>> RUN npm config set registry https://registry.npmmirror.com/ && \
  29 | >>>     npm i && \
  30 | >>>     npm run build && \
  31 | >>>     pip install pydantic -i https://mirrors.aliyun.com/pypi/simple/ && \
  32 | >>>     pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ && \
  33 | >>>     pip install fastapi_sso \
  34 | >>> 	transformers \
  35 | >>> 	accelerate -i https://mirrors.aliyun.com/pypi/simple/
  36 |     RUN pip uninstall litellm -y
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（pip install 步骤）
- 失败原因: pip 通过 `mirrors.aliyun.com` 镜像站下载 `nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl`（366.2 MB 大文件）时发生 TCP 读超时（`Read timed out`）。下载进度停在 353.4/366.2 MB 后连接中断，pip 抛出 `ReadTimeoutError` 导致整个 RUN 指令失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅为 open-webui 新增 24.03-LTS-SP4 版本的 Dockerfile 及配套元数据更新，构建命令结构和依赖声明均正确。失败是 CI 构建环境中 pip 从阿里云镜像站下载大型 wheel 包（nvidia_cudnn_cu13, 366MB）时网络连接超时所致，属于基础设施网络波动问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 中）
重新触发 CI 构建。网络超时通常是暂时性的，下次构建时镜像站连接可能恢复正常。如果大型 wheel 包能完整下载，构建即可通过。

### 方向 2（置信度: 低）
若多次重试仍超时，可考虑将 pip 镜像源从 `mirrors.aliyun.com` 更换为其他可用镜像站（如 `mirrors.tuna.tsinghua.edu.cn` 或官方 PyPI），或对 `nvidia_cudnn_cu13` 这类超大型包使用 `--default-timeout` 参数增加超时阈值。

## 需要进一步确认的点
- `mirrors.aliyun.com` 在该 CI 构建时段是否存在网络波动或带宽限制（需运维确认）
- 是否有其他同批次 PR 的构建也遇到类似的 `mirrors.aliyun.com` 超时问题，以判断是偶发还是系统性问题
- 若该镜像有其他版本的 Dockerfile（如 22.03-lts-sp4、24.03-lts-sp1），其构建是否也因同样原因失败（可作对比确认）
