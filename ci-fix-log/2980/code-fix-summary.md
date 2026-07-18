# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于 infra-error（基础设施问题），由 openEuler 24.03-LTS-SP4 RPM 仓库的 HTTP/2 流传输异常导致，与 PR 代码变更无关。

## 修改的文件
无。

## 修复逻辑
CI 失败的直接原因是 `dnf install` 下载 gcc-c++ RPM 包时遭遇 Curl error (92): Stream error in the HTTP/2 framing layer，DNF 耗尽镜像列表后构建终止。这是一个随机的网络基础设施问题——同一次构建中其他包（cmake-data、git-core）重试后均成功下载，gcc-c++ 两次尝试均失败。Dockerfile 中 `dnf install` 命令的语法和包名均正确（258 个依赖包已成功解析），无需修改任何代码。**建议直接重试 CI 构建**，大概率可通过。

## 潜在风险
无。