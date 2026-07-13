# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: curl error (92), HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤，即新增 Dockerfile 的第一个 RUN 指令）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库（`repo.****.org`）在 CI 构建期间出现 HTTP/2 协议层流错误（`Curl error 92: INTERNAL_ERROR`），导致 `cmake-data`、`git-core`、`gcc-c++` 共 3 个 RPM 包下载失败。其中 `cmake-data` 和 `git-core` 通过 dnf 自动重试成功，`gcc-c++`（约 13MB）在多次重试后仍失败，dnf 耗尽所有镜像后报错退出。

### 与 PR 变更的关联
**与 PR 改动无关**。PR 新增的 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 语法正确、依赖声明完整，与已有的 `24.03-lts-sp3` Dockerfile 结构一致。`README.md`、`doc/image-info.yml`、`meta.yml` 的修改也只涉及新增镜像条目的声明，无格式错误。构建在 Docker 镜像构建阶段（`dnf install` 从上游仓库拉取 RPM 包时）失败，根因是 openEuler 软件源一侧的 HTTP/2 传输问题，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改，触发 CI 重试即可。** 此失败是 openEuler 24.03-LTS-SP4 软件包仓库的临时网络/协议故障导致，Dockerfile 本身无问题。重新触发 CI 流水线，若仓库恢复可用，构建应能通过。

### 方向 2（置信度: 中，仅当重试持续失败时考虑）
若多次重试后同一错误持续出现，可能是 CI 构建节点与特定 openEuler 镜像站之间的 HTTP/2 兼容性问题。此时可在 Dockerfile 的 `dnf install` 前添加 `echo 'http2=false' >> /etc/dnf/dnf.conf`（禁用 HTTP/2 协议回退到 HTTP/1.1），或通过 dnf 配置切换至备用软件源镜像。

## 需要进一步确认的点
- 确认当前 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务是否正常（可在此 PR 之外用独立环境测试 `dnf install gcc-c++`）
- 若触发重试后仍失败，需确认 CI 构建节点到 `repo.****.org` 的网络链路是否存在中间代理干扰 HTTP/2 分帧的问题

## 修复验证要求
无需特殊验证步骤。重新触发 CI 流水线后，观察 `dnf install` 步骤是否能正常完成 258 个包的下载与安装即可。
