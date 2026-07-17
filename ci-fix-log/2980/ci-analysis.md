# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 镜像站流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误

```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

另外两个包也出现了相同的 HTTP/2 流错误，但重试后成功：
- `cmake-data-3.31.12-1.oe2403sp4.noarch.rpm` — HTTP/2 stream 15 INTERNAL_ERROR → 重试成功
- `git-core-2.54.0-2.oe2403sp4.x86_64.rpm` — HTTP/2 stream 75 INTERNAL_ERROR → 重试成功

### 根因定位

- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像站（`repo.****.org`）的 HTTP/2 服务端存在协议实现缺陷，向客户端返回 `INTERNAL_ERROR`（err 2）导致 curl 流层报错。`gcc-c++` 包（13 MB）经历两次 HTTP/2 流错误后，dnf 耗尽所有镜像重试次数，下载失败。

### 与 PR 变更的关联

**与 PR 变更无关。** 该 PR 仅新增了一个合法的 Dockerfile（`dnf install` 包列表语法正确、包名有效）和配套元数据文件。失败完全由 CI 构建环境与 openEuler 软件仓库之间的 HTTP/2 协议层不稳定引起，属于基础设施问题。同一构建过程中，`cmake-data` 和 `git-core` 也遭遇了相同的 HTTP/2 错误，只是碰巧在后续重试中成功，而 `gcc-c++` 在两次失败后不再有可用镜像。

## 修复方向

### 方向 1（置信度: 高）

**无需修改 PR 代码。** 等待 openEuler 软件仓库镜像站的 HTTP/2 服务恢复稳定后，重新触发 CI 构建（re-run / retry）。该问题属于仓库服务端的瞬时故障，与 Dockerfile 内容无关。

### 方向 2（置信度: 中）

若该仓库镜像站 HTTP/2 问题持续出现，可在 Dockerfile 的 `dnf install` 前添加重试/降级逻辑，例如：
- 为 `dnf` 配置增加 `retries` 和 `timeout` 参数
- 或在 `dnf install` 外层包裹重试循环（如 `for i in 1 2 3; do dnf install -y ... && break; sleep 30; done`）

## 需要进一步确认的点

- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）在 CI 构建时间点（2026-07-13 07:04 UTC 前后）是否存在已知的 HTTP/2 服务异常或中断。
- 确认同一时间段同类仓库（如 24.03-lts-sp3）的其他 PR CI 构建是否也出现了相同模式的 `Curl error (92)` HTTP/2 流错误，以判断是偶发故障还是系统性退化。
