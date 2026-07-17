# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库（`repo.****.org`）在通过 HTTP/2 协议分发 RPM 包时，多个包的下载流反复出现 `INTERNAL_ERROR (err 2)`，curl 重试耗尽所有镜像后，`dnf install` 失败（exit code: 1）。该问题同时影响了同一次构建中的两个并行 stage（builder 阶段 #8 和 stage-1 最终阶段 #7），且影响多个不同 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`），排除单个包或单次请求的偶发问题，属于仓库服务器端 HTTP/2 协议实现缺陷或代理/负载均衡层问题。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 openEuler 24.03-LTS-SP4 的 Dockerfile（与已有 sp3 Dockerfile 结构相同）及对应的文档/元数据条目。Dockerfile 中的 `dnf install` 命令本身语法和包名均正确（同 sp3 版本一致），失败完全由 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 传输层故障导致。sp3 版本的同类 Dockerfile 构建正常，进一步证明问题出在 sp4 仓库侧而非 Dockerfile 代码。

## 修复方向

### 方向 1（置信度: 中）
**等待仓库恢复后重试**。这是 openEuler 24.03-LTS-SP4 官方软件仓库的 HTTP/2 服务端临时故障。Curl error (92) 的 `INTERNAL_ERROR` 通常由服务器端 HTTP/2 实现缺陷或中间代理（如反向代理/负载均衡器）的流管理问题引起。无需修改任何代码，等待仓库运维方修复后重新触发 CI 构建即可。

### 方向 2（置信度: 低）
**降级 curl 连接协议**。如果仓库 HTTP/2 问题持续存在，可在 Dockerfile 的 `dnf install` 前通过设置环境变量 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf/curl 使用 HTTP/1.1 协议连接仓库，绕过 HTTP/2 流层错误。但这是规避手段而非根因修复，且需要确认该配置对仓库其他功能无副作用。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在 CI 失败时的运行状态是否正常，是否存在已知的 HTTP/2 协议相关问题。
2. 仓库前是否有 CDN 或反向代理（如 Nginx/Envoy），其 HTTP/2 配置是否存在导致流异常的已知缺陷。
3. 修改 `repo.****.org` 为其他 openEuler 官方镜像站（如 `mirrors.tuna.tsinghua.edu.cn` 或 `repo.huaweicloud.com`）是否仍有同样问题。
