# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败原因: CI 构建环境中 `repo.****.org` 仓库镜像站出现 HTTP/2 协议流中断（`Stream error in the HTTP/2 framing layer`, Curl error 92），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载失败。其中 gcc-c++ 包（13MB）两次重试均失败，耗尽所有镜像重试后 dnf 安装失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 语法正确，`dnf install` 命令及其参数均无问题。失败根因是 openEuler 24.03-LTS-SP4 仓库镜像站在构建时出现 HTTP/2 协议层面的传输故障，属于 CI 基础设施/网络层面的偶发问题。同一构建中 `cmake-data` 和 `git-core` 在遇到 HTTP/2 流错误后均重试成功，只有 `gcc-c++` 重试多次后仍失败，进一步说明这是瞬态网络问题而非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复——重试触发构建即可**。该失败为仓库镜像站 HTTP/2 流传输偶发中断导致的瞬态 infra 问题，Dockerfile 本身无缺陷。建议直接重新触发 CI 构建（retry / re-run），大概率可成功通过。

### 方向 2（置信度: 低）
如果多次重试均在同一包（gcc-c++）上失败，可能是该特定 RPM 包在镜像站上存在完整性/同步问题。此时需要：
- 检查 `repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 在镜像站上的实际可用性和文件完整性
- 或联系仓库镜像站管理员排查该文件的同步状态

## 需要进一步确认的点
- 确认该仓库镜像站（`repo.****.org`）在构建时段是否存在已知的网络波动或维护事件
- 如果多次 retry 仍然失败，需要人工验证 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 在镜像站上的可下载性和 checksum 完整性
