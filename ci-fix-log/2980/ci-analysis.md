# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在提供 RPM 包下载时出现 HTTP/2 协议层流错误（Curl error 92: INTERNAL_ERROR），导致 `cmake-data`、`git-core`、`gcc-c++` 三个包下载中断。其中 `gcc-c++` 在 dnf 重试耗尽所有 mirror 后仍失败，`dnf install` 命令整体以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 变更仅为新增 GrADS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关文档/元数据更新（4 个文件，共新增约 34 行）。Dockerfile 中的 `dnf install` 命令语法正确、依赖包列表完整。失败原因是 CI 构建环境中 openEuler 软件仓库的 HTTP/2 传输层出现间歇性故障，属于基础设施问题。`cmake-data` 在重试后成功下载（日志中可见其后续下载完成），也印证这是网络波动而非包不存在。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，触发 CI 重新运行即可。** 这是 openEuler 24.03-LTS-SP4 软件镜像仓库的临时性 HTTP/2 传输故障，与 PR 代码变更无关。等待仓库服务恢复（或路由到其他可用 mirror）后重新触发 CI 构建。若多次重试仍失败，可联系 openEuler 基础设施团队排查 `repo.****.org` 服务器的 HTTP/2 实现兼容性问题。

## 需要进一步确认的点
- 确认 `repo.****.org`（屏蔽域名）在故障时间点是否有网络异常或服务端维护记录。
- 确认同一时段其他 PR 的 openEuler 24.03-LTS-SP4 构建是否也出现相同的 HTTP/2 stream error，以判断是系统性故障还是偶发波动。
