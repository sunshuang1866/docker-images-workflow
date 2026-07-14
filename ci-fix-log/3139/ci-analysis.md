# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, Read timed out, nvidia-cudnn-cu13

## 根因分析

### 直接错误

```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
...
#12 257.5   File "/usr/lib64/python3.11/socket.py", line 718, in readinto
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

构建日志中出现的 `#10` 行（含 `error`、`errors` 等关键字）为 `tar -xvf` 解压 Node.js 时的正常文件路径输出，并非真实错误。**唯一的实际错误**是 pip 从 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13`（366.2 MB）时发生的读取超时：

```
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
#12 257.5 ERROR: Exception:
```

下载进度停在 353.4/366.2 MB 时连接超时。

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（`RUN` 多命令合并步骤中的 `pip install` 阶段）
- 失败原因: CI 构建环境从 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13`（366.2 MB 的 PyTorch CUDA 依赖）时发生网络读取超时，pip 抛出 `ReadTimeoutError`

### 与 PR 变更的关联

**与 PR 改动无直接关联**。该失败为 CI 基础设施网络问题（镜像站超时），非 PR 新增 Dockerfile 的代码逻辑缺陷。PR 仅新增了一个标准的 Dockerfile 和配套元数据，Dockerfile 中的安装命令语法正确。npm 构建阶段和大部分 pip 包下载均已成功完成，仅有最后一个大体积包 `nvidia-cudnn-cu13` 在下载至 96.5% 时因网络原因超时。

## 修复方向

### 方向 1（置信度: 中）
将 `mirrors.aliyun.com` 替换为更稳定的镜像源（如 `mirrors.huaweicloud.com` 或 `pypi.tuna.tsinghua.edu.cn`），或将大体积依赖包的下载源指定为上游 PyPI 官方源，避免阿里云镜像站间歇性超时。

### 方向 2（置信度: 中）
在 `pip install` 命令中增加 `--default-timeout=300`（延长超时时间）或添加 `--retries 5`（启用重试机制），使 pip 在网络波动时可自动重试而非直接失败。

### 方向 3（置信度: 低）
将 `npm i && npm run build` 和 `pip install` 拆分为两个独立的 RUN 层，利用 Docker 构建缓存减少重试时的重复下载时间。

## 需要进一步确认的点

1. 在 CI 构建环境中对 `mirrors.aliyun.com` 进行连通性和下载速度测试，确认是否为持续性问题还是偶发性波动
2. 确认同仓库中其他使用 `mirrors.aliyun.com` 的 Dockerfile 是否近期也出现类似超时问题（如该镜像站近期稳定性下降，可能需全局更换源）
3. 确认 `nvidia-cudnn-cu13` 包在阿里云镜像站的同步状态是否正常（该包 366 MB，若镜像站本身对该包的缓存有问题也会导致超时）
