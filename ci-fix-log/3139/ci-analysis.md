# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 阿里云镜像下包超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, Read timed out, pip install, HTTPSConnectionPool

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

前序日志显示超时发生时正在下载 `nvidia-cudnn-cu13` (366.2 MB 的 `.whl`)，下载到 353.4/366.2 MB 时连接中断。

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（`pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/` 步骤）
- 失败原因: pip 从阿里云 PyPI 镜像 (`mirrors.aliyun.com`) 下载大文件（`nvidia-cudnn-cu13`，366 MB）时发生 `ReadTimeoutError`，TCP 连接在传输过程中中断。`npm i` 和 `npm run build` 在同一 RUN 指令链中已完成，失败仅发生在 pip 阶段。

### 与 PR 变更的关联
PR 新增了一个完整的 Dockerfile，其中在 `RUN` 指令（第 28-35 行）中指定 `pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`。此 `requirements.txt` 依赖的 `torch` 间接依赖了体积达 366 MB 的 `nvidia-cudnn-cu13` 包，阿里云镜像在下载该大文件时发生 TCP 读超时。

该失败**与 PR 的代码逻辑无关**——Dockerfile 语法正确、依赖声明正确，属于外部镜像站的网络传输不稳定问题。同样的 Dockerfile 在其他时间或使用其他镜像源重试很可能会成功。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该错误为阿里云镜像站的网络传输超时，属于瞬态基础设施问题。触发 CI 重新构建后，若阿里云镜像恢复稳定，构建可能直接通过。

### 方向 2（置信度: 低）
**换用其他 PyPI 镜像源或官方源**。若阿里云镜像持续不稳定（尤其是对大文件传输），可将 `pip install` 的 `-i` 参数换为清华镜像 (`mirrors.tuna.tsinghua.edu.cn`) 或保留默认官方 PyPI 源。但需注意其他镜像源可能也有类似的稳定性问题，且换源后需重新验证。

### 方向 3（置信度: 低）
**增加 pip 重试机制**。在 `pip install` 命令中添加 `--retries 5 --timeout 120` 等参数，提高对大文件下载的网络容错能力。但这不能从根本上解决源站不稳定问题，只能降低失败概率。

## 需要进一步确认的点
1. 阿里云镜像站 (`mirrors.aliyun.com`) 在 CI 构建时段是否存在已知的网络波动或限流——可通过重试构建来确认是否为瞬态故障。
2. 同一 Dockerfile 中已有的 `22.03-lts-sp4` 和 `24.03-lts-sp1` 版本的构建是否也遇到类似的阿里云镜像超时——若仅 SP4 版本失败，可能是 SP4 基础镜像的网络栈差异。
3. CI 构建节点的网络出站带宽和连接超时配置——若默认超时较短（如 30 秒），下载 366 MB 文件时容易触发。

## 修复验证要求
（无需特殊验证——若采用方向 2 更换镜像源，code-fixer 只需确认新镜像源能正常解析和下载 `nvidia-cudnn-cu13` 等大文件即可。）
