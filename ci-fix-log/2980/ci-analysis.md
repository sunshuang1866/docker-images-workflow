# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, gcc-c++, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake autoconf automake libtool pkgconf-devel ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 镜像源（`repo.****.org`）在下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 等包时反复出现 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 dnf 多次重试后耗尽所有镜像源，最终安装失败。日志中同时观察到 `cmake-data` 和 `git-core` 两个包也出现了相同的 HTTP/2 流错误，表明这是镜像源服务端或 CI 构建节点与该镜像源之间的 HTTP/2 连接不稳定，而非特定包的下载问题。

### 与 PR 变更的关联
**无关**。PR 的变更仅包括：
1. 新增 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（30 行新文件，标准构建脚本）
2. 更新 `Others/grads/README.md`（新增一行表格条目）
3. 更新 `Others/grads/doc/image-info.yml`（新增一行镜像信息）
4. 更新 `Others/grads/meta.yml`（新增版本映射条目）

Dockerfile 中 `dnf install` 命令语法正确，所安装的包名（`gcc-c++`、`cmake` 等）均在日志的依赖解析列表中确认存在。失败根因是 CI 构建环境与 openEuler 24.03-LTS-SP4 镜像源之间的网络/协议层问题，与 PR 代码变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码**。此为 CI 基础设施问题（镜像源 HTTP/2 协议层不稳定），Code Fixer 无需处理。
- 建议操作：重新触发 CI 构建。HTTP/2 流错误属于网络瞬态故障，重试后大概率通过。
- 若多次重试仍失败，需检查 CI 构建节点到 `repo.****.org` 的网络链路（代理、防火墙是否干扰 HTTP/2 连接），或联系镜像源运维排查 HTTP/2 服务端问题。

## 需要进一步确认的点
- HTTP/2 流错误是否在同时间段内影响其他 PR 的 openEuler 24.03-LTS-SP4 构建（若其他 sp4 构建也失败，可确认是镜像源侧的普遍性问题）
- 重试后是否通过（用于确认是否为瞬态故障）
