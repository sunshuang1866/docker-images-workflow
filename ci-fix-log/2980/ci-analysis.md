# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, [MIRROR], No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 软件源（`repo.****.org`）在 CI 构建期间出现 HTTP/2 流层传输错误（`INTERNAL_ERROR (err 2)`），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载过程中断。其中 cmake-data 和 git-core 在重试后成功下载，但 `gcc-c++` 包两次重试均失败，最终所有镜像源耗尽，dnf 安装终止。

### 与 PR 变更的关联
此失败与 PR 代码变更**无关**。PR 仅新增了一个格式正确的 Dockerfile（`dnf install` 命令语法无误，包名列表与其他同项目的 Dockerfile 一致）和对应的元数据文件（README.md、image-info.yml、meta.yml）。构建失败完全由 CI 运行时 openEuler 软件源的网络传输波动导致，属于基础设施层面的偶发问题。

## 修复方向

### 方向 1（置信度: 高）
此失败为 `infra-error`，无需修改 PR 代码。直接重新触发 CI 构建即可。软件源的 HTTP/2 流错误是临时性网络问题，通常在重试后可自行恢复。如果多次重试仍失败，则需排查 `repo.****.org` 服务端状态或 CI 网络链路的 HTTP/2 兼容性。

## 需要进一步确认的点
- 确认 `repo.****.org` 在故障时间段的服务状态是否正常
- 确认 CI 构建节点到该软件源的网络链路是否存在 HTTP/2 代理或中间设备导致的兼容性问题
- 如果该问题持续复现，可能需要考虑在 Dockerfile 中配置 dnf 回退到 HTTP/1.1（如设置 `http2=false` 或添加备选镜像源）
