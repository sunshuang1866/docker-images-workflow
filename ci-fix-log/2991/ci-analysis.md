# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败原因: `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在通过 HTTP/2 协议下载 RPM 包时，多次出现 HTTP/2 流异常关闭（`INTERNAL_ERROR (err 2)`），导致 `git-core`、`gcc-c++` 包下载失败并触发镜像重试（`[MIRROR]`），最终 `guile` 包（git 的传递依赖）耗尽所有镜像后下载失败，`dnf install` 以退出码 1 结束。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 中 `dnf install -y git gcc gcc-c++ make cmake` 命令本身正确无误，安装的包列表是标准编译工具链，在 `dnf` 阶段正常解析出了 156 个待安装包。失败纯因 openEuler 官方镜像站 `repo.openeuler.org` 的 HTTP/2 服务端在传输 aarch64 RPM 包时出现流协议错误，属于 CI 基础设施/上游仓库问题，非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。该错误为 openEuler 官方镜像站 HTTP/2 服务的瞬时性问题，多数情况下重新触发 CI 构建即可绕过。若问题持续出现，则可能是镜像站 HTTP/2 实现与特定 aarch64 包的交互稳定性问题。

### 方向 2（置信度: 中）
**为 dnf install 添加重试参数**。在 Dockerfile 第 6 行的 `dnf install` 命令中追加 `--setopt=retries=10` 或 `--setopt=timeout=120`，提高 DNF 对网络波动的容忍度，减少单次镜像失败导致整体安装中断的概率。注意：此修改会改变 Dockerfile 内容，需确认符合项目规范后再实施。

### 方向 3（置信度: 低）
**在 `dnf install` 前配置备用镜像源**。在 RUN 命令中预先向 `/etc/yum.repos.d/` 添加华为云镜像站（`repo.huaweicloud.com`）或其他可靠的 openEuler 镜像，作为 `repo.openeuler.org` 的 fallback。此方向改动较大，如方向 1 重试即可恢复则无需采用。

## 需要进一步确认的点
- 该镜像站 HTTP/2 问题是否为 openEuler 24.03-LTS-SP4 aarch64 仓库的已知持续性故障，还是临时波动。可通过查看同一时间段内其他 PR 的 aarch64 构建日志确认。
- x86_64 架构的同 PR 构建是否成功（日志未提供）。如果 x86_64 成功而 aarch64 失败，进一步确认问题仅限 aarch64 仓库。
- `guile` 包的具体 RPM 文件大小（6.3 MB）是否在 HTTP/2 传输中有特殊的流分段行为，导致更容易触发该错误。
