# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try, dnf install

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
- 失败位置: Dockerfile 第 6 行 `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: CI 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 的 HTTP/2 传输层反复出现流错误（`Curl error 92: Stream error in the HTTP/2 framing layer`），导致多个 RPM 包（`git-core`、`gcc-c++`、`guile`）下载失败。`guile` 包的所有镜像/重试均耗尽（"No more mirrors to try"），dnf 安装以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅新增了一个 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）及其关联的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 内容完全正确——安装了构建 vvenc 所需的 `git gcc gcc-c++ make cmake`。失败纯粹是因为 openEuler 官方仓库（`repo.openeuler.org`）在该次 CI 运行期间 HTTP/2 服务不稳定，在 aarch64 架构上无法正常下载 RPM 包。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施问题，无需修改代码。** 失败是 `repo.openeuler.org` 镜像站在构建窗口内的瞬时网络/HTTP/2 服务异常（`Curl error 92`）导致的。应在 CI 侧重试该 job（retry），或等待仓库服务恢复后重新触发构建。PR 的 Dockerfile 和元数据文件本身没有任何错误。

### 方向 2（置信度: 低）
如果在多次重试后该问题持续出现，可以考虑在 Dockerfile 中为 `dnf` 添加重试参数（如 `--setopt=retries=10`），或将 `dnf install` 拆分为多次调用以降低单次下载的包数量。但这属于治标不治本，根因仍是上游仓库的 HTTP/2 服务器问题。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否存在已知的 HTTP/2 服务问题或 aarch64 架构的包服务中断。
- 确认其他同期构建的 aarch64 job 是否也遇到同样的 `Curl error 92` 问题——若存在同类失败则进一步印证是仓库侧问题。
- 重新触发一次 CI 构建，观察问题是否自行消失（临时性网络波动）。

## 修复验证要求
不适用。本次失败为 infra-error，与 PR 代码变更无关，无需对文件进行修复。
