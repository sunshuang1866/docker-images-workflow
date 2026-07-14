# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder stage 的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）在通过 HTTP/2 协议下载多个 RPM 包时反复出现 curl error 92（HTTP/2 流未被正常关闭，服务器端报 INTERNAL_ERROR），最终 `gcc` 包（34 MB）在尝试所有镜像后均失败，导致 dnf 安装步骤以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增的 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`）在语法和结构上完全正确，与已有的 `24.03-lts-sp3` 版本 Dockerfile 模式一致。失败纯粹由 CI 构建环境中 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议层传输故障引起。

值得注意的是，两个并行构建阶段（#7 stage-1 运行时阶段 和 #8 builder 构建阶段）同时遭遇了相同的 HTTP/2 流错误，且涉及多个不同 RPM 包（gcc-gfortran、glibc-devel、guile、gcc），表明问题出在仓库服务端而非特定文件或客户端。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 此为 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 协议故障，与 PR 代码无关。等待仓库服务恢复后重试构建即可。Code Fixer 无需处理。

### 方向 2（置信度: 低）
若多次重试仍持续失败，需由 CI 基础设施团队排查 openEuler 24.03-LTS-SP4 仓库 HTTP/2 服务的稳定性，或临时将 dnf 下载协议降级为 HTTP/1.1（通过 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 curl 的 `--http1.1` 选项）。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像 `repo.openeuler.org` 的 HTTP/2 服务在构建时段的健康状态
- 该仓库镜像是否对大于某阈值的文件下载存在 HTTP/2 流管理缺陷（注意到所有失败的包均在 1.4 MB 以上，34 MB 的 gcc 最终触发致命失败）
- 该批次 CI 构建中其他同样引用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也出现相同问题
