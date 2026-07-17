# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try

## 根因分析

### 直接错误

```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多次遭遇 HTTP/2 流错误（Curl error 92），其中 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 重试耗尽所有 mirrors 后彻底失败，导致整个 dnf 事务中断（exit code 1）。

### 与 PR 变更的关联

**与 PR 无关。** PR 仅新增了一个标准的 vvenc Dockerfile，其中的 `dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 命令语法完全正确，所请求的包名均存在于 openEuler 24.03-LTS-SP4 仓库中（dnf 已成功解析依赖关系并列出 156 个待安装包）。失败原因是构建期间 `repo.openeuler.org` 的 HTTP/2 协议层出现间歇性流中断，属于 CI 基础设施/上游仓库服务端问题，与本次 PR 的任何代码变更无关。

值得注意的是，同一个 dnf 事务中至少有 4 个不同包（`git-core`、`gcc-c++` 两次、`guile`）经历了 Curl error 92，其中前三者通过 mirror 重试最终成功，只有 `guile` 穷尽重试后失败。这表明仓库服务端的 HTTP/2 问题具有系统性（并非单个文件的偶发损坏），只是在当前构建中恰好让 `guile` 成为压垮骆驼的最后一根稻草。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 失败原因是 openEuler 官方仓库在构建时刻的 HTTP/2 服务不稳定，与代码无关。等待仓库服务恢复后重试，大概率通过。Code Fixer 无需修改任何代码。

### 方向 2（置信度: 低）
若该 runner 节点（`ecs-build-docker-aarch64-04-sp`）反复出现同类 HTTP/2 错误，可考虑在 Dockerfile 的 `dnf install` 命令中增加 `--retries` 参数以提升容错能力，或联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务端配置。

## 需要进一步确认的点

- `repo.openeuler.org` 的 HTTP/2 服务在此构建时间窗口（2026-07-09 14:08 UTC 左右）是否确实存在已知的服务端问题。如果同时间段其他 PR 的 aarch64 构建也出现类似 Curl error 92，则可进一步确认为服务端故障。
- 该节点 `ecs-build-docker-aarch64-04-sp` 的网络出口到 `repo.openeuler.org` 之间是否存在中间代理或防火墙干扰 HTTP/2 流。若其他 aarch64 runner 节点（如 `-03-sp`）在相同时间构建成功，则问题更倾向于特定节点而非仓库全局。
