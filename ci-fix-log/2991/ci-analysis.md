# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 镜像站流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI aarch64 runner 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，仓库服务器的 HTTP/2 连接反复出现帧层流错误（`INTERNAL_ERROR`），导致 `git-core`、`gcc-c++`（两次）、`guile` 等多个包下载失败，最终 `guile` 包因"所有镜像均已尝试"而致命失败，`dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准 Dockerfile（安装 `git gcc gcc-c++ make cmake` 后编译 vvenc）及相关元数据文件（README.md、image-info.yml、meta.yml）。失败原因是 `repo.openeuler.org` 镜像站服务器在 aarch64 架构上返回 HTTP/2 流错误，属于 CI 基础设施/上游仓库问题。Dockerfile 自身的语法和构建逻辑均无问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 此失败为 openEuler 官方镜像站 `repo.openeuler.org` 在 SP4 aarch64 仓库上的临时 HTTP/2 服务端问题。建议：
1. **重试 CI**：等待镜像站恢复后重新触发构建（`/retest` 或类似命令）。
2. 若持续失败，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager` 切换镜像源或强制使用 HTTP/1.1（如 `echo "http2=false" >> /etc/dnf/dnf.conf`），但**不建议仅为一个镜像的临时网络问题而修改 Dockerfile 代码**。

## 需要进一步确认的点
- x86_64 架构的同 PR 构建是否成功（若成功，证实问题仅限 aarch64 的 SP4 仓库节点）。
- `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 路径下的 RPM 包是否在其他时间/环境可正常下载。
- 若多次重试均失败，需确认是否是 SP4 aarch64 仓库中 `guile` 等包的文件本身损坏或缺失，而非临时网络问题。
