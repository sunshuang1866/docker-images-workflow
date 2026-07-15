# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, repo.openeuler.org, No more mirrors to try

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
- 失败原因: 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 镜像站对多个 RPM 包（git-core、gcc-c++、guile）返回 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），重试耗尽后 `guile` 包下载失败，导致整个 dnf 事务回滚。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增的 Dockerfile 内容正确——`dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 是常规合法的包安装命令。失败根因是 openEuler 24.03-LTS-SP4 的 aarch64 仓库镜像在构建时刻存在 HTTP/2 服务端流传输异常，属于基础设施层面的暂时性故障。Dockerfile 第 6 行的指令本身没有任何语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。这是 CI 基础设施侧 `repo.openeuler.org` 镜像源在 aarch64 上的 HTTP/2 传输层暂时性故障，与 PR 代码无关。等待镜像站恢复后重新触发 CI 构建即可通过。如果问题持续出现，需要在 CI 配置层面对 dnf 添加重试机制（如 `--retries` 或 `dnf makecache` 预检），但这不属于 Dockerfile 修改范畴。

## 需要进一步确认的点
- `repo.openeuler.org` 的 aarch64 仓库在构建时刻是否存在已知的服务端 HTTP/2 问题（可查阅 openEuler 基础设施状态页面）
- 该失败是否仅出现在 aarch64 架构（日志中 runner 为 `ecs-build-docker-aarch64-04-sp`），x86_64 构建是否正常通过

## 修复验证要求
无需验证。本次失败为 infra-error，不存在代码修复。重试 CI 构建即可。
