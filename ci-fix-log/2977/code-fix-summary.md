# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：`repo.openeuler.org` 在 aarch64 构建时段 HTTP/2 连接不稳定（Curl error 92: INTERNAL_ERROR, Curl error 56: SSL_ERROR_SYSCALL），导致 `vim-common` 等 RPM 包下载失败，yum install 整体退出。

## 修改的文件
无

## 修复逻辑
该失败属于 CI 基础设施层面的瞬时网络故障（`repo.openeuler.org` 服务端 HTTP/2 流异常关闭），与 PR #2977 新增的 Dockerfile 内容无关。Dockerfile 语法正确，`yum install` 包列表合法，所有 173 个依赖包均已成功解析并开始下载（部分包在重试后成功），仅 `vim-common` 在所有镜像源重试后仍失败。

修复方向：**重试 CI 构建即可**。若多次重试后仍失败，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 aarch64 仓库服务状态或 CI runner 到源站的网络链路质量。

## 潜在风险
无