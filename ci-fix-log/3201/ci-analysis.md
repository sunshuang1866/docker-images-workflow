# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 外部仓库大文件下载断连
- 新模式症状关键词: Curl error (18), Transferred a partial file, transfer closed with, dnf install, maca-sdk, eur.openeuler.openatom.cn

## 根因分析

### 直接错误
```
#10 421.4 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 43044896 bytes remaining to read]
#10 803.6 [MIRROR] mcblas-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblas-3.7.0.38-1.aarch64.rpm [transfer closed with 27524468 bytes remaining to read]
#10 836.8 [MIRROR] mcblaslt-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblaslt-3.7.0.38-1.aarch64.rpm [transfer closed with 399936528 bytes remaining to read]
#10 956.6 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 34752742 bytes remaining to read]
#10 956.6 [FAILED] mccl-3.7.0.38-1.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#10 956.6 Error: Error downloading packages:
#10 956.6   mccl-3.7.0.38-1.aarch64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile:13`（`dnf install -y --allowerasing maca-sdk-${ARCH}` 步骤）
- 失败原因: Copr 仓库 `eur.openeuler.openatom.cn` 在传输大体积 RPM 文件（mcblaslt 400MB、mccl 48MB、mcblas 45MB）时反复断连（Curl error 18: 部分传输），dnf 耗尽 10 次重试后下载失败。仅 aarch64 架构的 CI 构建受影响。

### 与 PR 变更的关联
PR 新增的 `maca-sdk` Dockerfile 依赖第三方 Copr 仓库 `eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/` 作为 RPM 安装源。该仓库服务器在服务大文件（单个最大 849 MB，总计 2.4 GB）时不够稳定，连接在传输中途被关闭，导致构建失败。PR 本身的 Dockerfile 逻辑和配置正确，dnf 已配置 `retries=10` 仍无法完成下载。问题根因在上游仓库的可用性，不在 PR 代码变更本身。

额外注意：`EUR.repo` 中 baseurl 使用 `openeuler-24.03_LTS_SP2-$basearch`（SP2），而基础镜像为 `openeuler/openeuler:24.03-lts-sp3`（SP3）。当前不是失败原因，但可能存在运行时兼容性风险。

## 修复方向

### 方向 1（置信度: 中）
在上游 Copr 仓库稳定性无法保证的情况下，改为多阶段构建：先用一个临时阶段（基于相同 openeuler 基础镜像）在本地执行 `dnf download --destdir=/rpms maca-sdk-${ARCH}` 完成下载，然后第二阶段从中 `COPY` 本地缓存的 RPM 包进行安装。这样可以利用 dnf 的缓存机制，即使多次重试失败，前一次成功下载的部分 RPM 也会被保留。

### 方向 2（置信度: 中）
联系上游 Copr 仓库维护者（`ObjectNotFound/maca-sdk`）确认仓库服务器是否有带宽限制、请求频率限制或 CDN 配置问题，从根本上解决大文件传输中断问题。同时可考虑是否有其他镜像源或替代下载渠道（如 MetaX 官方 SDK 下载站）。

### 方向 3（置信度: 低）
在 Dockerfile 中将 dnf 下载策略调整为逐个包单独安装（而非一次性安装所有 58 个包），并增加 `--downloadonly` 预处理步骤，利用 dnf 的 keepcache 保留已成功下载的包，减少单次重试需重新下载的总数据量。

## 需要进一步确认的点
1. 该 Copr 仓库是否仅为 aarch64 架构不稳定，x86_64 构建日志未提供，需确认 x86_64 构建是否单独通过。
2. `EUR.repo` 中 SP2 与基础镜像 SP3 的版本差异是否会在运行时引入不兼容问题，需查阅 MetaX MACA SDK 的 openEuler 兼容性矩阵。
3. 上游 Copr 仓库 `ObjectNotFound/maca-sdk` 的维护状态和稳定性 SLA，确认是否计划长期作为可靠的 RPM 源。
4. `dnf install` 命令中配置了 `retries=10`、`timeout=600`、`minrate=100`、`max_parallel_downloads=4`，但日志中实际构建的 RUN 命令与 PR diff 不一致（diff 中无 `echo` 写入 dnf.conf 的部分），需确认 CI 在构建前是否对 Dockerfile 做了自动改写。

## 修复验证要求
若选择方向 1（多阶段构建缓存本地 RPM），code-fixer 必须：
1. 在本地/CI 环境执行 `dnf download --resolve --destdir=/tmp/rpms maca-sdk-aarch64-3.7.0.38-1`（基于 `EUR.repo` 配置的仓库），验证所有 58 个依赖包可被完整下载。
2. 验证第二阶段 `dnf install --offline /localrpms/*.rpm` 的离线安装方式在 openeuler:24.03-lts-sp3 上可行。
3. 分别验证 x86_64 和 aarch64 两个架构的 Dockerfile 构建。
