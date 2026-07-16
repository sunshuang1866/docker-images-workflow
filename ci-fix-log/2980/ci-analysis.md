# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 时遭遇多次 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），所有镜像源均已尝试但全部失败。部分其他包（`cmake-data`、`git-core`）也出现相同错误，虽然 cmake-data 经重试后成功下载，但 `gcc-c++` 最终所有重试均告失败。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 新增了一个 Grads 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，其 `dnf install` 命令本身语法和包名均正确（依赖解析成功，共列出 258 个待安装包）。失败的直接原因是 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 镜像服务在 CI 构建期间出现流中断问题，属于临时的基础设施网络故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个 CI 基础设施问题（`infra-error`），表现为 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 服务端异常中断流连接。建议重新触发 CI 构建（retry），通常此类镜像源瞬时波动在重试后即可恢复。如果重试多次仍然失败，则需排查 CI 构建节点与 `repo.****.org` 之间的网络链路健康状况，或考虑在 Dockerfile 中为 `dnf` 增加 `--retries` 和 `--setopt=timeout=` 参数以提高抗抖动能力。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 openEuler 24.03-LTS-SP4 仓库服务当时是否存在已知中断或性能降级。
- 若持续重试失败，确认 CI 节点到该仓库的网络链路是否正常（是否存在代理/防火墙干预 HTTP/2 连接）。
