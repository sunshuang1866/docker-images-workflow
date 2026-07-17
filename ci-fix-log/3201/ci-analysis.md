# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 外部仓库大文件下载断连
- 新模式症状关键词: Curl error (18), Transferred a partial file, transfer closed with, dnf install, No more mirrors to try, all mirrors were already tried

## 根因分析

### 直接错误
```
#10 421.4 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 43044896 bytes remaining to read]
#10 803.6 [MIRROR] mcblas-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file... [transfer closed with 27524468 bytes remaining to read]
#10 836.8 [MIRROR] mcblaslt-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file... [transfer closed with 399936528 bytes remaining to read]
#10 956.6 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file... [transfer closed with 34752742 bytes remaining to read]
#10 956.6 [FAILED] mccl-3.7.0.38-1.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#10 956.6 Error: Error downloading packages:
#10 956.6   mccl-3.7.0.38-1.aarch64: Cannot download, all mirrors were already tried without success
#10 ERROR: process "/bin/sh -c ... dnf install -y --allowerasing maca-sdk-${ARCH} ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile:13-21`（`dnf install -y --allowerasing maca-sdk-aarch64` 步骤）
- 失败原因: Copr 外部仓库 `eur.openeuler.openatom.cn` 在下载大型 RPM 包（总大小约 2.4 GB，含 mcflashattn 849 MB、mcblaslt 400 MB、mcfft 264 MB 等）时，服务端反复主动中断连接（`transfer closed with XXX bytes remaining to read`），导致 curl 下载未完成即被截断。CI 虽已注入 `retries=10` 和 `timeout=600` 的 dnf 配置，但因服务端持续断连且下载速度极慢（部分包仅 22-24 kB/s），重试耗尽后仍无法完成全部包下载。**此失败与 PR 的 Dockerfile 代码逻辑无关，根因在于上游 Copr 仓库的可用性/稳定性问题。**

### 与 PR 变更的关联
PR 新增了 maca-sdk 镜像的全部文件（Dockerfile、EUR.repo、meta.yml、image-list.yml 条目、README.md）。Dockerfile 本身的构建逻辑正确——COPY 仓库配置文件、dnf install 安装元包，语法和依赖声明均无误。失败的直接原因是 `EUR.repo` 中引用的外部 Copr 仓库（`eur.openeuler.openatom.cn`）在 CI 构建时网络连接不稳定。若该仓库稳定可用，构建应能通过。

## 修复方向

### 方向 1（置信度: 中）
**更换 RPM 包下载源或添加备用镜像**。当前 `EUR.repo` 仅配置了一个 baseurl（`eur.openeuler.openatom.cn`），且 dnf 输出的 "[MIRROR]" 字样表明实际下载时该仓库可能存在多个镜像，但均不可靠。可考虑：
- 确认 Copr 仓库是否提供了其他地理区域的镜像/mirrorlist 地址，添加到 `EUR.repo` 的 `baseurl` 或 `mirrorlist` 配置中
- 联系 maca-sdk 仓库维护者（ObjectNotFound）确认服务端是否存在带宽或连接数限制

### 方向 2（置信度: 低）
**重试触发**。该失败可能是临时性网络波动，直接重新触发 CI 构建有可能通过。日志中已经配置了 `retries=10` 和 `timeout=600`，但在极慢网速下（部分包仅 22 kB/s）仍不够。可在 Dockerfile 中将 `max_parallel_downloads` 降低至 1-2，减少并发连接数以降低服务端断连概率；或将 `timeout` 进一步增大以应对大文件慢速下载场景。

## 需要进一步确认的点
1. **该 Copr 仓库是否持续不可用**：需确认 `eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/` 目前是否可正常访问和下载。如果该仓库已废弃或下架 maca-sdk 制品，则需寻找替代来源。
2. **x86_64 架构是否也失败**：当前日志仅为 aarch64（arm64）构建失败的片段。需确认 x86_64 构建是否因同样原因失败，还是仅 aarch64 仓库有问题。
3. **EUR.repo 中 baseurl 的 SP2/SP3 版本标注**：`EUR.repo` 的 baseurl 写死了 `openeuler-24.03_LTS_SP2`，但 Dockerfile 基础镜像为 `openeuler:24.03-lts-sp3`。需确认这是有意为之（该 Copr 仓库的 SP2 包与 SP3 兼容）还是编排错误。如果是后者，需修正 baseurl 中的 SP 版本号。

## 修复验证要求
若修复方向涉及修改 `EUR.repo` 中的 baseurl 或添加镜像地址，code-fixer 需在提交前验证：
1. 新的下载源确实可达且支持 aarch64 架构的 RPM 包
2. 所有 58 个依赖包在新源中版本一致（均为 `3.7.0.38-1`）
3. 若更换源，执行 `dnf makecache --refresh && dnf download --resolve maca-sdk-aarch64` 确认全部包可成功下载
