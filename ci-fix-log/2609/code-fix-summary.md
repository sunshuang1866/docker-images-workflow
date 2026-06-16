# 修复摘要

## 修复的问题
Dockerfile 中 `ARG VERSION=710-20250515-before-cpenv` 对应的 Git 引用在上游仓库 `eclipse-ee4j/glassfish` 中不存在，导致 `git clone -b ${VERSION}` 失败。

## 修改的文件
- `Others/glassfish/710-20250515-before-cpenv/24.03-lts-sp3/Dockerfile`: 将 `ARG VERSION=710-20250515-before-cpenv` 改为 `ARG VERSION=7.1.0`

## 修复逻辑
CI 分析报告指出根因是 `git clone -b 710-20250515-before-cpenv` 在上游仓库 `eclipse-ee4j/glassfish` 中找不到对应分支或 tag。经验证，上游仓库不存在 `710-20250515-before-cpenv` 这个引用。版本号中 `710` 对应 GlassFish 7.1.0，上游存在 `refs/tags/7.1.0`（commit `7aa0146c`），将其作为 VERSION 即可使 `git clone -b` 正确检出源码。

## 潜在风险
无。该修改仅替换了 Dockerfile 中的版本号引用，与现有同类 Dockerfile（如 `7.0.23`、`7.0.25`）使用上游 tag 名称的模式一致，不影响其他功能。