# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 阿里云镜像站下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, Read timed out, pip install, nvidia-cudnn

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
#12 257.5   ...
#12 257.5 TimeoutError: The read operation timed out
...
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（`pip install -r backend/requirements.txt` 步骤）
- 失败原因: 在通过阿里云 PyPI 镜像站（`mirrors.aliyun.com`）安装依赖时，下载大体积包 `nvidia-cudnn-cu13==9.20.0.48`（366.2 MB）至 353.4/366.2 MB（约 96%）处发生 Socket 读取超时，导致 pip 依赖解析阶段失败。

### 分析说明

npm 构建阶段（`npm i && npm run build`）已成功完成，失败发生在后续的 pip install 阶段。日志显示在超时前大量 Python 包已成功从 `mirrors.aliyun.com` 下载完成（见 Build tail 中数十个包的成功下载记录），仅在大文件 `nvidia-cudnn-cu13` 接近下载完成时触发超时。这属于网络层面的读超时异常，与 Dockerfile 代码逻辑或依赖版本声明无关。

### 与 PR 变更的关联

PR 变更的 Dockerfile（`AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile`）沿用了同一应用其他 os-version 变体（`22.03-lts-sp4`、`24.03-lts-sp1`）的 pip 镜像站配置（`https://mirrors.aliyun.com/pypi/simple/`），未引入新的代码逻辑问题。失败是 CI 构建环境与阿里云镜像站之间的网络波动所致，与 PR 本身的内容无直接代码缺陷关联。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**：该超时为网络波动导致的一次性失败（大文件下载接近完成时中断），后续 CI 重试可能自动恢复。建议先触发一次重跑，观察是否通过。

### 方向 2（置信度: 低）
**换用其他镜像站**：若 `mirrors.aliyun.com` 对大文件下载持续不稳定，可将 pip 安装的镜像站更换为其他源（如 `https://pypi.tuna.tsinghua.edu.cn/simple/` 或 `https://repo.huaweicloud.com/repository/pypi/simple/`），降低大体积包下载超时风险。

### 方向 3（置信度: 低）
**增加 pip 超时重试机制**：在 pip install 命令中增加 `--timeout` 和 `--retries` 参数（如 `pip install --timeout 120 --retries 5 ...`），提高对大文件下载的网络容忍度。但需注意这会增加构建时间。

## 需要进一步确认的点

- 该超时是否为一次性的网络波动，还是 `mirrors.aliyun.com` 对于超大 PyPI 包（>300MB）存在持续的服务端限速/断开策略。
- 同样使用 `mirrors.aliyun.com` 的 `24.03-lts-sp1` 和 `22.03-lts-sp4` 变体是否也出现过类似超时（用于判断是镜像站普适性问题还是本次 CI 环境的临时网络问题）。
- `nvidia-cudnn-cu13==9.20.0.48` 是否可替换为更小的本地缓存版本或以其他方式获取（避免依赖远程大文件下载）。
