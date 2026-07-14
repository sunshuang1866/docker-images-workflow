# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, [MIRROR], [FAILED], No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像服务器发生 HTTP/2 协议层流错误（Curl error 92: `INTERNAL_ERROR`），导致 `cmake-data`、`git-core`、`gcc-c++` 等多个 RPM 包的下载流异常中断。其中 `cmake-data` 和 `git-core` 经重试后下载成功，但 `gcc-c++-12.3.1-110` 在所有镜像重试后仍然失败（`No more mirrors to try`），最终 `dnf install` 因无法获取该包而以 exit code 1 失败。

### 与 PR 变更的关联
**与 PR 改动无关。** 此次 PR 仅新增了一个 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`），其 `dnf install` 命令格式和包列表与同类 openEuler 24.03-lts-sp4 的 Dockerfile 完全一致，语法正确。失败发生在 `dnf` 从远程仓库下载 RPM 包的网络传输层，属于 openEuler 软件源镜像服务器端的临时性 HTTP/2 基础设施故障，PR 代码本身没有引入任何问题。

## 修复方向

### 方向 1（置信度: 低 — 仅缓解手段）
**重试构建**。此失败属于瞬时的 CI 基础设施/镜像源网络波动问题，并非代码错误。在实际操作中，重新触发 CI 构建大概率可以通过（待镜像源 HTTP/2 服务恢复后 `dnf` 可正常下载）。Code Fixer 无需处理此问题。

### 方向 2（置信度: 低）
若该问题反复出现，可从 CI 侧考虑：在 `dnf install` 前针对 `gcc-c++` 等大包单独增加重试次数（如 `dnf install -y --setopt=retries=10 ...`），或在 Dockerfile 中预先配置备用镜像源，降低单次 HTTP/2 流错误导致失败的概率。但这类优化属于 CI 基础设施层面的改进，不应在本次 PR 中处理。

## 需要进一步确认的点
- 确认 `repo.****.org` 软件源的 HTTP/2 服务是否已恢复正常（可通过 `curl -I` 测试同一 URL 可达性）。
- 若多次重建后仍然失败，需排查 repo 源端是否存在持续性的 HTTP/2 协议问题，或该特定 RPM 包（`gcc-c++-12.3.1-110.oe2403sp4`）是否在源上已损坏/缺失。
