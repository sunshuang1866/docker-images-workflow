# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站下载超时
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
```
下载 `nvidia_cudnn_cu13-9.20.0.48`（366.2 MB）到约 353.4 MB 时 TCP 连接读超时。

### 根因定位
- 失败位置: Dockerfile:28 — `pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/` 步骤
- 失败原因: pip 从阿里云 PyPI 镜像下载 `nvidia-cudnn-cu13`（366.2 MB 大文件）时网络读超时，导致整个 `pip install` 步骤退出码 2，Docker 构建失败。

### 与 PR 变更的关联
**无关**。PR 变更仅新增了一个 Dockerfile 及配套的 README、image-info.yml、meta.yml 条目，均为常规的新 OS 版本适配。失败原因是 CI 构建环境中 `mirrors.aliyun.com` 镜像站对大型 PyPI 包的下载连接不稳定，与 PR 代码改动无关。

> 注：Dockerfile 第 28 行使用了 `BUILDARCH` 变量（与已知模式09「BuildKit 预定义变量 BUILDARCH 冲突」一致），但本次失败并非由该问题触发（Node.js 下载及 npm 构建均成功完成）。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，**Code Fixer 无需修改代码**。可考虑以下操作之一（需人工判断）：
- 重试 CI 构建（网络波动可能是临时的）
- 将 PyPI 镜像从 `mirrors.aliyun.com` 更换为更稳定的镜像源（如 `pypi.tuna.tsinghua.edu.cn` 或上游 `pypi.org`）
- 对超大包（如 `nvidia-cudnn-cu13` 366 MB）通过 `--default-timeout` 或环境变量 `PIP_DEFAULT_TIMEOUT` 增大 pip 下载超时阈值

### 方向 2（置信度: 中，次要问题）
Dockerfile 第 17 行使用了 BuildKit 预定义变量名 `BUILDARCH`，与已知模式09冲突。虽本次未触发，但在不同环境（尤其是 BuildKit 版本升级后）可能引发架构字符串错误。建议后续将 `BUILDARCH` 改为自定义名称（如 `MY_ARCH`），以规避潜在风险。

## 需要进一步确认的点
无。日志明确显示网络读超时错误，根因清晰。如重复出现，需排查 CI 构建节点到 `mirrors.aliyun.com` 的网络链路质量。
