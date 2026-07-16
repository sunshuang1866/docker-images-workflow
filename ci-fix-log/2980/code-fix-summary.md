# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 传输层瞬时故障导致 RPM 包下载失败。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认：
- `dnf install` 的依赖解析阶段已成功完成（258 个包均有效且存在于仓库中），Dockerfile 中声明的包名完全正确。
- 失败发生在 RPM 包下载阶段，日志显示 `Curl error (92): Stream error in the HTTP/2 framing layer`，多个包（cmake-data、git-core、gcc-c++）均受波及。cmake-data 和 git-core 通过 dnf 内置重试机制成功下载，仅 gcc-c++ 两次重试均失败而最终出错。
- 根因是 openEuler 24.03-LTS-SP4 软件仓库镜像服务器 `repo.****.org` 的 HTTP/2 传输层不稳定，属于基础设施层面问题，与 PR 代码变更无关。

**建议操作**：在镜像服务器恢复稳定后重新触发 CI 构建即可，无需修改任何源代码。

## 潜在风险
无