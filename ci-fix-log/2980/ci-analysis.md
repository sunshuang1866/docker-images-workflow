# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), HTTP/2, Stream error, INTERNAL_ERROR, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6` — `RUN dnf install` 步骤
- 失败原因: Docker 构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，遇到 HTTP/2 协议层面的流错误（`Curl error (92): INTERNAL_ERROR`）。`cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 的两次重试（stream 65 和 stream 83）均失败，最终 `dnf` 用尽所有镜像后报错退出。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了一个标准格式的 Dockerfile（含常规的 `dnf install` 依赖安装命令）和配套元数据文件。Dockerfile 中 `dnf install` 命令语法正确，所列包名均为 openEuler 24.03-LTS-SP4 仓库中的标准包。失败由仓库镜像服务器的 HTTP/2 协议层面不稳定引起，属于 CI 基础设施/网络层面的偶发性问题。

## 修复方向

### 方向 1（置信度: 中）
**无需修改代码，触发重新构建。** 该失败由 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端不稳定引起，属于临时性基础设施问题。在 PR 评论中回复触发词（如 `retest` 或 `/retest`）重新触发 CI 构建，大概率可以成功。

### 方向 2（置信度: 低）
**如果多次重试仍失败**，考虑在 Dockerfile 的 `dnf install` 前添加重试机制（如 `dnf install --setopt=retries=10` 或使用 `dnf download` + `rpm -i` 分步重试），但这只是缓解手段，根因仍在仓库端。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 `repo.****.org` 仓库镜像在此期间是否存在已知的 HTTP/2 服务不稳定问题
- 观察同一时间段内其他 24.03-lts-sp4 PR 是否也出现同类 Curl error (92) —— 如果是，则确认为仓库端问题
- 如果多次重试均失败，需检查 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 是否已从仓库中移除（版本过旧被清理），此时可能是与模式02类似的版本不存在问题
