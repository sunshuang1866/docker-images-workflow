# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, dnf install

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
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 传输层出现多个 `INTERNAL_ERROR`（Curl error 92），导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个大型 RPM 包（10MB+）下载失败，重试耗尽后 dnf 报错退出。该问题在两个构建阶段（#7 stage-1 和 #8 builder）同时出现。

### 与 PR 变更的关联

**与 PR 代码变更无关。** PR 仅新增了一个标准结构的 Dockerfile（安装编译依赖 → 克隆源码 → 编译 → 多阶段复制）和配套元数据文件。Dockerfile 中的 `dnf install` 包列表语法正确、包名有效（同阶段 #7 中其他小包如 `compat-openssl11-libs`、`binutils`、`dbus-libs` 等成功下载）。失败完全由 openEuler 镜像站的 HTTP/2 服务器端流中断引起，同样的包（`gcc-gfortran`、`glibc-devel`）在 #7 和 #8 两个独立容器构建上下文中均出现相同错误，说明是仓库端问题而非单次网络抖动。

## 修复方向

### 方向 1（置信度: 中）
重新触发 CI 构建。HTTP/2 流错误（`INTERNAL_ERROR`）通常是仓库服务器端临时故障，大概率无需任何代码变更，重试后可恢复正常。

### 方向 2（可选，置信度: 低）
若重试持续失败，可在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager --setopt fastestmirror=1` 或配置备用镜像源，以规避特定镜像节点的 HTTP/2 问题。但鉴于该错误同时影响 #7 和 #8 两个阶段的多个不同包，更有可能是仓库端全局问题而非个别镜像节点问题。

## 需要进一步确认的点

- 本次 CI 构建时刻 openEuler 24.03-LTS-SP4 镜像站是否存在已知的 HTTP/2 服务异常或维护事件。
- 同期其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也出现了相同的 `Curl error (92)` 下载失败，以确认是系统性故障还是本构建节点独有问题。
