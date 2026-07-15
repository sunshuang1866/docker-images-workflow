# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施/网络瞬时故障（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 aarch64 构建节点执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 协议层流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`），guile 包耗尽所有镜像重试后永久失败。这是 `repo.openeuler.org` 镜像站的 HTTP/2 服务端/网络问题，PR 新增的 Dockerfile 中 `dnf install` 命令格式与项目中其他 vvenc Dockerfile 完全一致，所列包名均为有效包名。PR 改动未引入任何导致此失败的因素。

**建议操作**：重新触发 CI 构建。如果同一 runner（`ecs-build-docker-aarch64-04-sp`）持续出现同类 HTTP/2 错误，需排查该 runner 到 `repo.openeuler.org` 的网络连接或 HTTP/2 代理兼容性。

## 潜在风险
无