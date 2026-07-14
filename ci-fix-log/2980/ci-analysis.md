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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像站在下载 RPM 包时出现 HTTP/2 流层协议错误（`Curl error (92): Stream error in the HTTP/2 framing layer`）。其中 `cmake-data` 和 `git-core` 经重试后下载成功，但 `gcc-c++` 在所有镜像源上重试后均失败（`No more mirrors to try`），导致 dnf 安装步骤整体失败。

### 与 PR 变更的关联

**与 PR 改动无关。** 本次 PR 新增的 Dockerfile 本身语法正确、依赖声明合理。失败完全由 CI 构建时 openEuler 24.03-LTS-SP4 RPM 仓库镜像站的 HTTP/2 通信不稳定引起，属于基础设施层面的瞬时故障。同类问题同样可能影响其他使用 24.03-LTS-SP4 仓库的镜像构建。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 这是典型的 CI 基础设施瞬时故障，openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 服务端问题随时可能恢复。Code Fixer 无需对 Dockerfile 做任何修改，直接触发 re-run / retry 即可。

### 方向 2（置信度: 中，仅在重试持续失败时考虑）
**添加 dnf 重试参数或 HTTP/1.1 降级。** 如果该仓库镜像持续出现 HTTP/2 错误，可在 Dockerfile 的 `dnf install` 命令前设置环境变量强制 curl 使用 HTTP/1.1（`--setopt=minrate=0 --setopt=timeout=300` 或配置 `/etc/dnf/dnf.conf` 的 `ip_resolve=4` 等），或为 `dnf` 追加 `--retries=10 --setopt=retries=10` 提高容错。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像 (`repo.****.org`) 当前服务状态是否已恢复
- 如果持续失败，确认是否仅 x86_64 仓库受影响，还是 aarch64 仓库也有相同问题
- 检查同时期其他使用 24.03-LTS-SP4 基础镜像的 PR 是否也遇到相同的 `Curl error (92)` 失败
