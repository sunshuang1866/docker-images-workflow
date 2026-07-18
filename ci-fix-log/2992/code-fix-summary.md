# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 infra-error，系 openEuler 24.03-LTS-SP4 仓库镜像站 HTTP/2 连接不稳定导致的临时网络故障（Curl error 92: Stream error in the HTTP/2 framing layer），与 PR 代码变更无关。

## 修改的文件
无。PR 中所有文件（Dockerfile、README.md、image-info.yml、meta.yml）内容均无错误。

## 修复逻辑
构建日志显示 builder 阶段（`#8`）和 runtime 阶段（`#7`）两个独立 stage 在 `dnf install` 时均遭遇相同的 HTTP/2 流层错误（gcc、gcc-gfortran、glibc-devel、guile 等多个包受影响），镜像站所有 mirror 重试后仍无法下载 gcc 包，导致构建失败。Dockerfile 中 `dnf install` 命令语法和依赖声明均正确（已验证），根因为仓库侧 HTTP/2 服务问题。

**建议操作**：等待仓库恢复后重新触发 CI 构建（`retry`）即可。若后续持续出现此问题，可考虑在 Dockerfile 中 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制使用 HTTP/1.1 作为临时规避手段，但此为低置信度方向，不建议作为首选。

## 潜在风险
无。本次未修改任何代码。