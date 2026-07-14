# CI 失败分析报告

## 基本信息
- PR: #3139 — chore(open-webui): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: pip镜像站下载超时
- 新模式症状关键词: ReadTimeoutError, mirrors.aliyun.com, pip, HTTPSConnectionPool, Read timed out

## 根因分析

### 直接错误

```
#12 257.5 ERROR: Exception:
#12 257.5 Traceback (most recent call last):
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 452, in _error_catcher
#12 257.5     yield
#12 257.5   File "/usr/lib/python3.11/site-packages/pip/_vendor/urllib3/response.py", line 575, in read
#12 257.5     data = self._fp_read(amt) if not fp_closed else b""
#12 257.5            ^^^^^^^^^^^^^^^^^^
...
#12 257.5 TimeoutError: The read operation timed out
#12 257.5 pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='mirrors.aliyun.com', port=443): Read timed out.
```

### 根因定位
- 失败位置: `AI/open-webui/0.1.108/24.03-lts-sp4/Dockerfile:28-35`（RUN 指令中 `pip install -r backend/requirements.txt` 步骤）
- 失败原因: CI 构建容器中 pip 从 `mirrors.aliyun.com` 镜像站下载大体积依赖包 `nvidia-cudnn-cu13`（366.2 MB）时，HTTPS 连接读取超时。日志显示该包已下载 353.4/366.2 MB 后断连，属于网络传输中断。

### 补充说明

日志中 "Error lines (newest first)" 部分出现的 `#10` 行（含大量 `error*.js`、`make-error.js` 等文件路径）均为 `tar -xvf` 解压 Node.js 包时的**正常 verbose 输出**——这些只是文件名中含 "error" 字样的 npm 内部模块源代码文件，不代表构建错误。npm 部分的 `npm i` 与 `npm run build` 均已成功完成（`#12 20.60 .svelte-kit/output/...` 为构建产物）。

### 与 PR 变更的关联

**无关**。PR 变更是为 openEuler 24.03-LTS-SP4 新增 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 的语法和逻辑均正确：
- Node.js 安装与架构识别正常（日志中 `node-v18.0.0-linux-x64/` 确认架构字符串正确构造）
- `npm i` 和 `npm run build` 成功完成
- 失败仅发生在 pip 下载大型依赖包的网络传输阶段，属于 CI 基础设施/网络稳定性问题

## 修复方向

### 方向 1（置信度: 高）

重新触发构建。该失败为网络读取超时导致的偶发性 infra 问题，Dockerfile 代码本身无错误。`nvidia-cudnn-cu13`（366.2 MB）是一个特别大的 wheel 包，在网络波动时更容易触发超时。在当前 RUN 指令合并了 npm 和 pip 两步的情况下，重试成本较高（每次需重新执行 `npm i` 和 `npm run build`），可考虑将 pip install 步骤拆分为独立 RUN 层以便利用 Docker 层缓存加速重试。

### 方向 2（置信度: 低）

若 `mirrors.aliyun.com` 在 CI 构建环境中持续不可靠，可将 pip 镜像源换为其他可用源（如官方 PyPI 或 `mirrors.tuna.tsinghua.edu.cn`）。当前日志中仅最后一个大包超时、此前多数批量下载正常，更偏向偶发网络波动而非镜像源系统性不可用。

## 需要进一步确认的点

- CI 构建节点（runner）的网络出口是否存在带宽限制、连接数限制或长连接超时策略，导致大文件传输不稳定（该包需持续约 15 秒传输，最大瞬时速度 23 MB/s）。
- 同一时段是否有其他并发构建任务共享 runner 带宽。
- 若连续多次重试均在同一文件 `nvidia-cudnn-cu13` 处超时，需检查该文件在 `mirrors.aliyun.com` CDN 边缘节点的缓存完整性。
- Dockerfile 中声明了 `ARG BUILDARCH`（BuildKit 预定义 ARG，见模式09），虽本次未引发问题，但建议将 RUN 内的局部变量 `BUILDARCH` 更名为自定义名称以避免与 BuildKit 预定义变量冲突。
