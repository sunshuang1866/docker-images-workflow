# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 第三方仓库下载超时
- 新模式症状关键词: Curl error (28), Timeout was reached, Operation too slow, Curl error (18), Transferred a partial file, eur.openeuler.openatom.cn

## 根因分析

### 直接错误
```
#10 558.8 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (18): Transferred a partial file for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [transfer closed with 44151766 bytes remaining to read]
#10 692.4 [MIRROR] mcblaslt-3.7.0.38-1.aarch64.rpm: Curl error (28): Timeout was reached for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblaslt-3.7.0.38-1.aarch64.rpm [Operation too slow. Less than 1000 bytes/sec transferred the last 30 seconds]
#10 728.4 [MIRROR] mccl-3.7.0.38-1.aarch64.rpm: Curl error (28): Timeout was reached for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mccl-3.7.0.38-1.aarch64.rpm [Operation too slow. Less than 1000 bytes/sec transferred the last 30 seconds]
#10 1061.7 [MIRROR] mcblas-3.7.0.38-1.aarch64.rpm: Curl error (28): Timeout was reached for https://eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/openeuler-24.03_LTS_SP2-aarch64/00111760-maca-sdk-aarch64/mcblas-3.7.0.38-1.aarch64.rpm [Operation too slow. Less than 1000 bytes/sec transferred the last 30 seconds]
#10 1061.7 [FAILED] mcblas-3.7.0.38-1.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#10 1061.7 Error: Error downloading packages:
#10 ERROR: process "/bin/sh -c ARCH=..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile:13`（`dnf install -y --allowerasing maca-sdk-${ARCH}` 步骤）
- 失败原因: CI 构建环境在 aarch64 runner 上从 `eur.openeuler.openatom.cn`（EUR/Copr 仓库）下载 MACA SDK 组件 RPM 包时，多个大型包（mcblaslt 400MB、mcfft 264MB、mccl 48MB、mcblas 45MB，总下载量 2.4 GB）出现网络超时（Curl error 28）和传输中断（Curl error 18），最终 `mcblas-3.7.0.38-1.aarch64.rpm` 在所有镜像尝试失败后，dnf 报错退出。

### 与 PR 变更的关联
PR 新增了 `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile`，其 `dnf install` 步骤依赖 EUR Copr 仓库（`eur.openeuler.openatom.cn`）提供的 MACA SDK RPM 包。Dockerfile 和仓库配置文件本身语法正确，shell case 语句也正确将 `TARGETPLATFORM=linux/arm64` 解析为 `aarch64`。失败完全由第三方仓库的网络传输质量导致，与 Dockerfile 编写逻辑无直接关联。

额外注意点：`EUR.repo` 中 baseurl 使用的是 `openeuler-24.03_LTS_SP2-$basearch` 路径，但 Dockerfile 基础镜像为 `openeuler/openeuler:24.03-lts-sp3`（SP3），而 repo 路径指向 SP2。当前失败阶段网络错误掩盖了此版本错配问题，但如果后续网络恢复后包依赖与 SP3 基础系统不兼容，可能会引发二次失败。

## 修复方向

### 方向 1（置信度: 中）
**更换下载源或添加重试机制**。EUR Copr 仓库对大型文件（>100MB）的传输稳定性不足。可尝试：
- 在 `dnf install` 命令中添加 `--retries 5` 提高下载容忍度
- 在 `dnf` 配置中增加超时时间（`timeout`、`minrate` 等参数）
- 调查 MACA SDK 是否有其他官方镜像源或国内镜像可供替代

### 方向 2（置信度: 低）
**修正 EUR.repo 中的 openEuler 版本号**。当前 `EUR.repo` 引用 SP2 路径（`openeuler-24.03_LTS_SP2`），而 Dockerfile 基于 SP3 镜像构建。如果 MACA SDK 针对 SP3 发布了对应的 repo 路径，应切换为 SP3 对应的仓库（如 `openeuler-24.03_LTS_SP3-$basearch`），以减少潜在的包依赖冲突。

## 需要进一步确认的点
1. EUR Copr 仓库（`eur.openeuler.openatom.cn`）对 CI runner 网络是否确实可达但带宽受限？需确认是否 runner 的出口带宽或防火墙规则限制了大文件下载。
2. 该仓库是否有 SP3 版本的 repo 路径？当前 repo 指向 SP2，而镜像基座是 SP3，存在版本错配风险。
3. `mxgpu_llvm`（225MB）、`mcflashattn`（849MB）、`mcfft`（264MB）等超大型包的下载在日志中未出现（可能尚未轮到它们下载即已失败），网络恢复后这些包也可能触发同样的超时问题。
4. 需要确认上游 MACA SDK 包是否支持直接 wget/curl 预下载到构建上下文内，通过 `COPY` 方式绕过 dnf 的网络依赖。

## 修复验证要求
无需特殊验证。若选择修复方向 2（切换 SP2 → SP3 路径），需先确认 `eur.openeuler.openatom.cn` 上是否存在 `openeuler-24.03_LTS_SP3-aarch64` 对应的仓库目录及 RPM 包。
