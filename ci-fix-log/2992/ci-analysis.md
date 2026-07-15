# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: `Curl error (92)`, `Stream error in the HTTP/2 framing layer`, `INTERNAL_ERROR (err 2)`, `No more mirrors to try`

## 根因分析

### 直接错误
```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的官方 RPM 软件仓库（`repo.****.org`）在本次 CI 构建期间出现 HTTP/2 连接异常，多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc 等）下载过程遭遇 `Curl error (92)`——HTTP/2 流被非正常关闭（`INTERNAL_ERROR`），dnf 在多次重试所有可用镜像后仍无法成功下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`，导致 `dnf install` 命令以 exit code 1 失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。本次 PR 的改动仅为新增 Multiwfn 镜像的 openEuler 24.03-LTS-SP4 版本 Dockerfile 及配套元数据文件（README.md、meta.yml、image-info.yml），Dockerfile 中的 `dnf install` 命令语法、包名均正确。失败根因是 openEuler 24.03-LTS-SP4 RPM 仓库在 CI 执行时段出现网络层 HTTP/2 协议异常，属于基础设施问题。

值得注意的是：
- Builder 阶段（`#8`）因 `gcc` 包下载失败直接报错退出，退出码为 1。
- 最终阶段（`#7`）在 builder 失败后被 `CANCELED`（非自身错误），但其日志中也出现了 `gcc-gfortran` 和 `glibc-devel` 包的同类 Curl error (92)，说明仓库不稳定是多阶段共性问题。
- 两个阶段分别下载不同包集合时均遭遇相同错误，进一步佐证这是上游仓库服务端问题，而非某个特定包的问题。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试。** 该错误为 openEuler 24.03-LTS-SP4 RPM 仓库侧的临时网络/服务端 HTTP/2 协议异常，PR 的 Dockerfile 代码无需修改。在仓库服务恢复稳定后重新触发 CI 构建极大概率可通过。若多次重试均在该仓库出现相同错误，需联系 openEuler 基础设施团队排查仓库服务器 HTTP/2 配置。

## 需要进一步确认的点
1. 该 openEuler 24.03-LTS-SP4 仓库近期是否频繁出现 HTTP/2 流错误？建议查询 CI 历史中其他 PR 在相同时间段、使用同一基础镜像（`openeuler/openeuler:24.03-lts-sp4`）的构建记录，判断是偶发还是持续问题。
2. CI 构建节点的网络环境是否需要调整 HTTP 协议降级策略（如 dnf 配置中禁用 HTTP/2 回退到 HTTP/1.1）以规避此类仓库侧 HTTP/2 实现缺陷。
3. 若仅为极低概率偶发事件，无需额外处理，重试即可。
