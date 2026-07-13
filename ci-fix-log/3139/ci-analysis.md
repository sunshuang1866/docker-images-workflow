# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, Read timed out, pip install

## 根因分析

### 直接错误
```
#12 257.5 ERROR: Exception:
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

下载 `nvidia_cudnn_cu13-9.20.0.48-py3-none-manylinux_2_27_x86_64.whl` (366.2 MB) 时，在 353.4 MB 处发生读超时：

```
#12 257.5      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸  353.4/366.2 MB 23.0 MB/s eta 0:00:01
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-33`（`pip install` 步骤）
- 失败原因: Docker 构建过程中，`pip install` 从阿里云镜像站 `mirrors.aliyun.com` 下载大型 Python 依赖包 `nvidia_cudnn_cu13`（366 MB）时发生网络读超时，导致构建中断

### 与 PR 变更的关联
**与 PR 改动无直接关联**。PR 新增的 Dockerfile 使用与已有 `24.03-lts-sp1` 版本相同的 `pip install -i https://mirrors.aliyun.com/pypi/simple/` 镜像站配置，属于标准模式。失败原因是镜像站网络连接不稳定（下载大包时读超时），是 CI 基础设施/外部依赖问题，非代码缺陷。日志中 npm 解压时出现的 `error` 关键词（如 `audit-error.js`、`error-message.js`）仅为 npm 内部模块的文件名，非实际错误。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。网络超时属于偶发性基础设施问题，大概率重试即可通过。镜像站连接在本次构建中其他包的下载均正常完成，仅在最后一个大文件（366 MB）尾部超时。

### 方向 2（置信度: 低）
若多次重试均在同一位置（相同包的相同下载进度）超时，考虑更换更稳定的 PyPI 镜像源或增加 pip 超时配置（`--timeout` 参数）。

## 需要进一步确认的点
- 检查 CI 构建节点到 `mirrors.aliyun.com` 的网络连通性是否稳定
- 确认其他使用相同镜像源的构建 job 是否也出现类似超时
- 若为该镜像的首次构建（新建 Dockerfile），需确认上游 npm / pip 依赖在运行时均正常可用
