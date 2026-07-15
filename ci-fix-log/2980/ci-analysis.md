# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, [MIRROR], dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: Dockerfile:6（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在通过 HTTP/2 传输 RPM 包时频繁出现 `Stream error (INTERNAL_ERROR err 2)`，多个包（`cmake-data`、`git-core`、`gcc-c++`）的下载均遭遇此错误。其中 `cmake-data` 和 `git-core` 重试后成功下载，但 `gcc-c++`（13MB）两次重试均失败，最终 dnf 放弃并报错退出。

### 与 PR 变更的关联
**无关**。此 PR 仅新增了 4 个文件：
- `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（新增，30行）
- `Others/grads/README.md`（新增1行表格条目）
- `Others/grads/doc/image-info.yml`（新增1行表格条目）
- `Others/grads/meta.yml`（新增2行 meta 条目）

Dockerfile 中的 `dnf install` 命令语法正确，包名与同类镜像（如 `24.03-lts-sp3`）一致。失败纯粹是因为构建时 openEuler 仓库镜像的 HTTP/2 层不稳定，属于 CI 基础设施的临时性网络故障，与 PR 代码变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可**。此错误为 openEuler 仓库镜像的 HTTP/2 流传输层临时故障（Curl error 92: INTERNAL_ERROR），属于基础设施层面的间歇性问题。日志中 `cmake-data` 和 `git-core` 也在首次下载时遇到同类错误、但重试后成功，说明仓库镜像并非彻底不可达，只是当时 HTTP/2 连接不稳定。重新触发 CI 构建大概率可以通过。Code Fixer 无需修改任何代码。

## 需要进一步确认的点
无需进一步确认。根因明确为网络基础设施问题，且分析置信度高。

## 修复验证要求
无需修复操作。若重新触发 CI 构建后仍失败，需检查 openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 的健康状态，或联系基础设施团队排查 `ecs-build-docker-x86-03-sp` runner 到仓库镜像的网络连通性。
