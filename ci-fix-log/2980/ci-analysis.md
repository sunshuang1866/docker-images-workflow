# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库在 DNF 下载 `gcc-c++` 等 RPM 包时出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），多次重试均失败，所有镜像源耗尽后构建中止。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 新增的 Dockerfile 中 `dnf install` 命令语法正确，所列包名（`gcc-c++`、`cmake`、`git` 等）均为 openEuler 24.03-LTS-SP4 仓库中的有效包名。构建在基础镜像拉取完成（`#6 DONE 10.6s`）后，进入软件包下载阶段时，仓库端 HTTP/2 连接出现间歇性断流，属于 CI 基础设施/上游仓库的网络问题。

## 修复方向

### 方向 1（置信度: 高）
**等待仓库恢复后重试构建**。错误为 `Curl error (92): Stream error in the HTTP/2 framing layer`，这是 HTTP/2 协议层的传输错误，通常由服务端或中间代理的瞬时故障导致。在 CI 中重新触发构建（retry）即可，无需修改任何代码。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）的 HTTP/2 服务状态是否正常，是否存在已知的间歇性服务降级。
- 如果同一仓库的其他 PR 也出现类似 HTTP/2 流错误，则更确认是上游仓库问题而非个案。
