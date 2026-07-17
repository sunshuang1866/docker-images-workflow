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
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

此外还有两个类似的 HTTP/2 流错误（但不致命）：
- `cmake-data-3.31.12-1.oe2403sp4.noarch.rpm` — Curl error (92)，但重试后成功
- `git-core-2.54.0-2.oe2403sp4.x86_64.rpm` — Curl error (92)，但重试后成功

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像服务器在处理 HTTP/2 请求时发生内部流错误（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 包连续两次下载中断、所有镜像重试耗尽后安装失败。同一构建中 `cmake-data` 和 `git-core` 也遭遇了同类 HTTP/2 流错误，但通过重试成功。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅做了以下操作：
1. 新增文件 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（30 行，全新）
2. 更新 `Others/grads/README.md`（添加 1 行表格条目）
3. 更新 `Others/grads/doc/image-info.yml`（添加 1 行表格条目）
4. 更新 `Others/grads/meta.yml`（添加 2 行路径映射）

这些都是标准的添加新镜像所需元数据，不涉及任何能导致 HTTP/2 网络错误的变更。失败发生在构建该新 Dockerfile 时，`dnf install` 从外部仓库下载依赖包过程中遭遇了仓库服务器的 HTTP/2 协议问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，等待 CI 基础设施恢复后重试。** 错误根因是 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在 CI 构建时存在 HTTP/2 流协议问题。同一构建中同一仓库的其他包（`cmake-data`、`git-core`）也出现了相同的 Curl error (92)，只是重试后成功；`gcc-c++` 不幸两次尝试均失败。这是**临时性基础设施故障**，PR 代码本身没有错误。建议 re-trigger CI 构建。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像在 CI 构建网络的当前可达性及 HTTP/2 服务稳定性。
- 如果该仓库持续不稳定，可能需要将 Dockerfile 中的 dnf 仓库源切换到备用镜像站，或在 `dnf install` 命令中添加 `--setopt=retries=10` 等重试参数以增大容错率。
- 确认其他基于 `openeuler:24.03-lts-sp4` 基础镜像的 Dockerfile 是否也受同类 HTTP/2 错误影响（从日志看，`cmake-data` 和 `git-core` 也遭遇了相同错误，仅因重试成功才未导致失败）。

## 修复验证要求
无。此为 infra-error，不涉及代码修改。
