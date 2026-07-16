# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SP4仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-15`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 x86_64 架构构建过程中出现 HTTP/2 协议层流错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），导致 `cmake-data`、`git-core`、`gcc-c++` 等多个 RPM 包下载失败。dnf 在尝试了所有可用镜像后仍无法成功下载 `gcc-c++`，最终构建中止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及相关元数据文件，Dockerfile 本身语法和包依赖声明均正确（dnf 已成功解析了 258 个包的依赖关系并开始下载，其中 40 个包已成功下载）。失败完全是由于 openEuler 24.03-LTS-SP4 仓库镜像在网络传输层出现 HTTP/2 协议错误导致的，属于 CI 基础设施问题。日志中 `cmake-data` 包在遭遇一次 HTTP/2 错误后重试成功（1199.1 → 1252.9），但 `gcc-c++`（13MB 大包）在两个不同镜像上均失败（stream 65 和 stream 83），说明问题具有间歇性与镜像相关性。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 基础设施临时故障。建议直接**重试 CI 构建**——如果镜像服务恢复正常，构建即可通过。同时可向 openEuler 仓库运维团队报告 SP4 镜像站存在 HTTP/2 stream 错误（影响 x86_64 架构 OS 仓库下多个 RPM 包的大文件下载）。

### 方向 2（置信度: 低）
**dnf 配置降级为 HTTP/1.1。** 如果 SP4 仓库镜像的 HTTP/2 问题持续性存在，可在 Dockerfile 的 `dnf install` 前通过 `echo "http2=false" >> /etc/dnf/dnf.conf` 或等效方式强制 dnf 使用 HTTP/1.1 协议下载，规避 HTTP/2 流错误。但此方向为临时规避手段，不建议作为正式修复。

## 需要进一步确认的点
- 同 PR 的 aarch64 架构构建 job 日志中，24.03-LTS-SP4 仓库是否也存在相同 Curl error (92)？（如果 aarch64 也失败，说明是整个 SP4 镜像站问题；如果仅 x86_64 失败，可能是 x86_64 特定镜像节点问题）
- 该 SP4 仓库镜像的 HTTP/2 错误是临时性还是持续性？建议间隔一段时间后重试构建以确定。
- PING `repo.****.org` 的网络链路是否稳定？是否存在中间代理/负载均衡器导致 HTTP/2 长连接被异常关闭？

## 修复验证要求
无需验证。本失败为 infra-error，无代码修复，Code Fixer 无需处理。
