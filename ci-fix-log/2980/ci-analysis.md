# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境中 `dnf install` 从 openEuler 24.03-LTS-SP4 的 RPM 仓库（`repo.****.org`）下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 时遭遇 HTTP/2 协议层流错误（Curl error 92: Stream error in the HTTP/2 framing layer），经过多次重试后所有镜像源均耗尽，导致 `dnf install` 以 exit code: 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该失败是 openEuler 24.03-LTS-SP4 RPM 镜像站在构建时刻发生网络/服务器端 HTTP/2 协议异常。证据：
1. 多个不同包（`cmake-data`、`git-core`、`gcc-c++`）均遇到完全相同的 HTTP/2 流错误（`err 2: INTERNAL_ERROR`），而非针对特定包版本的 404。
2. 部分受影响的包（`cmake-data`、`git-core`）在重试其他镜像后成功下载，仅 `gcc-c++` 耗尽了所有镜像。
3. PR 仅新增 Dockerfile、README 和元数据文件，未修改任何与 dnf 源配置或网络相关的代码。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建。** 该错误极大概率为 openEuler RPM 镜像站的临时性网络抖动（HTTP/2 协议层异常），与 PR 代码变更无关。建议直接在 CI 上 re-run 该 job，观察是否通过。如果重复出现相同错误，则可能是该特定包版本在镜像站确实存在问题，需要进一步排查。

## 需要进一步确认的点
1. 确认 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 在 openEuler 24.03-LTS-SP4 官方仓库中是否真实存在且可正常访问（排除包名/版本号不匹配的可能）。
2. 如果是 aarch64 架构的构建 job 也失败，需要获取对应的 aarch64 构建日志，确认是同一个包的相同 HTTP/2 错误还是不同的错误（以判断是镜像站全局问题还是 x86_64 特定问题）。
3. 确认 CI runner 所在网络与 `repo.****.org` 之间的 HTTP/2 连接是否稳定（可能需要 CI 运维介入排查）。
