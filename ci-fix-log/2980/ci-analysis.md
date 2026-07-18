# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在 HTTP/2 传输层出现 `INTERNAL_ERROR (err 2)` 流错误，导致 `gcc-c++`（13 MB）等多个 RPM 包下载失败，`dnf` 尝试所有可用镜像后仍无法成功下载，最终安装步骤以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个结构正确的 grads Dockerfile 和配套元数据文件。失败是 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 传输层网络问题（Curl error 92），属于 CI 基础设施层面的瞬时或系统性故障。日志中也可见 `cmake-data` 和 `git-core` 同样遭遇了 HTTP/2 stream 错误，尽管它们最终重试成功。

## 修复方向

### 方向 1（置信度: 中）
**重试构建。** 该失败是网络/mirror 瞬时问题，与代码无关。在 CI 中重新触发构建（re-run），大概率可以成功。如果在多次重试后仍重复出现，则说明 openEuler 24.03-LTS-SP4 的 `OS` 仓库镜像存在持续性的 HTTP/2 传输问题，需联系镜像站运维排查。

## 需要进一步确认的点
1. 该镜像仓库 (`repo.****.org`) 的 HTTP/2 支持是否存在已知问题或配置缺陷，导致 `INTERNAL_ERROR (err 2)` 频繁出现。
2. 是否有其他 PR 在构建 openEuler 24.03-lts-sp4 镜像时也遇到相同的 Curl error (92) 问题——如果是系统性故障，则可作为新的已知模式归档；如果是个例，则属于瞬时网络抖动。
3. 如果重试多次仍持续失败，需确认是否可以通过 `dnf` 配置禁用 HTTP/2（如设置 `http2=false` 或降级到 HTTP/1.1）来规避该 mirror 的 HTTP/2 问题。

## 修复验证要求
本案例无需 code-fixer 介入，属于 infra-error 类型。Code Fixer 不需要处理此 PR。
