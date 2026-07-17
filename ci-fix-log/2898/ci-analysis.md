# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 测试框架脚本 `common_funs.sh:13`（[Check] 阶段）
- 失败原因: CI 测试运行环境中缺少 `shunit2`（Shell 单元测试框架），`common_funs.sh` 第 13 行尝试 source 该库时失败，导致整个 [Check] 阶段报 CRITICAL 并标记构建为 FAILURE。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文档（README.md、image-info.yml、meta.yml），未修改 CI 测试脚本或运行环境配置。日志显示 Docker 镜像构建（#1-#11 步骤）和推送均成功完成（`[Build] finished`、`[Push] finished`），失败仅发生在后续的 [Check] 测试阶段，原因是 CI runner 环境缺少 `shunit2` 依赖。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施运维方需在测试 runner 环境中安装 `shunit2`。可通过包管理器安装（如在 openEuler 上 `dnf install shunit2`）或将 shunit2 脚本部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径下。

### 方向 2（置信度: 低）
若 `shunit2` 确实已安装在 runner 上但路径不对，可能是 `common_funs.sh` 中的 `shunit2` source 路径写死，需要根据实际安装位置调整路径。

## 需要进一步确认的点
- CI runner 环境中 `shunit2` 的预期安装路径和安装方式
- 同一 CI 环境中其他镜像（如 go 1.25.6-oe2403sp3）的 [Check] 测试是否能正常通过（若其他镜像也失败，确认是全局 infra 问题；若仅此镜像失败，需排查是否存在路径或权限差异）
