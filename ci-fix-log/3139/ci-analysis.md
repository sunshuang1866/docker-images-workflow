# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: pip 镜像站下载超时
- 新模式症状关键词: ReadTimeoutError, Read timed out, mirrors.aliyun.com, pip install, HTTPSConnectionPool

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry https://registry.npmmirror.com/ && ... pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ && ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（RUN 指令中的 pip install 步骤）
- 失败原因: pip 从 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13`（366.2 MB 的大型 wheel 包，仅下载到 353.4/366.2 MB）时发生网络读取超时（`Read timed out`），导致整个 `pip install -r backend/requirements.txt` 失败，进而 Docker 构建退出码为 2。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增的 Dockerfile 语法正确，`pip install` 命令格式无误。失败原因是阿里云 PyPI 镜像站在下载大型包（`nvidia-cudnn-cu13` 366MB）时网络不稳定导致连接超时。这是一个纯粹的 CI 基础设施/网络问题。

## 修复方向

### 方向 1（置信度: 高）
**重试即可**。该失败是偶发性网络超时，建议在 CI 中重新触发构建。如果超时反复发生，可考虑以下可选措施：
- 在 Dockerfile 的 `pip install` 命令中增加重试机制（如 `pip install --retries 5 --timeout 120`）
- 切换 PyPI 镜像源为其他更稳定的镜像站（如 `https://mirrors.tuna.tsinghua.edu.cn/pypi/simple/`）

### 方向 2（置信度: 中）
如果重试仍然失败且同一镜像站反复对大型包超时，可以分两步安装：先 `pip install` 排除 `torch` 等重量级依赖的 requirements，再单独安装 `torch`（它会拉取 `nvidia-cudnn-cu13`），并为其单独设置更长的超时时间或使用其他镜像源。

## 需要进一步确认的点
- 确认 `mirrors.aliyun.com` 在当前 CI 网络环境中是否持续不稳定，是否有其他 PR 的构建也遇到同样的超时问题。如果是系统性问题，需考虑统一更换镜像源。
