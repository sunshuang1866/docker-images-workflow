# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM大文件下载中断
- 新模式症状关键词: Curl error (18), Transferred a partial file, No more mirrors to try, COPR, transfer closed

## 根因分析

### 直接错误
```
#10 421.4 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 43044896 bytes remaining to read]
#10 803.6 [MIRROR] mcblas-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblas-3.7.0.38-1.aarch64.rpm [transfer closed with 27524468 bytes remaining to read]
#10 836.8 [MIRROR] mcblaslt-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblaslt-3.7.0.38-1.aarch64.rpm [transfer closed with 399936528 bytes remaining to read]
#10 956.6 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 34752742 bytes remaining to read]
#10 956.6 [FAILED] mccl-3.7.0.38-1.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#10 956.6 Error: Error downloading packages:
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile:13-21`（`dnf install maca-sdk-${ARCH}` 步骤）
- 失败原因: COPR 仓库 `eur.openeuler.openatom.cn` 在传输大文件 RPM 包时频繁中断连接（Curl error 18: transfer closed with bytes remaining），涉及包包括 `mccl`（48MB）、`mcblas`（45MB）、`mcblaslt`（400MB）等。总下载量达 2.4 GB，其中 `mcflashattn`（849MB）、`mcfft`（264MB）、`mxgpu_llvm`（225MB）等超大包尚未开始下载。dnf 在 10 次重试后所有大型包均下载失败，导致安装步骤整体失败。

### 与 PR 变更的关联
PR 新增了 maca-sdk 镜像的 Dockerfile 和 EUR.repo 仓库配置。失败由 Dockerfile 中 `dnf install maca-sdk-${ARCH}` 步骤触发，但**根因不是 PR 代码错误**，而是 COPR 上游仓库服务器在传输大文件时连接不稳定。PR 的 Dockerfile 和 repo 配置本身语义正确——dnf 成功解析了 58 个包的依赖关系（全部找到），小型包（如 commonlib 66KB、macainfo 18KB）均下载成功，只有大文件（>40MB）因传输中断而失败。

## 修复方向

### 方向 1（置信度: 高）
**将 RPM 大文件下载策略从单次 dnf install 改为分批下载 + 逐个重试**：
- 当前默认 `max_parallel_downloads=4` 导致 4 个大文件并发下载，可能加剧服务器侧连接中断。将 `max_parallel_downloads` 降为 1，串行下载可降低并发中断概率。
- 将 `minrate` 从 100 字节/秒适当提高（如 1024），避免极低速连接占用过长时间后才判定失败。
- 在 `dnf install` 失败后增加额外重试循环（`for i in $(seq 1 5); do dnf install -y --allowerasing maca-sdk-${ARCH} && break; done`），因为 dnf 内部重试不会跨越整个安装事务（已下载缓存的包在重试时无需重新下载）。

### 方向 2（置信度: 中）
**增加 dnf 超时时间以容忍更长的下载间歇**：将 `timeout` 从 600 秒（10 分钟）提升到 1800 秒（30 分钟）。日志显示 `mccl` 首次失败在 421 秒、第二次失败在 956 秒——说明单个大文件下载可持续数分钟，但在连接中断后 dnf 等待重试的时间窗内可能因 timeout 限制而整体失败。更长的超时可让 dnf 有更多时间等待镜像响应。

### 方向 3（置信度: 低）
**排查 COPR 仓库 URL 中的 OS 版本不匹配**：EUR.repo 中 baseurl 路径包含 `openeuler-24.03_LTS_SP2-$basearch`，但基础镜像是 `openeuler:24.03-lts-sp3`。虽然 dnf 在当前仓库中成功找到了所有依赖（说明 SP2 仓库的包对 SP3 兼容），但不排除部分大型包在该路径下的 CDN/镜像节点存在稳定性差异。可向上游确认是否应使用 SP3 专用路径。

## 需要进一步确认的点
1. COPR 仓库 `eur.openeuler.openatom.cn` 的当前健康状态——该仓库是否对 CI 环境的 IP 段存在限速或连接数限制。
2. 该 COPR 仓库是否为 maca-sdk 3.7.0.38 的唯一可用源。若有备用镜像站地址，可同时配置多个 baseurl 以增加容错。
3. 失败仅出现在 aarch64 架构（日志中 TARGETPLATFORM 为 `linux/arm64`），需确认 x86_64 架构构建是否同样会触发此问题（可能因包体积差异而不同）。
4. EUR.repo 中 baseurl 的 `openeuler-24.03_LTS_SP2` 与基础镜像 `24.03-lts-sp3` 的版本不一致是否为有意为之，以及是否存在对应的 SP3 仓库路径。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本失败不涉及对外部源文件的正则 patch。）
