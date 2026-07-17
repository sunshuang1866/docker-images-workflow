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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 连接层出现间歇性流错误（Curl error 92: `HTTP/2 stream ... was not closed cleanly: INTERNAL_ERROR (err 2)`），导致 `cmake-data`、`git-core`、`gcc-c++` 三个 RPM 包的下载失败。其中 `cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 在所有镜像重试后仍无法下载（`No more mirrors to try`），最终 `dnf install` 退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 内容（`dnf install` 包列表、编译步骤）在语法和逻辑上均无问题（PR 仅新增了一个 Dockerfile 和三个元数据文件）。失败的直接原因是构建时 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 服务端不稳定，属于 CI 基础设施层的瞬时网络故障。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI 构建。** 这是仓库镜像站的瞬时 HTTP/2 流错误，属于基础设施问题，与代码无关。在镜像站恢复稳定后重新触发 CI 构建极有可能通过。无需修改任何代码。

### 方向 2（置信度: 低）
如果该仓库镜像站频繁出现 HTTP/2 流错误，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `dnf makecache` 或配置 `retries=10` 等 dnf 重试参数，但这不是根本解决方案——根本问题在于镜像站服务器端。

## 需要进一步确认的点
- 该镜像站（`repo.****.org`）是否在构建时段存在已知的服务端故障或维护窗口。
- 如果该问题持续复现，需要确认是否需要更换镜像源或联系镜像站运维排查 HTTP/2 层问题。
