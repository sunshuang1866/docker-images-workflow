# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, MIRROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（dnf install 步骤）
- 失败原因: CI 构建环境中 `dnf` 从 openEuler 24.03-LTS-SP4 官方软件仓库 (`repo.****.org`) 下载 RPM 包时，多个包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc` 等）均遭遇 Curl error (92)——HTTP/2 流被服务端非正常关闭（`INTERNAL_ERROR`），所有镜像重试均耗尽后 `dnf` 报错退出。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准的多阶段构建 Dockerfile 和配套的元数据文件（`meta.yml`、`image-info.yml`、`README.md`），`dnf install` 命令语法和包名均正确。失败纯粹由 openEuler 软件仓库服务端的 HTTP/2 协议层故障引起，属于 CI 基础设施问题。

具体证据：
- 多阶段构建的两个阶段（builder 的 `#8` 和 stage-1 的 `#7`）**同时**遭遇不同包的同类型 HTTP/2 流错误。
- 失败的包具有随机性（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc` 各在不同 stream 上失败），不是特定包的版本或 URL 路径问题。
- 部分包下载成功（如 `acl`、`compat-openssl11-libs`、`binutils` 等），说明仓库是可访问的但 HTTP/2 连接不稳定。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 官方软件仓库 `repo.****.org` 服务端的 HTTP/2 临时故障。建议重试 CI（re-run/retrigger pipeline），等待仓库服务恢复后构建应能正常通过。

### 方向 2（置信度: 低）
如果该仓库持续不稳定，可考虑在 Dockerfile 的 `dnf install` 前增加 `dnf makecache --refresh` 或通过 `echo "http/1.1" >> /etc/dnf/dnf.conf` 强制 dnf 使用 HTTP/1.1 避免 HTTP/2 协议层问题。但这属于针对基础设施缺陷的 workaround，不应作为标准修复方案。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 `OS` 仓库（`repo.****.org`）在当前时段是否存在已知的 HTTP/2 服务端异常或维护事件。
- 如果 CI 重试仍然失败，需联系仓库管理员确认镜像站状态。
