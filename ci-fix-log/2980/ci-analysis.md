# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, openEuler repository, No more mirrors to try

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
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件包仓库（`repo.*.org`）在下载 `gcc-c++` 包（13 MB）时出现 HTTP/2 流协议错误（Curl error 92），dnf 在尝试所有镜像后仍无法下载成功，安装步骤整体失败。日志中共出现 3 个包（cmake-data、git-core、gcc-c++）遭遇同类 HTTP/2 流中断，其中前两个在重试后成功，仅 gcc-c++ 在所有镜像均失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 这是 CI 基础设施问题——openEuler 24.03-LTS-SP4 软件包仓库在构建时出现了 HTTP/2 协议层不稳定。PR 新增的 Dockerfile 语法正确，所列软件包均为 openEuler 24.03-LTS-SP4 仓库中实际存在的包（日志中 dnf 已成功解析依赖并列出 258 个待安装包），前三方包（cmake-data、git-core）也已通过重试成功下载。失败纯因 `gcc-c++` 在仓库侧的 HTTP/2 传输反复中断且耗尽重试次数。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是瞬时的网络/仓库基础设施问题，Dockerfile 本身无需任何修改。触发 re-run 后大概率可以通过。

### 方向 2（置信度: 中，仅当重试多次仍失败时考虑）
如果该仓库持续出现 HTTP/2 流错误，可考虑在 Dockerfile 的 `dnf install` 命令前添加重试机制，例如用 `dnf install -y --allowerasing ... || dnf install -y --allowerasing ...` 或在 RUN 命令前增加 `dnf makecache` 预热元数据，但这不是根本解决方案，根因在仓库侧。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库 `repo.*.org` 在该构建时间段的可用性状态，是否为临时波动。
- 如果多次重试始终失败，需要排查 `repo.*.org` 对该 CI runner IP 的 HTTP/2 连接是否有限流或防护策略。
