# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 阿里云镜像下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, Read timed out, pip install, nvidia_cudnn

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
------
ERROR: failed to solve: process "/bin/sh -c npm config set registry https://registry.npmmirror.com/ && npm i && npm run build && pip install pydantic -i https://mirrors.aliyun.com/pypi/simple/ && pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ && pip install fastapi_sso 	transformers 	accelerate -i https://mirrors.aliyun.com/pypi/simple/" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（RUN 指令中的 pip install 步骤）
- 失败原因: pip 从 `mirrors.aliyun.com` 下载 `nvidia_cudnn_cu13` 包（366.2 MB）时发生网络读超时，下载进度卡在 353.4/366.2 MB 后连接中断。npm 构建阶段已成功完成，失败仅发生在后续的大体积 pip 包下载阶段。

### 与 PR 变更的关联
PR 新增了 openEuler 24.03-LTS-SP4 的 Dockerfile，其中 pip 下载源设置为 `https://mirrors.aliyun.com/pypi/simple/`。失败并非 PR 代码逻辑缺陷所致，而是阿里云镜像站在下载大体积包（`nvidia_cudnn_cu13`，约 366 MB）时网络不稳定导致的连接超时。已有兄弟 Dockerfile（如 `24.03-lts-sp1`）同样使用阿里云镜像，此类超时属于间歇性网络基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
换用更稳定的 pip 镜像源或添加重试机制。可将 pip 安装命令中的 `-i https://mirrors.aliyun.com/pypi/simple/` 替换为其他镜像（如清华镜像 `https://pypi.tuna.tsinghua.edu.cn/simple/`），或为 pip 命令添加 `--retries 5 --timeout 120` 参数以提高大文件下载的容错能力。

### 方向 2（置信度: 低）
拆分 RUN 步骤，将大体积依赖下载单独放在一个 RUN 层中，利用 Docker 构建缓存减少重复下载。若超时持续发生，可将 `nvidia_cudnn_cu13` 等特大包改为预下载到本地或使用多阶段构建从官方镜像复制。

## 需要进一步确认的点
- 阿里云镜像 `mirrors.aliyun.com` 从 CI 构建环境（Jenkins runner）的连通性及带宽是否持续不稳定，建议在 CI 环境中手动测试 `pip download nvidia-cudnn-cu13==9.20.0.48 -i https://mirrors.aliyun.com/pypi/simple/` 验证是否为一次性网络抖动
- 确认 `24.03-lts-sp1` 版本 Dockerfile 的构建是否也偶发同样的超时（若同用阿里云镜像），以判断是否需要全局更换镜像源
