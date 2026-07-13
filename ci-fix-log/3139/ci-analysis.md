# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 镜像站大文件下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, pip install, nvidia-cudnn-cu13

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
#12 257.5   ...
#12 257.5   File "/usr/lib64/python3.11/ssl.py", line 1167, in read
#12 257.5     return self._sslobj.read(len, buffer)
#12 257.5 TimeoutError: The read operation timed out
#12 257.5 ...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

下载 `nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl`（366.2 MB）时，在 353.4/366.2 MB（约 96%）处发生读超时。

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`
- 失败原因: `pip install -r backend/requirements.txt` 从 `mirrors.aliyun.com` 下载大型 wheel 包 `nvidia-cudnn-cu13`（366 MB）时网络读超时。此前 npm 构建（`npm i && npm run build`）已成功完成，证明 Dockerfile 逻辑本身无误，失败由镜像站网络不稳定导致。

### 与 PR 变更的关联

PR 新增了 open-webui 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其中所有 pip 操作均指定 `-i https://mirrors.aliyun.com/pypi/simple/` 作为镜像源。`nvidia-cudnn-cu13`（366 MB）是 `torch` → `sentence_transformers` 的传递依赖，安装时从阿里云镜像站下载该大文件触发读超时。

此失败**与 PR 代码变更相关**（Dockerfile 选择了特定镜像站），但**非代码逻辑错误**——属于网络基础设施不稳定导致，重试可能成功。

## 修复方向

### 方向 1（置信度: 中）
在 Dockerfile 的 pip install 命令中增加重试机制（如 `--retries 5 --timeout 120`），或为大型依赖单独拆分安装步骤以提高单点重试成功率。

### 方向 2（置信度: 低）
考虑将 pip 镜像源切换为其他更稳定的大型文件托管源（如 `pypi.org` 加代理，或 `pypi.tuna.tsinghua.edu.cn`），避免阿里云镜像站对大文件下载的不稳定问题。

## 需要进一步确认的点
- 同仓库内其他使用 `mirrors.aliyun.com` 的 Dockerfile（如 `open-webui/0.1.108/22.03-lts-sp4/Dockerfile`、`open-webui/0.1.108/24.03-lts-sp1/Dockerfile`）在 CI 中是否也出现过类似超时，以判断是偶发还是持久性问题。
- 该镜像站对超大文件（>300 MB）的下载是否存在带宽限制或超时配置。
- 是否可以通过 CI 重试机制（而非 Dockerfile 修改）解决该问题。
