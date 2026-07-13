# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: PyPI镜像下载超时
- 新模式症状关键词: Read timed out, ReadTimeoutError, mirrors.aliyun.com, pip install

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
#12 257.5 ...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry https://registry.npmmirror.com/ &&     npm i &&     npm run build &&     pip install pydantic -i https://mirrors.aliyun.com/pypi/simple/ &&     pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ &&     pip install fastapi_sso \ttransformers \taccelerate -i https://mirrors.aliyun.com/pypi/simple/" did not complete successfully: exit code: 2
```

下载进度中断点：
```
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
```
正在下载的包为 `nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl`（366.2 MB），仅剩约 12.8 MB 时 TCP 读取超时。

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（`pip install -r backend/requirements.txt` 步骤）
- 失败原因: CI 构建环境通过 `mirrors.aliyun.com` PyPI 镜像站下载 `nvidia-cudnn-cu13`（366.2 MB，torch 的间接依赖）时发生 TCP 读取超时，pip 无法完成依赖解析与安装。

### 与 PR 变更的关联
与 PR 代码变更**无直接关联**。PR 新增了一个完全新的 Dockerfile（首次构建），失败是 CI 基础设施层面的网络问题（镜像站连接超时），而非 Dockerfile 语法或逻辑错误。npm 构建阶段（`npm i && npm run build`）已成功完成，pip 安装前期大量包下载正常，仅最后一个大包 `nvidia-cudnn-cu13`（366.2 MB）下载中断。

## 修复方向

### 方向 1（置信度: 中）
**重试即可**。该失败为网络瞬断所致，属于偶发性 infra-error。Code Fixer 无需修改代码，触发 CI 重跑大概率可通过。

### 方向 2（置信度: 低）
**为 pip install 添加重试机制**。在 Dockerfile 的 `pip install` 命令中增加 `--retries 5 --timeout 300` 参数，提高下载健壮性。但这不能根本解决网络问题，仅能降低偶发超时的影响。

### 方向 3（置信度: 低）
**更换 PyPI 镜像源**。将 `mirrors.aliyun.com` 更换为其他镜像（如 `mirrors.tuna.tsinghua.edu.cn` 或官方 `pypi.org`），但不同镜像在不同 CI 环境中的可达性不同，需实际测试验证。

## 需要进一步确认的点
- 该 CI runner 到 `mirrors.aliyun.com` 的网络稳定性如何（是否为偶发，还是该镜像站对该 runner 持续不可用）
- 是否存在镜像站频率限制（防爬策略）导致大文件下载被中断
- 同一镜像在 x86-64 和 aarch64 架构上的构建是否均失败（日志仅显示 x64 构建）
