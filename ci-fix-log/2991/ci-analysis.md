# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, repo.openeuler.org, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: aarch64 CI runner（`ecs-build-docker-aarch64-04-sp`）在通过 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个独立包（git-core、gcc-c++、guile）先后遭遇 HTTP/2 流错误（Curl error 92: `INTERNAL_ERROR`），最终 `guile` 包耗尽重试次数后导致整个 `dnf install` 命令以 exit code 1 失败。

### 与 PR 变更的关联
**无关**。该 PR 仅新增了一个标准 Dockerfile（安装 git、gcc、gcc-c++、make、cmake 后编译 vvenc 1.14.0），Dockerfile 语法和依赖声明均无问题。失败根因是 `repo.openeuler.org` 仓库在 aarch64 runner 上的 HTTP/2 连接不稳定，属于 CI 基础设施/网络问题。git-core 虽在首次失败后重试成功，但 gcc-c++（两次失败）和 guile（一次失败）持续失败，表明网络波动是系统性的而非偶发的单文件问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。这是 `repo.openeuler.org` 仓库的临时性网络波动导致的 infra-error，与 PR 代码无关。等待 openEuler 镜像源恢复稳定后重新触发 CI 构建即可。Code Fixer 无需处理。

## 需要进一步确认的点
- 同一时间段的 amd64 runner 上该构建是否也失败了（日志中仅包含 aarch64 runner 的输出）。如果 amd64 构建成功，则进一步确认问题局限于 aarch64 网络链路。
- `repo.openeuler.org` 在 aarch64 runner 所在网络环境中是否存在周期性稳定性问题，若此模式频繁出现，可考虑在 Dockerfile 中为 `dnf install` 添加 `--retries` 参数或切换至更稳定的镜像源。
