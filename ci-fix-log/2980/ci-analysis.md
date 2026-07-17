# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 yum/dnf 软件源镜像服务器（`repo.****.org`）在处理 HTTP/2 请求时多次出现流层错误（Stream error, INTERNAL_ERROR），导致 `cmake-data`、`git-core`、`gcc-c++` 等多个 RPM 包下载中断。其中 `gcc-c++`` 包在 3 次重试后仍全部失败，最终 `dnf install` 因无可用镜像源而终止（exit code: 1）。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、README 条目、image-info.yml 条目和 meta.yml 条目。新增的 Dockerfile 中 `dnf install` 命令语法正确，包列表与同项目其他已成功构建的 Dockerfile 一致。失败是 openEuler 24.03-LTS-SP4 镜像站侧的 HTTP/2 协议层间歇性故障导致的，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该失败是镜像站 HTTP/2 协议层间歇性故障，非代码问题。等待镜像站恢复后重新触发 CI 构建即可。若多次重试仍持续失败，考虑在 dnf 命令前临时禁用 HTTP/2 或降低 curl 的连接协议版本（如在 Dockerfile 的 `RUN dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或 `echo "http2=false" >> /etc/yum.conf`），但这是临时绕过方案，不推荐作为长期修复。

### 方向 2（置信度: 中）
**联系 openEuler 基础设施团队**。`repo.****.org` 镜像站在 2026-07-13 07:04 UTC 前后存在 HTTP/2 服务端 bug（返回 INTERNAL_ERROR），影响了多个并发下载流。这是镜像站服务器端问题，应向 openEuler 基础设施团队报告该时段的服务异常，确认镜像站是否已恢复稳定。

## 需要进一步确认的点
1. 重新触发 CI 构建（不修改任何代码），确认镜像站是否已恢复。若重试后仍失败，且错误同为本报告中 HTTP/2 流错误，则需确认镜像站的持续可用性状态。
2. 确认 `repo.****.org` 镜像站近期是否有维护或已知的 HTTP/2 服务端问题公告。
3. 若重试后失败但错误不同（如新的依赖缺失、编译错误），需重新分析新的日志。
4. 确认 aarch64 (arm64) 架构节点的构建结果是否也遇到了同样的镜像站问题。当前日志仅包含 x86_64 节点日志。
