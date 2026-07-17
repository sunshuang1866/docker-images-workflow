# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Copr仓库大文件下载中断
- 新模式症状关键词: Curl error (18), Transferred a partial file, No more mirrors to try, maca-sdk, eur.openeuler.openatom.cn

## 根因分析

### 直接错误
```
#10 421.4 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 43044896 bytes remaining to read]
#10 803.6 [MIRROR] mcblas-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblas-3.7.0.38-1.aarch64.rpm [transfer closed with 27524468 bytes remaining to read]
#10 836.8 [MIRROR] mcblaslt-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblaslt-3.7.0.38-1.aarch64.rpm [transfer closed with 399936528 bytes remaining to read]
#10 956.6 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 34752742 bytes remaining to read]
#10 956.6 [FAILED] mccl-3.7.0.38-1.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#10 956.6 Error: Error downloading packages:
#10 ERROR: process "... did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile:13-21`（RUN dnf install maca-sdk 步骤）
- 失败原因: 外部 COPR 仓库 `eur.openeuler.openatom.cn` 在向 aarch64 CI 节点传输大型 RPM 包（mccl ~48MB、mcblas ~45MB、mcblaslt ~400MB）时反复中断连接（Curl error 18：传输未完成即关闭），dnf 在耗尽所有重试（10 次）后因"无更多镜像可尝试"而失败。

### 与 PR 变更的关联
**此次 PR 变更未直接触发该失败。** PR 新增了 maca-sdk 的 Dockerfile、EUR.repo、meta.yml 及 README.md，Dockerfile 中的 RUN 指令逻辑本身无错误——ARCH 变量推导正确（`linux/arm64` → `aarch64`），dnf 配置参数（`minrate=100`、`timeout=600`、`retries=10`）均合法。失败是由远端 RPM 仓库的**网络服务质量问题**导致，与 PR 的代码变更无关。

**额外发现：PR diff 与 CI 日志存在差异。** PR diff 中 Dockerfile 的第二个 RUN 指令仅包含 ARCH 推导和 dnf 安装步骤，而 CI 日志中的实际 RUN 指令前置了 `echo -e "minrate=100\ntimeout=600\nretries=10\nmax_parallel_downloads=4" >> /etc/dnf/dnf.conf`。这表明 CI 实际构建的 Dockerfile 内容与 diff 所示不同，diff 可能已被截断，或存在额外的上游注入。该差异不影响根因判定，但需在后续确认文件实际内容。

## 修复方向

### 方向 1（置信度: 高）
该失败属于 `infra-error`——外部 RPM 仓库在上传/分发大型 aarch64 包时稳定性不足。**Code Fixer 无需修改 Dockerfile 或 PR 代码**。建议将问题反馈给 `eur.openeuler.openatom.cn` 仓库维护方，或等待 COPR 服务恢复后重新触发 CI。如果需立即绕过，可考虑：
- 将 maca-sdk 所需的 RPM 包预先下载并托管到 CI 可稳定访问的内网镜像站，修改 `EUR.repo` 的 `baseurl` 指向该镜像站
- 在 Dockerfile 中将 `max_parallel_downloads` 从 4 降为 1，减少并发连接对远端服务器的压力

### 方向 2（置信度: 低）
如果远端仓库问题持续不可用，可考虑将 maca-sdk RPM 包打入 Dockerfile 所在目录，通过 `COPY` + 本地 `dnf install` 的方式绕过远程下载。但这需要预先获取所有 58 个依赖 RPM 包（总计 2.4GB），维护成本高。

## 需要进一步确认的点
1. **确认 x86_64 架构的构建结果**：当前日志仅展示了 aarch64 构建失败，未提供 x86_64 的日志。需确认 x86_64 是否同样因下载中断而失败，还是仅 aarch64 受影响。
2. **确认 PR diff 与实际 Dockerfile 的一致性**：CI 日志中 RUN 指令比 diff 多了 dnf.conf 配置行，需要确认实际提交的 `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile` 内容。
3. **确认 COPR 仓库稳定性**：`eur.openeuler.openatom.cn` 仓库中 aarch64 下的大型包（mcblaslt 400MB、mcfft 264MB、mcgpufort 273MB 等）是否存在普遍的传输中断问题，需要与仓库维护方确认。

## 修复验证要求
**不适用**。本次失败为 infra-error，无需 Code Fixer 修改代码。若方向 1 中的"换源"方案被采纳，则 code-fixer 需验证新镜像站可正常提供全部 58 个 aarch64 RPM 包，且 `dnf install maca-sdk-aarch64` 可完整成功（包括所有大型子包如 mcblaslt、mcfft、mccl 等）。
