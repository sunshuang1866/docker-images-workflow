# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在 Docker 构建阶段出现 HTTP/2 协议层错误（`Curl error 92: Stream error in the HTTP/2 framing layer`），导致多个 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）下载失败。`gcc-c++` 包在重试两次后耗尽所有镜像源，`dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准格式的 Dockerfile（`dnf install` 安装编译依赖 → 编译安装 GrADS）以及三个元数据/文档文件。`dnf install` 所列包均为 openEuler 24.03-LTS-SP4 官方仓库的标准包，Dockerfile 语法无误。失败根因是 CI 构建时 openEuler 仓库镜像服务端的 HTTP/2 流异常，属于基础设施瞬时故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 此失败为 CI 构建节点与 openEuler 仓库镜像之间的 HTTP/2 网络传输瞬时故障，属于 `infra-error`。Code Fixer 无需处理，建议触发 rerun/retry 该 CI job 即可。若该问题频繁复现，需由 CI 基础设施管理员排查仓库镜像服务器（`repo.****.org`）的 HTTP/2 配置或网络链路稳定性。

## 需要进一步确认的点
- 该仓库镜像（`repo.****.org`）是否在构建时段存在已知的 HTTP/2 服务端问题或网络波动。
- 同一时段其他使用 openEuler 24.03-LTS-SP4 仓库的构建 job 是否也出现相同错误，以确认是单次瞬时故障还是持续性问题。
- 若 retry 后仍然失败，可考虑在 Dockerfile 的 `dnf install` 前增加 `dnf makecache` 或配置回退到 HTTP/1.1 的 curl 选项以规避 HTTP/2 层错误。
