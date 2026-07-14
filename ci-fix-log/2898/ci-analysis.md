# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
[Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 流水线的 `[Check]` 阶段中，eulerpublisher 测试框架的 `common_funs.sh` 脚本第 13 行尝试 source `shunit2`（Shell 单元测试框架），但 shunit2 未安装在 CI 测试 runner 环境中，导致测试脚本加载失败，整个 Check 阶段报 CRITICAL。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Go 1.25.6 的 Dockerfile 及相关的元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建阶段（#7 → #11）全部成功完成——包括 Go 源码下载、解压、环境配置、镜像构建、以及推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`，无任何错误。失败发生在镜像构建和推送完成之后的 `[Check]` 测试验证阶段，原因是 CI 测试 runner 环境缺少 `shunit2` 依赖，与 PR 改动的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI 的测试 runner 环境（运行 eulerpublisher container Check 的节点）上安装 shunit2（Shell 单元测试框架）。shunit2 可通过以下方式安装：
- 包管理器安装（如 `dnf install shunit2` / `apt install shunit2`）
- 或从 GitHub 下载并放置到 `/usr/local/etc/eulerpublisher/tests/container/app/../common/` 或 `PATH` 可及的位置

此为基础设施层面的修复，不属于代码变更范畴。

## 需要进一步确认的点
1. 确认 CI 测试 runner 节点上 shunit2 是否确实未安装，以及安装后是否需要配置 `common_funs.sh` 中的 source 路径。
2. 确认同一 runner 上运行的其他镜像（如已有的 Go 1.25.6-oe2403sp3）的 `[Check]` 阶段是否也因相同原因失败，以排除是新镜像类型触发了不同的测试路径导致的问题。
3. 如 shunit2 无法安装到该 runner，确认是否可跳过特定镜像类型的 Check 阶段或调整测试框架配置。
