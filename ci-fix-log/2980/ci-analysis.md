# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建节点从 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）下载 `gcc-c++` RPM 包时，HTTP/2 传输层发生流错误（`Curl error (92): HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），两次重试均失败，所有镜像源均已尝试完毕，`dnf install` 以 exit code 1 终止。

日志中还出现了 `cmake-data`（#7 1199.1）和 `git-core`（#7 1776.2）的同类 Curl error (92)，但这两个包在重试后成功下载。最终只有 `gcc-c++`（13MB 的大包）因重试耗尽而失败，说明网络不稳定对大型包下载影响更显著。

### 与 PR 变更的关联
**与 PR 改动无关。** 该失败属于 CI 基础设施层的网络问题：
- PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 和配套元数据文件（README.md、image-info.yml、meta.yml），所有变更都是合法的 Docker 镜像新增操作。
- `dnf install` 中列出的所有软件包名称在 openEuler 24.03-LTS-SP4 仓库中均存在（日志第 724 行成功列出了完整的依赖解析结果，共 258 个包），说明 Dockerfile 语法和包名正确无误。
- 错误本质是 CI runner 与 RPM 仓库间的 HTTP/2 协议层网络传输异常，同一次构建中多个包（cmake-data、git-core）都遭遇了同类错误。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该失败是 openEuler 24.03-LTS-SP4 RPM 仓库（`repo.****.org`）的 HTTP/2 服务端在 CI 构建时段的临时网络波动导致，与代码无关。可以：
- 直接重新触发 CI 构建（`retest`），大概率能够通过。
- 如果反复失败，检查 `repo.****.org` 仓库在该时段的服务可用性和 HTTP/2 协议层配置。

### 方向 2（置信度: 低）
**为 dnf install 添加重试机制**。在 Dockerfile 的 `dnf install` 命令前增加 `dnf makecache` 或使用 `--retries` 参数（如果 dnf 版本支持），但这是通用优化而非针对此特定问题的必要修复。

## 需要进一步确认的点
- 确认 `repo.****.org` 在 CI 构建时间（2026-07-13 07:04 UTC 前后）是否有服务波动或 HTTP/2 代理层异常。
- 确认同批次的 aarch64 runner 上该 Dockerfile 的构建结果——如果 aarch64 构建成功而仅 x86_64 失败，则进一步支持网络瞬时故障的判断；如果两架构均失败，则可能是仓库侧 HTTP/2 配置存在系统性问题。
