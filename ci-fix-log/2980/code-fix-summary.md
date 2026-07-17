# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 openEuler 24.03-LTS-SP4 软件包镜像仓库 HTTP/2 传输层瞬态网络故障（Curl error 92: Stream error in the HTTP/2 framing layer），属于 CI 基础设施问题（infra-error），与 PR #2980 新增的 GrADS Dockerfile 及任何代码变更无关。

## 修改的文件
无。该失败为纯粹的基础设施/网络瞬态故障，Dockerfile 中的 `dnf install` 包列表在语法和内容上均无错误，不需要对任何文件进行修改。

## 修复逻辑
分析报告确认：cmake-data 和 git-core 通过镜像重试成功下载，但 gcc-c++（13 MB 较大包）经过两次重试后仍失败。从其他包重试成功的现象判断，这是单次构建中的网络瞬态，而非持续性仓库问题。正确的处理方式是触发 CI 重试（re-run），在仓库服务正常的时间窗口内，相同的 `dnf install` 命令应能正常完成。

## 潜在风险
无。未对任何代码文件进行修改，不会引入任何风险。