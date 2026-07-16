# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

其他同样受 HTTP/2 流错误影响的包（均来自 `repo.openeuler.org` aarch64 仓库）：
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
```

### 根因定位
- 失败位置: Dockerfile:6（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: `repo.openeuler.org` 的 HTTP/2 传输层反复出现流中断（Curl error 92 / INTERNAL_ERROR），导致多个 aarch64 RPM 包下载失败。其中 `git-core` 和 `gcc-c++` 经重试后下载成功，但 `guile` 包在重试耗尽后仍失败（No more mirrors to try），最终 `dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法完全正确，失败发生在其向 openEuler 官方 RPM 仓库下载 aarch64 架构依赖包的阶段，属于 CI 基础设施侧（仓库 HTTP/2 传输）的瞬时网络问题。构建节点为 `ecs-build-docker-aarch64-04-sp`（aarch64 runner），日志中 CI 预检步骤（镜像规范检查）已通过，排除了元数据格式问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 此失败为 `repo.openeuler.org` RPM 仓库的 HTTP/2 传输层瞬时故障，与本次 PR 的代码变更无关。建议重新触发 CI（retry）即可。在重试前可确认 `repo.openeuler.org` 仓库服务是否恢复正常。

## 需要进一步确认的点
- 确认 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 仓库当前网络可达且 HTTP/2 无异常。若持续出现 Curl error 92，可能是仓库 CDN 节点或 HTTP/2 配置问题，需联系 openEuler 基础设施团队排查。
