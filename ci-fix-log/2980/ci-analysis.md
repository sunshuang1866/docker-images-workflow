# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源 HTTP/2 协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像服务器在处理 HTTP/2 连接时出现内部协议错误（`INTERNAL_ERROR (err 2)`），导致 `dnf install` 在下载 `gcc-c++`（13 MB）和 `cmake-data`、`git-core` 等较大包时 HTTP/2 流异常中断。虽然部分受影响的包通过重试成功下载，`gcc-c++` 在两次重试后仍失败，最终所有镜像源均耗尽，构建失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个 Dockerfile（grADS 2.2.3 on openEuler 24.03-lts-sp4），Dockerfile 中 `dnf install` 列出的软件包名全部合法且正常存在于仓库中。失败原因是 CI 构建时 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端存在间歇性协议错误，属于基础设施层面的网络问题。日志显示 `cmake-data` 和 `git-core` 在遭遇同样的 `Curl error (92)` 后重试成功，进一步佐证服务端不稳定是间歇性的。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 这是 CI 基础设施/软件源镜像服务的临时性网络问题。等仓库镜像 HTTP/2 服务恢复正常后，重新触发 CI 构建即可通过。如果反复出现，可联系 openEuler 基础设施团队排查 `repo.****.org` 镜像站的 HTTP/2 配置。

### 方向 2（置信度: 低）
**降级 dnf 的 HTTP 协议为 HTTP/1.1。** 如果 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 问题持续存在且短时间内无法修复，可考虑在 `dnf install` 前通过 `/etc/dnf/dnf.conf` 或 curl 全局配置强制使用 HTTP/1.1 作为临时绕过方案。但这是治标不治本的措施，不推荐作为首选方案。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 服务状态——该问题是否为持续性故障还是间歇性波动
- 该仓库镜像是否有 HTTP/2 的连接数限制或请求速率限制，`dnf install` 并发下载 258 个包可能触发了某些阈值
- 如果同批 PR 中其他基于 24.03-lts-sp4 的 Dockerfile 也失败，可佐证是基础设施问题；如果能单独通过，则可能是本次构建的 runner 节点与镜像站之间的网络链路异常
