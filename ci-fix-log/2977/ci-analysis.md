# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2传输中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner 上构建 Docker 镜像时，`yum install` 从 `repo.openeuler.org` 下载 RPM 包过程中，openEuler 官方仓库 CDN 出现多次 HTTP/2 传输层中继错误（`Stream error / INTERNAL_ERROR`）和 SSL 读取失败（`SSL_ERROR_SYSCALL`），其中 `kernel-headers`、`gcc`、`perl-MIME-Base64` 三个包在重试后成功下载，但 `vim-common` 在所有镜像重试耗尽后仍下载失败，导致整个 `yum install` 事务失败。

日志中出现了 4 次网络级下载错误：
| 失败包 | 错误类型 | 最终结果 |
|--------|---------|---------|
| gcc-12.3.1 | Curl error (92): HTTP/2 stream INTERNAL_ERROR | 重试后成功 |
| kernel-headers-6.6.0 | Curl error (92): HTTP/2 stream INTERNAL_ERROR | 重试后成功 |
| perl-MIME-Base64-3.16 | Curl error (56): SSL_ERROR_SYSCALL | 重试后成功 |
| vim-common-9.0.2092 | Curl error (92): HTTP/2 stream INTERNAL_ERROR | **重试耗尽，失败** |

### 与 PR 变更的关联
**无关。** PR 仅新增了一个标准的 Dockerfile，包含常规的 `yum install` 依赖安装步骤，语法正确、包名有效（与同仓库同软件的 `24.03-lts-sp3` 版本逻辑一致）。失败纯粹由 openEuler 官方 RPM 仓库的 CDN 网络不稳定导致，与 Dockerfile 内容、包列表、构建参数均无关系。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施侧重试 / 重新触发。** 该失败是 openEuler 官方仓库 `repo.openeuler.org` 在特定时段对 aarch64 架构的 HTTP/2 传输不稳定所致（同一次构建中 173 个包中有 169 个正常下载，仅 4 个触发网络错误）。直接在 CI 中重新触发构建（retrigger），大概率可成功。这不是代码层面的问题，Code Fixer 无需修改任何文件。

## 需要进一步确认的点
- 无。日志中网络错误信息清晰完整，根因明确为 CI 基础设施 / 上游仓库网络问题，无需在代码库中进一步查阅。

## 修复验证要求
无。该失败为 infra-error，不涉及代码修改，无需验证。
