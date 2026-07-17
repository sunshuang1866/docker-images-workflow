# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: Docker 构建过程中，`dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时遭遇 HTTP/2 流错误（Curl error 92），涉及 `cmake-data`、`git-core`、`gcc-c++` 三个包。前两者在自动重试后成功，但 `gcc-c++-12.3.1-110.oe2403sp4` 在两个不同 HTTP/2 流（stream 65、stream 83）上均失败，耗尽所有镜像重试次数后安装失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准格式的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）及配套的 README、meta.yml、image-info.yml 文档更新。Dockerfile 中的 `dnf install` 命令列出的均为 openEuler 24.03-LTS-SP4 仓库中的标准基础开发包，语法和包名均正确。失败原因纯粹是下载阶段 openEuler 仓库镜像的 HTTP/2 连接异常，属于 CI 基础设施侧的网络/服务端问题。

## 修复方向

### 方向 1（置信度: 中）
**该失败为瞬时 infra-error，大概率通过重新触发 CI 构建可恢复。** 日志中 `cmake-data` 和 `git-core` 在遭遇相同 HTTP/2 错误后自动重试成功，说明仓库服务本身可用，只是当时存在间歇性抖动。`gcc-c++` 包（约 13MB）恰好赶上了持续较差的时间窗口。建议：直接重新触发 CI job 重试构建。

### 方向 2（置信度: 低）
如果多次重试均因同一包失败（`gcc-c++-12.3.1-110.oe2403sp4`），则可能是该 RPM 包在 openEuler 24.03-LTS-SP4 仓库的所有镜像节点上均存在文件损坏。此时需要联系 openEuler 仓库维护方检查该包的完整性，或等待仓库侧修复后再触发构建。

## 需要进一步确认的点
1. 重新触发同一 CI job 后是否仍然失败？若 3 次重试均失败且错误均指向 `gcc-c++` 同一版本，则排除瞬时网络波动，确认是仓库侧包文件问题。
2. 其他使用 openEuler 24.03-LTS-SP4 基础镜像的同 PR 或近期 PR 是否也出现相同失败？若存在同类失败，可进一步确认是仓库基础设施的普遍问题。
3. aarch64 架构的下游构建 job（如 `/job/aarch64/…`）日志是否也出现相同错误？若两架构均失败且指向同一包，则可确认是仓库侧问题而非单节点网络抖动。
