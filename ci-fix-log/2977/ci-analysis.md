# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: YUM 镜像站 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install

## 根因分析

### 直接错误

```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
```

在整个构建过程中，多个 RPM 包在下载时遭遇了 HTTP/2 流错误，包括：

| 包名 | 错误类型 | 最终结果 |
|------|---------|---------|
| gcc-12.3.1-110 (30MB) | curl(92): HTTP/2 INTERNAL_ERROR | 重试后成功 (7:01) |
| kernel-headers-6.6.0-159 (1.7MB) | curl(92): HTTP/2 INTERNAL_ERROR | 重试后成功 (4:59) |
| perl-MIME-Base64-3.16-2 (19KB) | curl(56): SSL_ERROR_SYSCALL | 重试后成功 |
| vim-common-9.0.2092-36 (7.8MB) | curl(92): HTTP/2 INTERNAL_ERROR | **失败，所有镜像源已耗尽** |

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 构建环境中 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）从 `repo.openeuler.org` 下载 RPM 包时，多个包遭遇 HTTP/2 流错误（`INTERNAL_ERROR` / `SSL_ERROR_SYSCALL`），其中 `vim-common` 经过所有镜像源重试后仍未成功，导致 yum 安装失败，构建中止。173 个包中有 172 个最终下载成功，仅 `vim-common` 因镜像源耗尽而失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的变更是新增一个 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，Dockerfile 中 `yum install` 命令的包列表和语法均正确无误。失败原因是 CI 基础设施层面 `repo.openeuler.org` 的 aarch64 仓库在构建时段出现了 HTTP/2 连接不稳定问题。

## 修复方向

### 方向 1（置信度: 中）
**重试触发 CI 重新构建。** 此失败为 transient 网络问题，`repo.openeuler.org` 的 aarch64 SP4 仓库在构建时段出现了 HTTP/2 连接不稳定。通常情况下重新触发构建即可通过，无需修改代码。如果重试后仍然失败，则可能是 SP4 aarch64 仓库本身存在系统性问题。

### 方向 2（置信度: 低）
**在 yum install 前添加镜像源配置或重试策略。** 如果多次重试仍失败，可考虑在 Dockerfile 的 `yum install` 前添加 yum 配置以增加重试次数或使用备用镜像源，减少单次网络波动导致构建失败的概率。

## 需要进一步确认的点
1. 确认 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 仓库在多个时段是否存在持续性的 HTTP/2 连接问题（若持续失败，则非 transient 问题，需联系 openEuler 基础设施团队排查仓库侧 CDN/服务器问题）。
2. 检查同批次其他 SP4 aarch64 构建 job 是否也出现类似错误——如果是，则是仓库侧系统性问题；如果只有本 job 失败，则是节点或临时网络波动。
3. 确认 `vim-common` 这个间接依赖是否可以避免安装（当前是通过 `git` → `perl-Git` → `vim-common` 拉入的间接依赖），在不影响构建的情况下减少下载包数量以降低失败概率。
