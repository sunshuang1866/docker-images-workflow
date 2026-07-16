# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error（CI 基础设施问题），与 PR 变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败的直接原因是 CI 基础设施 `eulerpublisher` 包中的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 使用了 Windows 风格的换行符（CRLF），导致 shebang 行被内核解析为 `/bin/sh\r`，报 "bad interpreter: No such file or directory"。

CI 日志确认 Docker 镜像的构建（Build）和推送（Push）阶段均已成功完成，仅 [Check] 阶段因 CI 工具自带测试脚本的换行符缺陷而失败。PR 变更仅新增了 bwa 0.7.18 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），变更内容与 CI 失败无因果关系。

此问题需由 CI 基础设施维护者将 `eulerpublisher` 包中的 `bwa_test.sh` 脚本换行符从 CRLF 转换为 LF（Unix 格式），例如使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理。

## 潜在风险
无