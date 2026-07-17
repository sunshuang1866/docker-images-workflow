# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 命令）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库镜像在响应 dnf 下载请求时反复出现 HTTP/2 协议层错误（Curl error 92），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载失败，在耗尽所有可用镜像后 dnf 退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 这是一个 CI 基础设施问题。PR 仅新增了一个格式正确的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法和包名均正确。失败根因是 openEuler 24.03-LTS-SP4 仓库镜像服务器在 CI 构建时间窗口内存在 HTTP/2 协议层不稳定性，导致 RPM 包下载中断。两个并行构建阶段（builder #8 和 stage-1 #7）同时遭遇了相同的 HTTP/2 流错误，进一步证实是服务端/网络层问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建即可。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的临时性网络/协议层故障，不是代码问题。在镜像服务恢复稳定后重试 CI 应能成功通过。

### 方向 2（置信度: 低）
如果同一镜像仓库反复出现 HTTP/2 流错误，可考虑在 Dockerfile 的 `dnf` 命令前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 禁用 HTTP/2，强制 dnf 使用 HTTP/1.1 下载。但此方向应在确认仓库 HTTP/2 问题为长期性问题时再采纳，当前更可能是临时波动。

## 需要进一步确认的点
- 同一时间窗口中是否有其他 PR 的 openEuler 24.03-LTS-SP4 构建也失败，以确认是全局性仓库问题而非单次偶发。
- openEuler 仓库维护方是否有已知的 HTTP/2 协议层问题或镜像同步中断公告。

## 修复验证要求
无需验证（infra-error，非代码问题）。
