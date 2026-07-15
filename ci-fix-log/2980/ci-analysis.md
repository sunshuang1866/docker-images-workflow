# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, Error downloading packages

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件源（`repo.****.org`）在本次构建期间 HTTP/2 连接不稳定，多个 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）下载时出现 `Curl error (92): Stream error in the HTTP/2 framing layer`。`cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 重试多次后耗尽所有镜像源，最终因 "No more mirrors to try" 导致 `dnf install` 失败。

### 与 PR 变更的关联
与 PR 代码变更无关。PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及其配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `dnf install` 所声明的包列表完整且语法正确。失败完全由 CI 构建时 openEuler 软件源服务器的 HTTP/2 协议层临时故障引起，属于基础设施层面的网络传输问题。

## 修复方向

### 方向 1（置信度: 高）
无需修改 Dockerfile 或任何代码。该失败属于 CI 基础设施问题（openEuler 软件源镜像站 HTTP/2 连接临时中断）。建议直接重试 CI 构建，等待镜像源恢复，大概率可以构建成功。

### 方向 2（置信度: 低）
如果该镜像源持续不稳定，可在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager --setopt=ip_resolve=4` 以强制使用 IPv4，或改用其他 openEuler 镜像源（如 `repo.huaweicloud.com`）替代当前源。但这属于绕过手段而非修复，上游源恢复后应还原。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 软件源（`repo.****.org`）在该时间段是否存在已知的网络波动或维护事件。
- 确认该类 HTTP/2 流错误是否在同时间段的其他 PR 构建中也出现，以排除 CI runner 自身的网络配置问题。
