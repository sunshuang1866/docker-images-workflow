# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: pip镜像下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, pip install, nvidia-cudnn-cu13, Read timed out

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 457, in _error_catcher
#12 257.5     raise ReadTimeoutError(self._pool, None, "Read timed out.")
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry https://registry.npmmirror.com/ && ... && pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ && ..." did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`
- 失败原因: `pip install -r backend/requirements.txt` 从 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13==9.20.0.48`（366.2 MB，`torch` 的传递依赖）时网络读取超时，下载进度停在 353.4/366.2 MB（96.5%），触发 `ReadTimeoutError`。

### 与 PR 变更的关联
PR 新增了 open-webui 的 SP4 Dockerfile（全新文件），其中 `pip install` 指定了 `-i https://mirrors.aliyun.com/pypi/simple/` 作为 Python 包索引源。该镜像源配置与项目其他 Dockerfile 的惯用做法一致，并非本次 PR 引入的特殊配置。npm 阶段（`npm i` + `npm run build`）和 pip 的小体积包下载均成功，仅在大文件 `nvidia-cudnn-cu13`（366 MB）下载接近完成时超时。该超时属于 CI 构建环境的临时网络波动或阿里云镜像站对该大文件的连接稳定性问题，与 PR 的代码改动无直接因果关系。

### 补充说明
日志开头的"Error lines (newest first)"部分包含大量 `node-v18.0.0-linux-x64/lib/node_modules/npm/.../error*.js` 路径，这些是 `tar -xvf` 解压 Node.js 二进制包时的**正常提取输出**（文件路径中包含 `error` 字样），**并非构建错误**。实际第一个真正的错误是上述 pip 超时。

## 修复方向

### 方向 1（置信度: 中）
直接重试 CI 构建。网络超时是典型的瞬时性基础设施问题，尤其是大文件下载在接近完成时超时，重试后通常可以成功。若重试仍失败，需考虑更换 PyPI 镜像源或为大文件下载添加重试机制。

### 方向 2（置信度: 低）
若多次重试在同一位置（`nvidia-cudnn-cu13` 下载）均超时，可能是阿里云镜像站对该特定大文件的 CDN 分发不稳定。可考虑将 PyPI 镜像源从 `mirrors.aliyun.com` 换为 `pypi.tuna.tsinghua.edu.cn` 或 `mirrors.ustc.edu.cn`，或在 `pip install` 命令中增加 `--default-timeout=300` 提高超时阈值。

## 需要进一步确认的点
- 确认同一时间段内其他使用 `mirrors.aliyun.com` 的 Dockerfile 构建是否也出现类似超时（以判断是阿里云镜像站的普遍问题还是个案）
- 确认 CI 构建环境的网络状况（是否存在带宽限制或代理问题）
- 确认是否存在已有 SP1 Dockerfile（`24.03-lts-sp1/Dockerfile`）且其构建日志中是否也使用相同镜像源未超时（作为对比参考）
