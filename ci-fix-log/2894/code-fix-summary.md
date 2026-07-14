# 修复摘要

## 修复的问题
CI 失败为 infra-error（`eulerpublisher` 包缺少 `distroless` 模块），与 PR 代码变更无关，无需修改 Dockerfile 或构建逻辑。顺带修正了 README.md 和 image-info.yml 中新镜像版本描述的文字笔误（`22.03` → `24.03`）。

## 修改的文件
- `Others/bisheng-jdk/README.md`: 修正 `21.0.5-oe2403sp4` 行中基础镜像版本描述 `22.03-LTS-SP4` → `24.03-LTS-SP4`
- `Others/bisheng-jdk/doc/image-info.yml`: 同上修正

## 修复逻辑
1. **CI 失败部分**：分析报告明确判定为 `infra-error`。Docker 镜像构建和推送均已成功，`eulerpublisher` 模块缺失是 CI 基础设施问题，需 CI 运维团队介入处理，不属于 Code Fixer 可修复范围。
2. **文档笔误部分**：该镜像基于 `openeuler/openeuler:24.03-lts-sp4`，但 README.md 和 image-info.yml 的表格中错误地写成了 `22.03-LTS-SP4`，属于笔误，已修正为 `24.03-LTS-SP4`。

## 潜在风险
无