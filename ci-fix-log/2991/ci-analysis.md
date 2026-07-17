# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install failed

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: `repo.openeuler.org` 镜像站的 openEuler 24.03-LTS-SP4 aarch64 仓库在构建期间出现 HTTP/2 流传输不稳定，多个 RPM 包（git-core、gcc-c++、guile）下载时持续触发 `Curl error (92): Stream error in the HTTP/2 framing layer`，其中 `guile` 包耗尽所有镜像重试后最终下载失败，导致 `dnf install` 命令以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 语法正确、包名有效（`git gcc gcc-c++ make cmake` 均为 openEuler 24.03-LTS-SP4 仓库中的合法包名）。失败是纯粹的 CI 基础设施问题——构建在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行，`repo.openeuler.org` 镜像站对 openEuler 24.03-LTS-SP4 aarch64 架构的软件源在构建期间 HTTP/2 层出现连接中断，属于服务端网络波动。该 Dockerfile 本身无需任何修改。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是 CI 基础设施层面的网络问题（`repo.openeuler.org` 镜像站 HTTP/2 流传输不稳定），与 Dockerfile 内容无关。建议操作：
- 等待镜像站网络恢复后，重新触发 CI 构建即可。
- 若该问题在多次重试后持续出现，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5` 或 `--setopt=retries=5` 参数增加下载重试次数，但这是规避措施而非根因修复。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像站的 openEuler 24.03-LTS-SP4 aarch64 仓库当前健康状况（是否存在 HTTP/2 服务端问题或 CDN 节点故障）。
- 确认该 CI 构建时段是否有其他 aarch64 架构的 SP4 构建任务也遇到同类 HTTP/2 流错误。若为系统性故障，需联系镜像站运维排查。
