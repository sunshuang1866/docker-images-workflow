# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站大文件下载超时
- 新模式症状关键词: ReadTimeoutError, Read timed out, mirrors.aliyun.com, HTTPSConnectionPool, nvidia-cudnn

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5     raise ReadTimeoutError(self._pool, None, "Read timed out.")
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
#12 ERROR: process "/bin/sh -c npm config set registry https://registry.npmmirror.com/ && ... pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ && ..." did not complete successfully: exit code: 2

Downloading nvidia-cudnn-cu13==9.20.0.48 (366.2 MB)
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28`（pip install 步骤）
- 失败原因: `pip install -r backend/requirements.txt` 从 `mirrors.aliyun.com` 下载 `nvidia-cudnn-cu13`（366 MB）时，在已完成 96.5% 的进度后发生 socket 读超时。此为大文件下载过程中的瞬时网络波动，与 PR 代码无关。

### 与 PR 变更的关联
无直接关联。该失败是 CI 构建环境与阿里云镜像站之间的瞬时网络问题。npm install 和 pip install 的前期依赖下载均正常完成（日志显示大量包从 `mirrors.aliyun.com` 成功下载），仅在最后一个超大包 `nvidia-cudnn-cu13`（366 MB）下载接近完成时触发了超时。这是典型的 infra-error，重新触发 CI 大概率会通过。

## 修复方向

### 方向 1（置信度: 高）
**重试即可，无需代码修改。** 该失败是瞬时网络超时，非代码缺陷。直接重新触发 CI 构建，大概率成功。

### 方向 2（置信度: 低）
**为 pip install 添加重试机制。** 可在 pip install 命令后追加 `--retries 5 --timeout 120` 参数，增加下载重试次数和超时容忍度，降低大文件下载失败的几率。但此改动非必须——现有其他同仓库镜像的 Dockerfile 普遍未加此类重试参数，单次超时不足以证明需要额外防御。

> 注意：Dockerfile 中的 npm install 部分 `Error lines` 区域显示的是 `error` 关键词匹配到的 npm 内部文件名（如 `audit-error.js`、`error-message.js`、`errors.js`），并非实际的 npm 构建错误。npm install 和 npm run build 均成功完成。

## 需要进一步确认的点
- 确认重新触发 CI 后是否仍然超时。若连续多次在同一包上超时，可能是 `mirrors.aliyun.com` 对该特定包的代理存在稳定性问题，届时需考虑换用其他镜像源（如清华源 `pypi.tuna.tsinghua.edu.cn`）。
- 注意当前 Dockerfile 中存在潜在问题：`BUILDARCH` 是 BuildKit 预定义变量（参考知识库模式09），在 RUN 中对其重新赋值不会生效。虽然此次失败非由此导致，但若后续 Node.js 下载步骤在 arm64 上出问题，这可能是根因。
