# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Repo镜像HTTP/2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, [MIRROR], No more mirrors to try, dnf install

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
- 失败位置: Dockerfile:6（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方 RPM 仓库镜像发生间歇性 HTTP/2 传输层错误（Curl error 92），导致 dnf 下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`（13 MB）时连续两次失败，所有镜像重试耗尽后 `dnf install` 整体失败。同时受影响的 `cmake-data`（2.1 MB）和 `git-core`（11 MB）在重试后恢复，唯独 `gcc-c++` 未恢复。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅包含 Dockerfile 新增（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）和元数据文件更新（`README.md`、`image-info.yml`、`meta.yml`），Dockerfile 中的 `dnf install` 命令包列表和写法均无错误。失败完全由 openEuler 24.03-LTS-SP4 仓库镜像服务的 HTTP/2 传输层间歇性故障导致，属于 CI 基础设施/上游仓库的临时问题。

需注意：日志中 `git-core`、`cmake-data` 等包也经历了相同的 HTTP/2 错误但最终重试成功，说明仓库镜像的不稳定性是广泛存在的，只是 `gcc-c++` 运气不好，两次重试均未能恢复。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 此失败为 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 传输层间歇性故障（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），是服务器端网络问题，非 PR 代码缺陷。通常该类问题不会持续存在，触发 recheck/re-trigger 即可通过。若多次重试仍失败，才需考虑方向 2。

### 方向 2（置信度: 低）
**若持续复现，可优化 dnf 重试/镜像配置。** 可考虑在 dnf 配置中增加重试次数和超时时间（如 `dnf install --setopt=retries=10 ...`），或将 DNF 的 HTTP/2 降级为 HTTP/1.1（`ip_resolve=4`、禁用 HTTP/2）以规避服务器端 HTTP/2 实现的间歇性 bug。但这应仅作为反复失败时的兜底方案，优先尝试方向 1。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像服务当前是否稳定（可通过浏览器或 `curl` 直接下载失败的 RPM 包 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 验证）
- 若该错误在多个 PR 的 24.03-LTS-SP4 构建中反复出现，需联系仓库运维团队排查 HTTP/2 服务端问题
