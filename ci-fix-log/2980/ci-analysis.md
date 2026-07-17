# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像在 CI 构建期间出现 HTTP/2 协议层面的流中断错误（Curl error 92），导致 `gcc-c++` 13 MB RPM 包经过两次重试后仍下载失败，`dnf install` 整体退出。`cmake-data` 和 `git-core` 也遇到了同样的流错误，但重试后成功下载。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件。Dockerfile 的 `dnf install` 命令包列表语法正确，与同项目已有的 sp3 版本 Dockerfile 模式一致。失败完全是由 openEuler 官方软件仓库镜像的网络层 HTTP/2 协议问题触发——3 个不同 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）在下载过程中各自遭遇了独立的 HTTP/2 stream 中断，说明是镜像站端的协议处理异常，而非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是典型的 `infra-error`——openEuler 24.03-LTS-SP4 仓库镜像在特定时段的 HTTP/2 流处理不稳定，与代码无关。Code Fixer 无需修改任何文件。等待镜像站恢复后重新运行 CI 流水线即可通过。

### 方向 2（置信度: 低）
如果问题持续反复出现（同一镜像站多次触发同类 HTTP/2 错误），可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5` 或 `--setopt=timeout=120` 参数增强网络容错能力。但鉴于当前日志显示为偶发性的基础设施协议层错误，暂不推荐此类改动。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）的 HTTP/2 服务在 CI 失败时段是否存在已知故障或维护窗口。
- 若该镜像持续出现 HTTP/2 流错误，排查 CI 构建节点与镜像站之间的网络代理/负载均衡器是否存在 HTTP/2 协议兼容性问题。
