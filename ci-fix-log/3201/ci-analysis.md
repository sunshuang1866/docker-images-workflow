# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游RPM仓库大文件传输中断
- 新模式症状关键词: Curl error (18), Transferred a partial file, No more mirrors to try, dnf install, copr

## 根因分析

### 直接错误
```
#10 421.4 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 43044896 bytes remaining to read]
#10 803.6 [MIRROR] mcblas-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblas-3.7.0.38-1.aarch64.rpm [transfer closed with 27524468 bytes remaining to read]
#10 836.8 [MIRROR] mcblaslt-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblaslt-3.7.0.38-1.aarch64.rpm [transfer closed with 399936528 bytes remaining to read]
#10 956.6 [FAILED] mccl-3.7.0.38-1.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#10 956.6 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile:13`（`dnf install -y --allowerasing maca-sdk-${ARCH}` 步骤）
- 失败原因: 上游 COPR 仓库 `eur.openeuler.openatom.cn` 在传输 `mccl`（48 MB）、`mcblas`（45 MB）、`mcblaslt`（400 MB）等大型 RPM 包时，服务器端反复提前关闭 TCP 连接（Curl error 18: partial transfer），尽管 dnf 已配置 `retries=10`、`timeout=600`、`minrate=100`，重试耗尽后所有镜像均告失败。

### 与 PR 变更的关联
PR 新增的文件（Dockerfile、EUR.repo、meta.yml、README.md、image-list.yml 条目）本身在语法和逻辑上没有问题。Docker 构建的前两步（`dnf update` + 安装 gcc/make 等工具链、COPY repo 文件）均成功，表明 Dockerfile 的 shell 语法和基础镜像均正常工作。

失败发生在第三步——从 PR 中 `EUR.repo` 配置的上游 COPR 仓库下载 MACA SDK 的 RPM 依赖包时，仓库服务器在传输大文件（尤其 `mcflashattn` 849 MB、`mcblaslt` 400 MB、`mcfft` 264 MB 等）时反复断开连接。这不是 PR 代码的错误，而是上游仓库的服务端稳定性问题。

## 修复方向

### 方向 1（置信度: 中）
联系 EUR COPR 仓库（`eur.openeuler.openatom.cn`）的维护者，确认 `ObjectNotFound/maca-sdk` 仓库中 `00111760-maca-sdk-aarch64` 批次的大文件 RPM 包是否完整上传且服务端支持断点续传 / Range 请求。若服务端不支持断点续传且频繁断开连接，即使增加 `retries` 也无法解决问题。

### 方向 2（置信度: 低）
若上游仓库短期内无法修复，可考虑在 Dockerfile 中将大文件 RPM 分开单独安装（使用多个 `dnf install` 命令分散下载压力），或为 dnf 增加 `--downloaddir` 配合外部缓存机制手动重试失败的包。但鉴于错误本质是服务端主动关闭连接（非超时），此方向效果有限。

## 需要进一步确认的点
1. 上游 EUR COPR 仓库 `eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/` 在 CI 构建时段（2026-07-17 09:31 UTC）是否正常运行——从浏览器或 `curl -I` 直接访问这些大文件 RPM 的 URL 验证服务端响应是否稳定。
2. `EUR.repo` 中 `baseurl` 指向 `openeuler-24.03_LTS_SP2-$basearch`（SP2），但 Dockerfile 基于 `openeuler:24.03-lts-sp3`（SP3）——确认这是有意为之（MACA SDK 包仅在 SP2 仓库中发布）还是路径配置错误，如果是后者则需要更新为 SP3 路径。
3. 确认同一 PR 的 x86_64（amd64）架构构建是否也遭遇同样的大文件下载中断，或仅 aarch64 仓库受影响。
