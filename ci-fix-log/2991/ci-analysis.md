# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: "仓库HTTP/2流错误"
- 新模式症状关键词: "Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, dnf install"

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
- 失败原因: CI aarch64 runner 上 `dnf install` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时遭遇 HTTP/2 协议层流错误（Curl error 92），多个包（git-core、gcc-c++、guile）的下载流被远端异常关闭。其中 git-core 重试后成功、gcc-c++ 两次均失败（仍在队列中）、guile 耗尽所有镜像重试后彻底失败，导致构建终止。

### 与 PR 变更的关联
**与 PR 无关。** 此次 PR 新增的 Dockerfile 内容完全正确——`dnf install -y git gcc gcc-c++ make cmake` 是标准的依赖安装命令，语法无误。失败根因是 `repo.openeuler.org` 仓库在 aarch64 节点上存在 HTTP/2 服务端流中断问题，属于 CI 基础设施层面的瞬时网络故障，与 PR 代码变更无关。该 Dockerfile 在其他时间段或重试后可能完全正常通过。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码，重试 CI 即可。** 这是 `repo.openeuler.org` 仓库 HTTP/2 服务的瞬时故障，属 infra-error。Code Fixer 无需对 PR 内容做任何修改。建议在 CI 流水线中直接 re-run 该 job，等待仓库端恢复后重新构建。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 仓库在 aarch64 节点的 HTTP/2 服务状态是否已恢复正常。
- 若多次重试后该问题持续复现，需确认是否需要在 dnf 配置中禁用 HTTP/2 或切换镜像源（但当前日志仅显示单次构建失败，更倾向认定为瞬时故障）。
