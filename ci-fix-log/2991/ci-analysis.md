# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:6` — `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: openEuler 24.03-LTS-SP4 的 aarch64 仓库镜像（`repo.openeuler.org`）在 HTTP/2 传输中多次出现流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致多个 RPM 包（`git-core`、`gcc-c++`、`guile`）下载失败。其中 `git-core` 经重试后成功，`gcc-c++` 重试仍失败（2次），`guile` 耗尽所有镜像后最终失败，触发 `dnf install` 退出码 1。`guile` 是 `git` 的传递依赖，并非 PR 直接指定的包。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准格式的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake` 命令格式完全正确，与同项目其他 vvenc 版本的 Dockerfile（如 24.03-lts-sp3）一致。失败纯粹由 openEuler 24.03-LTS-SP4 aarch64 仓库镜像的HTTP/2 传输不稳定导致，属于 CI 基础设施问题。

**关键证据**：同一个包（`gcc-c++`）在镜像重试后仍然失败（`stream 39` → `stream 51`），说明问题出在服务端 HTTP/2 连接层面，而非特定文件损坏或缺失。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。这是 openEuler 24.03-LTS-SP4 aarch64 仓库镜像的临时性基础设施故障（HTTP/2 流错误）。重新触发 CI 重试即可——若镜像服务恢复正常，构建应能通过。Dockerfile 本身无需任何修改。

### 方向 2（置信度: 低）
若重试后仍然失败（说明 `guile` 包在上游仓库确实有下载问题），可在 `dnf install` 命令中添加 `--setopt=timeout=300` 或 `--setopt=minrate=0` 参数增加下载容错性。但这属于治标手段，不推荐优先采用。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 aarch64 仓库镜像（`repo.openeuler.org`）在构建时刻的 HTTP/2 服务端状态是否异常（需运维侧确认）
- 确认同仓库的其他 aarch64 构建 job（如其他 SP4 镜像）在同一时间段是否也出现相同错误，以排除单包问题
