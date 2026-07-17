# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 外部仓库大文件下载中断
- 新模式症状关键词: Curl error (18), Transferred a partial file, No more mirrors to try, dnf install, COPR

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
- 失败原因: 外部 COPR 仓库 `eur.openeuler.openatom.cn` 在传输大型 RPM 包（mccl ~48MB、mcblas ~45MB、mcblaslt ~400MB）时，服务端多次在传输未完成时主动关闭连接，导致 curl 报 `Curl error (18): Transferred a partial file`。尽管 Dockerfile 已配置 `retries=10` 和 `timeout=600`，服务器持续在传输中途断开连接，所有重试均耗尽后 dnf 失败。

### 与 PR 变更的关联

**与 PR 改动有一定关联，但非代码逻辑错误**。PR 新增了 Dockerfile，其中：

1. `EUR.repo` 指向的 COPR 仓库路径为 `openeuler-24.03_LTS_SP2-$basearch/`（SP2），但 Dockerfile 基础镜像为 `openeuler:24.03-lts-sp3`（SP3），存在 SP2/SP3 版本不一致（即使下载成功也可能引发后续兼容性问题）。
2. COPR 仓库 URL 中包含 `ObjectNotFound` 用户空间路径，该名称暗示该 COPR 项目可能未正确发布或存在访问限制。
3. 下载总大小高达 2.4 GB（含多个 100MB+、甚至 800MB+ 的包），在 CI 受限网络环境下极易因传输中断而失败。

但直接失败原因是外部仓库的服务端连接稳定性问题，Dockerfile 语法和构建逻辑本身没有错误（case 语句正确地将 `TARGETPLATFORM=linux/arm64` 解析为 `aarch64`）。

## 修复方向

### 方向 1（置信度: 中）
**确认 COPR 仓库可用性并修正 SP2/SP3 不一致**。检查 `eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/` 是否确实为公开可用的 maca-sdk RPM 仓库，并确认 `openeuler-24.03_LTS_SP2-aarch64/` 路径是否对应当前 3.7.0.38 版本的制品。如果该 COPR 项目存在问题（如 `ObjectNotFound` 暗示），需联系仓库维护者确认正确的仓库地址。同时，如果上游确实有对应 SP3 的制品路径，应将 `EUR.repo` 中的 SP2 修正为 SP3（即 `openeuler-24.03_LTS_SP3-$basearch/`）。

### 方向 2（置信度: 低）
**提高下载容错或切换下载源**。可尝试将 `minrate` 设为 0 或移除该限制（当前 `minrate=100` 可能导致慢速连接被中断），或增加更多重试次数。如果 COPR 仓库持续不稳定，考虑在 Dockerfile 中使用 `wget` 或 `curl` 分步下载各个 RPM 包并增加断点续传能力，而非依赖 dnf 单次重试机制。或者将大型 RPM 包的上游源替换为更稳定的镜像。

## 需要进一步确认的点

1. **COPR 仓库地址是否正确**：`eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/` 中的 `ObjectNotFound` 是否为合法的 COPR 用户名（如 openEuler 的 openatom 实例下的用户），还是表示仓库状态异常。需确认该地址在浏览器或非 CI 环境下能否正常访问和下载。

2. **SP2 vs SP3 版本对齐**：EUR.repo 的 baseurl 使用 `openeuler-24.03_LTS_SP2`，但 Dockerfile 基于 `openeuler:24.03-lts-sp3`。需确认上游 COPR 仓库是否存在 `openeuler-24.03_LTS_SP3` 对应的制品路径，以及这两个版本的包是否 ABI 兼容。

3. **是否只在 aarch64 上失败**：当前日志仅展示 arm64 构建失败。需确认 x86_64（amd64）构建是否也会遇到同样的下载中断问题，或仅 aarch64 通道存在该网络故障。

4. **CI 网络出口限制**：需确认 CI 构建节点（`ecs-build-docker-aarch64-*`）是否有对该 COPR 仓库的带宽或连接限制，导致大文件传输被强制中断。

## 修复验证要求

1. **验证 COPR 仓库可访问性**：code-fixer 必须在修复前从 CI 外网环境使用 `curl -I` 和 `dnf download` 测试 `eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/` 路径下 `mccl-3.7.0.38-1.aarch64.rpm` 等包是否可完整下载。

2. **验证 SP2/SP3 版本对齐**：如需修正 `EUR.repo` 中的 SP2→SP3，必须先确认上游 COPR 仓库确实存在 `openeuler-24.03_LTS_SP3-aarch64/` 路径及其制品，否则修正后仍会失败。
