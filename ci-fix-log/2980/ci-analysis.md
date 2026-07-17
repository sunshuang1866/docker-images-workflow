# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2协议异常
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件源镜像站在服务端 HTTP/2 协议层面出现异常（`INTERNAL_ERROR (err 2)`），多个包下载时遭遇 `Stream error in the HTTP/2 framing layer`（Curl error 92）。部分包（如 git-core）在重试后下载成功，但 gcc-c++ 在所有镜像重试耗尽后仍然失败，导致 `dnf install` 整体退出码为 1。

### 与 PR 变更的关联
**此次失败与 PR 代码变更无关。** PR 仅新增了一个 Dockerfile（及其元数据文件），Dockerfile 中 `dnf install` 命令的语法和包名完全正确（已验证：258 个包均通过依赖解析，下载阶段才开始报错）。失败的根本原因是 openEuler 24.03-LTS-SP4 的 RPM 软件源镜像站发生了 HTTP/2 协议层间歇性故障，属于 CI 基础设施问题（infra-error）。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，等待镜像站恢复后重试构建。** 这是典型的 CI 基础设施网络/协议层瞬时故障。至少 3 个不同包（cmake-data、git-core、gcc-c++）在下载时遭遇了相同的 HTTP/2 stream INTERNAL_ERROR，说明问题出在服务端而非客户端或 Dockerfile。其中 git-core 重试后成功，gcc-c++ 多次重试后耗尽镜像失败。建议在镜像站恢复后触发 re-run。

### 方向 2（置信度: 低，若镜像站持续故障可考虑）
若该镜像站长期不可用，可考虑在 Dockerfile 的 `dnf install` 之前修改 `/etc/yum.repos.d/` 中的 repo 配置，将 `repo.openeuler.org` 替换为其他可用镜像站。但当前日志中所有失败 URL 主机名均为 `repo.****.org`（已被脱敏），无法确认具体是哪个镜像托管站点。

## 需要进一步确认的点
1. 日志中的 `repo.****.org` 原始域名是什么？是否是 `repo.openeuler.org` 或其他内部镜像站？
2. 该镜像站的 HTTP/2 故障是间歇性还是持续性？可通过手动 curl 测试特定 RPM 包 URL 的 HTTP/2 连接稳定性确认。
3. 在相同时间窗口内，其他依赖 openEuler 24.03-LTS-SP4 源做 `dnf install` 的 PR 是否也出现相同错误？（若有多案例可佐证平台级故障）
