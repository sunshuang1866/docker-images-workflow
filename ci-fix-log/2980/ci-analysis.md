# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建节点在下载 openEuler 24.03-LTS-SP4 RPM 仓库中的 `gcc-c++` 包（13 MB）时，仓库服务器的 HTTP/2 连接连续两次出现流层错误（`Curl error 92: INTERNAL_ERROR`），dnf 重试所有可用镜像源后均失败。另外两个包 `cmake-data` 和 `git-core` 也曾出现同类 HTTP/2 错误，但重试后下载成功。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 Dockerfile（含正确的 `dnf install` 包列表）、README.md 条目、image-info.yml 条目和 meta.yml 条目，均为规范的纯增量变更。Dockerfile 中 `dnf install` 列出的所有包名（`gcc-c++`, `cmake`, `git` 等）在 openEuler 24.03-LTS-SP4 仓库中均确实存在（日志中 Dependencies resolved 阶段已列出完整的 258 个待安装包及版本号，证明包名无误）。失败根因是 `repo.****.org` 仓库服务器在处理 HTTP/2 帧时发生了服务端内部错误，属于 CI 基础设施/网络问题。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。HTTP/2 流错误是服务端瞬态故障，通常在下一轮 CI 运行中不会重现。若重试后仍失败，可在 Dockerfile 的 `dnf install` 前插入重试机制（如将单条 `dnf install` 包装在循环中反复重试），或临时关闭 DNF 的 HTTP/2 协议尝试（`echo "http2=false" >> /etc/dnf/dnf.conf`），待仓库服务端修复后再还原。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 RPM 仓库（`repo.****.org`）在 CI 运行时段（2026-07-13 07:04 UTC）是否存在服务端 HTTP/2 实现缺陷或临时过载。可通过在 CI 节点上手动执行 `curl --http2 -O <gcc-c++ RPM URL>` 验证。
- 该仓库是否对来自 CI runner IP 段的 HTTP/2 高频连接有速率限制或连接数限制，导致部分流被服务端异常关闭。
