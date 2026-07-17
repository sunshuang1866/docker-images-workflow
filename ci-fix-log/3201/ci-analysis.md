# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 外部仓库下载超时
- 新模式症状关键词: Curl error (28), Timeout was reached, Operation too slow, Less than 1000 bytes/sec, No more mirrors to try, COPR, eur.openeuler.openatom.cn

## 根因分析

### 直接错误
```
#10 558.8 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 44151766 bytes remaining to read]
#10 692.4 [MIRROR] mcblaslt-3.7.0.38-1.aarch64.rpm: Curl error (28): Timeout was reached for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblaslt-3.7.0.38-1.aarch64.rpm [Operation too slow. Less than 1000 bytes/sec transferred the last 30 seconds]
#10 728.4 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (28): Timeout was reached ...
#10 1061.7 [MIRROR] mcblas-3.7.0.38-1.aarch64.rpm: Curl error (28): Timeout was reached ...
#10 1061.7 [FAILED] mcblas-3.7.0.38-1.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#10 1061.7 Error: Error downloading packages:
#10 1061.7   mcblas-3.7.0.38-1.aarch64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile:13-20`（`RUN dnf install -y --allowerasing maca-sdk-${ARCH}`）
- 失败原因: COPR 仓库 `eur.openeuler.openatom.cn` 对 aarch64 架构的大型 RPM 包下载速度极低（<1KB/s 持续超过 30 秒即触发 curl 超时），58 个依赖包总下载量 2.4GB，其中 `mcblaslt`（400MB）、`mcfft`（264MB）、`mxgpu_llvm`（225MB）等大包无法在 dnf 默认超时内完成下载。日志显示该仓库整体下载速率仅约 20-30KB/s，对百 MB 级文件完全不切实际。

### 与 PR 变更的关联
PR 新增了 maca-sdk 镜像的 Dockerfile 及配套文件，Dockerfile 本身逻辑正确（架构判断、软件包安装命令均无误）。失败完全由第三方 COPR 仓库的下载速度/可用性导致，与 PR 代码质量无关。但该仓库作为 maca-sdk 的唯一下载源，其网络状况直接影响此镜像能否构建成功。

另外，`EUR.repo` 中 `baseurl` 路径包含 `openeuler-24.03_LTS_SP2`（SP2），而基础镜像为 `openeuler:24.03-lts-sp3`（SP3），存在版本不一致。虽不直接导致此次网络超时失败，但可能引发后续包兼容性问题。

## 修复方向

### 方向 1（置信度: 高）
在 `dnf install` 命令中添加超时和重试参数，提高下载容忍度。当前 dnf/curl 默认在单次传输持续低于 1KB/s 超过 30 秒即判定超时。可配置 dnf 的 `minrate`、`timeout` 和 `retries` 参数，例如通过 `/etc/dnf/dnf.conf` 设置 `minrate=100`（降低最低速率阈值）、`timeout=600`（延长超时）、`retries=10`（增加重试次数）。同时可考虑在 `dnf install` 前加入 `echo "minrate=100\ntimeout=600\nretries=10" >> /etc/dnf/dnf.conf`。

### 方向 2（置信度: 中）
若 COPR 仓库持续不稳定，可尝试寻找 maca-sdk 的备用镜像源或使用本地缓存方案。例如在 CI 构建环境中预先将 RPM 包下载到本地 HTTP 服务器或对象存储，然后在 Dockerfile 中使用本地源。但这需要 CI 基础设施配合，超出代码修改范围。

### 方向 3（置信度: 低）
修正 `EUR.repo` 中 `baseurl` 的 openEuler 版本从 `SP2` 改为 `SP3`，确保与基础镜像版本一致。不过这需要确认上游 COPR 仓库是否提供了 `openeuler-24.03_LTS_SP3` 路径的构建产物。目前日志中下载的包来自 SP2 路径，SP3 路径可能不存在。

## 需要进一步确认的点
1. COPR 仓库 `eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/` 是否提供了 `openeuler-24.03_LTS_SP3-aarch64/` 路径的 RPM 包？若 SP3 路径存在且下载速度更快，只需修正 `EUR.repo` 中的 `baseurl`。
2. 在非 CI 网络环境（如本地开发机）下，从同一 COPR 仓库下载这些大包的速度是否也如此缓慢？这有助于区分是 COPR 服务器本身限速还是 CI 出口带宽受限。
3. `EUR.repo` 中 SP2 的仓库是否与 SP3 基础镜像存在 ABI 兼容性问题？即使下载成功，运行时也可能出现符号不匹配。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本次失败不涉及正则匹配外部源文件）
