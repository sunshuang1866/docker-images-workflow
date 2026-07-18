# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), dnf install, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境在通过 `dnf` 从 `repo.****.org` 下载 RPM 包时，openEuler 24.03-LTS-SP4 仓库镜像服务器多次返回 HTTP/2 协议层错误（Curl error 92: Stream error in the HTTP/2 framing layer, HTTP/2 stream was not closed cleanly: INTERNAL_ERROR），导致 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 下载重试耗尽后 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及配套文档（README.md、image-info.yml、meta.yml），Dockerfile 内容为标准的 `dnf install` 编译依赖 + `git clone` + 源码编译流程，语法正确，无可导致 HTTP/2 协议错误的代码逻辑。失败原因是仓库镜像服务器的网络基础设施问题：日志中至少 4 次独立出现 HTTP/2 流错误（涉及 `cmake-data`、`git-core`、`gcc-c++` 三个不同包），其中 `cmake-data` 和 `git-core` 重试后成功，`gcc-c++` 两次均失败，说明这是仓库侧临时间歇性协议层故障，非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 根因是 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议层间歇性错误，与代码无关。通常等待仓库服务恢复后重新触发 CI 即可通过。如果同镜像仓库持续出现此错误，需由 CI 基础设施管理员排查仓库代理/CDN 的 HTTP/2 配置。

### 方向 2（置信度: 低）
**更换仓库镜像源。** 如果 `repo.****.org` 的 HTTP/2 问题持续存在且短期内无法修复，可考虑在 Dockerfile 中将 dnf 的 repo 源切换为其他可用的 openEuler 24.03-LTS-SP4 镜像站（如华为云镜像站或其他已验证可达的镜像源），绕过当前仓库的协议层故障。

## 需要进一步确认的点
- CI 构建环境中的 `repo.****.org`（域名已脱敏）是否普遍存在 HTTP/2 协议兼容性问题（可检查同时段其他 PR 的 x86-64 job 是否有同类 Curl error 92 报错）
- `gcc-c++` 包（13MB）相比其他成功下载的大包（如 `gcc` 34MB、`git-core` 11MB 重试后成功）并不算特别大，需确认镜像仓库对该特定文件路径是否有损坏或配置异常
- 该 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 是否可临时降级为 HTTP/1.1 作为规避手段（需 CI 管理员确认可行性）

## 修复验证要求
无需验证。此失败为 `infra-error`，Code Fixer 无需处理代码。建议直接重新触发 CI 构建流水线。
