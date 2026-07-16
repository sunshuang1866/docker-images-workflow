# 修复摘要

## 修复的问题
CI 基础设施故障，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败是由于 `ecs-build-docker-aarch64-04-sp` aarch64 构建节点在从 `repo.openeuler.org` 下载 RPM 包（git-core、gcc-c++、guile 等）时发生 HTTP/2 流层错误（`Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR (err 2)`），属于临时性网络基础设施故障，与 PR #2991 新增的 vvenc Dockerfile 及其它元数据文件无关。Dockerfile 中的 `dnf install` 命令和包名均为 openEuler 24.03-LTS-SP4 仓库的有效配置，日志中也显示依赖解析成功（156 个待安装包）。

建议在 CI 侧重新触发该构建 job 以验证是否为一次性网络抖动。

## 潜在风险
无