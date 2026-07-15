# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org, dnf install

## 根因分析

### 直接错误
```
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

此外，构建过程中还出现了两次同类 `[MIRROR]` 警告（被自动重试恢复）：
- `git-core-2.54.0-2.oe2403sp4.aarch64.rpm` — HTTP/2 stream 43 异常，但重试后下载成功（#7 1273.6 → #7 1513.9）
- `gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm` — HTTP/2 stream 39 和 stream 51 均异常，日志中未见明确成功记录（#7 1419.8 / #7 1548.4）

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（dnf install 步骤）
- 构建节点: `ecs-build-docker-aarch64-04-sp`（aarch64）
- 失败原因: `repo.openeuler.org` 的 HTTP/2 服务器在 aarch64 runner 下载 `guile` RPM 包时反复发生 HTTP/2 流层协议错误（`INTERNAL_ERROR`），所有镜像源均已尝试但均失败，dnf 无法完成包安装。

### 与 PR 变更的关联

**此次失败与 PR 改动无关。** PR 仅添加了一个语法正确的 vvenc Dockerfile（含标准 `dnf install` 构建依赖声明）及配套元数据文件更新。失败发生在 `dnf install -y git gcc gcc-c++ make cmake` 这一通用包安装步骤，根因是 `repo.openeuler.org` 仓库服务器的 HTTP/2 流协议异常。同一构建过程中 `git-core` 和 `gcc-c++` 包也出现了相同类型的 `Curl error (92)` 镜像源告警，进一步证明这是仓库基础设施的间歇性问题，而非 Dockerfile 编写错误。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。这是 `repo.openeuler.org` 仓库服务器的临时性 HTTP/2 协议故障，与 PR 代码完全无关。大部分同类情况下，重试即可通过——日志中 `git-core` 包在出现一次镜像错误后重试成功即为佐证。Code Fixer 无需做任何代码修改。

### 方向 2（置信度: 低）
如果多次重试仍然失败，可能表明 `openEuler-24.03-LTS-SP4` 的 aarch64 仓库中 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 文件确实存在服务端问题（文件损坏或仓库元数据不一致）。此时需联系 openEuler 基础设施团队排查 SP4 仓库的 aarch64 通道状态。

## 需要进一步确认的点

- `gcc-c++` 包在两次镜像错误后是否实际下载成功（日志中未见明确成功记录，但最终失败包是 guile 而非 gcc-c++），这有助于判断仓库不稳定性的范围。
- 如果重试仍然失败，建议对比 x86_64 runner 上同一 Dockerfile 的构建结果（当前仅有 aarch64 日志），判断问题是架构特定还是仓库全局性的。

## 修复验证要求

无。此失败类型为 `infra-error`，无需代码修复，仅需重试 CI。
