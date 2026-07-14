# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 构建环境中 `dnf install` 从 openEuler 24.03-LTS-SP4 镜像站下载 RPM 包时，多次出现 HTTP/2 流帧错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`）。其中 `cmake-data` 和 `git-core` 在重试后下载成功，但 `gcc-c++`（13 MB，相对较大的包）两次重试均失败，最终 dnf 耗尽所有镜像源（`No more mirrors to try`），构建中止。该错误与 PR 代码变更无关，属于 CI 基础设施/镜像站网络传输稳定性问题。

### 与 PR 变更的关联
PR 新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`，Dockerfile 内容本身无语法或逻辑错误——`dnf install` 的包列表正确，仓库元数据正常下载（`OS`、`everything`、`EPOL` 等 repo 均成功同步）。失败完全由网络传输层面（镜像站 HTTP/2 连接不稳定）引起，与 PR 代码变更无因果关系。该镜像站不稳定问题会同等影响所有需要从该仓库下载较大 RPM 包的构建任务。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，无需修改代码。触发 **重新运行 CI job**（retry/re-run），在镜像站网络状态恢复正常后重新构建即可通过。该 gcc-c++ 包在 openEuler 24.03-LTS-SP4 仓库中是确认存在的有效包（dnf 已成功解析依赖并开始下载），仅为传输层面的瞬态故障。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 镜像站（`repo.****.org`）在失败时段是否存在已知的 HTTP/2 或 CDN 故障。
- 如果多次重试均失败，需排查 CI runner 到镜像站之间的网络链路是否存在 HTTP/2 协议兼容性问题（如中间代理/TLS 终结层与 HTTP/2 长连接的交互异常）。
