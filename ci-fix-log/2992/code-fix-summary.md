# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题——openEuler 24.03-LTS-SP4 仓库镜像服务器在 HTTP/2 连接中出现瞬态流中断（Curl error 92: INTERNAL_ERROR），导致 `dnf install` 下载 RPM 包失败。

## 修改的文件
无

## 修复逻辑
此失败与 PR 的代码变更无关。`Dockerfile` 中 `dnf install` 命令语法和包名列表均正确。失败点位于从 `repo.****.org` 下载 RPM 包的外部阶段，属于镜像仓库服务器的 HTTP/2 连接层瞬时故障。建议直接重新触发 CI 构建（retry），大概率可以通过。若多轮重试均失败，需排查 openEuler 仓库镜像的 HTTP/2 服务端配置。

## 潜在风险
无