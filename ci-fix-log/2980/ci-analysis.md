# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
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
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件源镜像在本次构建中频繁出现 HTTP/2 流错误（Curl error 92），导致 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 下载失败。虽部分包（cmake-data、git-core）通过重试其他镜像恢复，但 `gcc-c++` 在两次重试（流 65、流 83）后耗尽所有镜像，dnf 安装失败。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 仅新增了一个标准的 GrADS Dockerfile 和对应的元数据更新。Dockerfile 中的 `dnf install` 命令语法正确、包名合法，失败原因是上游 openEuler 24.03-LTS-SP4 镜像站的网络传输层问题（HTTP/2 `INTERNAL_ERROR`），属于 CI 基础设施层面的 transient 故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是一个 CI 基础设施问题——openEuler 24.03-LTS-SP4 RPM 仓库镜像在构建期间存在 HTTP/2 协议层不稳定性。建议方式：
- **直接重试 CI 构建**。此类 HTTP/2 流错误通常是临时性的镜像站问题，重跑后大概率通过。
- 若多次重试均失败，可考虑在 Dockerfile 中为 `dnf` 命令添加 `--retries=N`（默认 10）和 `--setopt=timeout=300` 等提高容错性的参数，但这属于被动规避而非根因修复。

## 需要进一步确认的点
- 在同一时段内，其他使用 24.03-LTS-SP4 基础镜像的构建 job 是否也出现相同错误（以判断是镜像站全局故障还是单次偶发）。
- 若重试多次仍持续失败，需确认 `repo.****.org` 的 openEuler 24.03-LTS-SP4 镜像站是否有持续性服务降级。
