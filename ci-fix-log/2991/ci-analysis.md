# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败原因: 构建在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，`repo.openeuler.org` 的 24.03-LTS-SP4 aarch64 仓库发生 HTTP/2 协议层流错误（Curl error 92: `INTERNAL_ERROR`）。多个 RPM 包（git-core、gcc-c++、guile）均遭遇此错误；git-core 和 gcc-c++ 在重试后下载成功，`guile` 包因所有镜像均已尝试过而最终失败，导致 `dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码无关。** 该 PR 新增的 Dockerfile 内容完全正确——基于 `openeuler:24.03-lts-sp4` 基础镜像，通过 `dnf install` 安装标准编译工具链（git、gcc、gcc-c++、make、cmake）。失败根因是 openEuler 官方 RPM 仓库 `repo.openeuler.org` 的 HTTP/2 服务在该时间窗口内不稳定，属于 CI 基础设施层面的网络问题。PR 的其他变更（README.md、image-info.yml、meta.yml）仅为文档和元数据补充，不涉及任何构建逻辑。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，直接触发重试即可。** 这是 `repo.openeuler.org` RPM 仓库的瞬时 HTTP/2 协议层故障，属于不可控的基础设施问题。在 CI 系统中对失败的 aarch64 build job 进行 re-run，大概率可成功通过。多个包（git-core、gcc-c++）在重试后均下载成功，说明该仓库并非完全不可用，只是 HTTP/2 流偶发中断。

### 方向 2（置信度: 中）
如果方向 1 多次重试仍失败，可检查 `repo.openeuler.org` 的 aarch64 仓库服务状态是否已恢复。若仓库持续不可用，需联系 openEuler 基础设施团队排查 HTTP/2 后端服务问题。

## 需要进一步确认的点
（无——日志直接指向网络层错误，根因明确。）

## 修复验证要求
无。本次故障与 PR 代码变更无关，不需要修改任何源文件或正则表达式。
