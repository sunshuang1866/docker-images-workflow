# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包镜像仓库在本次构建期间存在 HTTP/2 协议层错误，导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载时发生 `Curl error (92): Stream error in the HTTP/2 framing layer`。cmake-data 和 git-core 通过镜像重试成功下载，但 gcc-c++（13 MB，较大的包）经过两次重试（stream 65、stream 83）后仍然失败，最终因所有镜像均已尝试而无法下载，导致整个 `dnf install` 命令以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准的 GrADS Dockerfile（`dnf install` 编译依赖 → `git clone` 源码 → 编译安装）以及配套的元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 包列表在语法和内容上均无错误，失败纯粹是由于 openEuler 24.03-LTS-SP4 软件包仓库在构建时的 HTTP/2 传输层发生了瞬态网络故障。这是一个 CI 基础设施问题，与代码变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该失败为 openEuler 软件包仓库 HTTP/2 传输层的瞬态网络故障，属于纯粹的 CI 基础设施问题。无需对 Dockerfile 或任何代码文件进行修改。通过 CI 重新触发构建（re-run），在仓库服务正常的时间窗口内，相同的 `dnf install` 命令应能正常完成所有包的下载。

### 方向 2（置信度: 低）
若反复重试仍然失败（说明仓库 HTTP/2 问题持续存在），可考虑在 Dockerfile 的 `dnf install` 命令前添加重试逻辑（如 `dnf install --setopt=retries=10`），或临时更换 openEuler 镜像源。但根据日志中其他包（cmake-data、git-core）在重试后成功下载的事实，这更可能是单次构建中运气不佳的网络瞬态，而非持续性问题。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 镜像仓库的 HTTP/2 协议错误是否为持续性故障（可通过查看同时段其他使用相同基础镜像的 CI job 是否也失败来验证）。
- 若问题持续，需要联系 openEuler 镜像站运维确认仓库服务端 HTTP/2 配置是否存在问题。
- 若该失败仅在本次构建中出现且重试后通过，则确认为一过性网络抖动，无需任何代码修复。
