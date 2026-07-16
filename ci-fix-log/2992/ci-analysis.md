# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: dnf镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤，builder 阶段 #8）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像在 CI 构建环境中反复出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），dnf 重试耗尽所有可用镜像后，`gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34 MB）及 `gcc-gfortran`、`guile`、`glibc-devel` 等多个包下载失败，导致整个依赖安装步骤返回 exit code 1。

### 与 PR 变更的关联

**与 PR 代码变更无关。** 本次 PR 纯属新增 openEuler 24.03-LTS-SP4 的 multiwfn Dockerfile 及配套元数据（README.md、image-info.yml、meta.yml）。Dockerfile 中 `dnf install` 的包列表（git、gcc、gcc-c++、gcc-gfortran、make、openblas-devel、lapack-devel）均为 openEuler 24.03-LTS-SP4 官方仓库的标准包，语法正确、包名有效。失败根因是 CI 构建节点与 openEuler 24.03-LTS-SP4 软件源镜像之间的 HTTP/2 传输层不稳定——两个并行的 dnf install 阶段（builder 的 #8 和 runtime 的 #7）均遭遇相同的 Curl error (92)。该问题属于仓库镜像侧或 CI 网络层的瞬时故障。

值得注意的是，runtime 阶段（#7，仅需 32 个包/208 MB）在经历个别包的 HTTP/2 错误后，多数包下载成功，最终状态为 `CANCELED`（因 builder 阶段先失败）；而 builder 阶段（#8，需要 157 个包/261 MB）因包数量多、总体积大，gcc 主包（34 MB）下载失败耗尽所有镜像重试。

## 修复方向

### 方向 1（置信度: 中）
**重试触发。** 本失败为 CI 基础设施/镜像源瞬时网络故障，Dockerfile 本身无问题。直接对 PR 重新触发 CI 构建（re-run），利用 dnf 自带的重试和镜像切换机制，在镜像源恢复稳定后大概率能通过。

### 方向 2（置信度: 低）
**调整 dnf 重试/超时参数。** 如果重试后仍持续失败，可在 Dockerfile 的 `dnf install` 前增加 dnf 配置，提高重试次数和超时容忍度（如 `dnf install --setopt=retries=10 --setopt=timeout=300 ...`），缓解 HTTP/2 流短暂中断导致的失败。但此方案不解决根本的网络问题。

### 方向 3（置信度: 低）
**更换镜像源。** 如果特定镜像（`repo.****.org`）持续不稳定，可考虑在 Dockerfile 中预先替换 dnf 的 baseurl 为更稳定的镜像站。但这通常不是单个 Dockerfile 应做的事，更应在 CI runner 环境或基础镜像层面解决。

## 需要进一步确认的点

1. **确认镜像源健康状况**：`repo.****.org`（被掩码的仓库地址）在 CI 失败时段的 HTTP/2 服务是否正常。可以手动 `curl --http2` 测试该仓库的连通性和稳定性。
2. **确认是否所有 SP4 构建均受影响**：同一 CI 时段是否有其他基于 openEuler 24.03-LTS-SP4 的镜像构建也出现同样错误，以区分是特定镜像源问题还是全局网络问题。
3. **确认 arm64 架构构建结果**：PR diff 中声明该镜像支持 `amd64, arm64`，但日志仅显示 x86_64 构建。需确认 aarch64 构建 job 的结果，可能 arm64 侧没有此问题（不同 runner 网络环境不同）。
