# 修复摘要

## 修复的问题
ovirt-engine 构建时 `LocalizedMessageHelperTest` 3 个测试用例失败，原因是容器环境缺少 locale 数据包且未设置 `LANG`/`LC_ALL` 环境变量，导致 JVM 对多 locale（en-US、de-AT、ru-RU）的日期时间格式化输出与测试期望不匹配。

## 修改的文件
- `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 中追加 `glibc-langpack-en` 包，并在其后新增 `ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8` 环境变量声明。

## 修复逻辑
根据 CI 分析报告"方向 1（置信度: 中）"的建议，在 Dockerfile 构建阶段补充 locale 相关配置：
1. 添加 `glibc-langpack-en` 到 `dnf install` 列表，为容器提供完整的 glibc locale 数据（遵循本仓库中 `Bigdata/logstash` 等镜像的既有模式）
2. 新增 `ENV LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8`，确保 `make clean install-dev` 执行期间 JVM 能获取正确的 locale 环境设置，使 `java.text.DateFormat` 等 API 的格式化输出与 ovirt-engine 上游测试期望兼容

此修复仅改动 Dockerfile 构建环境配置，不涉及 ovirt-engine 上游源码或测试逻辑。

## 潜在风险
- 仅安装 `glibc-langpack-en` 可能不足以完全覆盖 de-AT、ru-RU 等非英语 locale 的测试预期。如果修复后这些测试仍然失败，需考虑追加 `glibc-langpack-de`、`glibc-langpack-ru` 或在构建时通过 `-DskipTests` 跳过已知的 locale 环境敏感测试。
- Adoptium JDK 11.0.27_6 的 CLDR 版本与 ovirt-engine 4.5.7 测试期望的 CLDR 版本可能存在固有差异，此修复通过系统 locale 数据对齐来缓解，但不保证 100% 消除所有 Unicode 字符级别的不匹配。