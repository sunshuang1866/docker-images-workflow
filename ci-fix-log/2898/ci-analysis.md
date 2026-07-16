# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI runner 的 `[Check]` 阶段，文件 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 环境中未安装 `shunit2` shell 测试框架，导致容器镜像的验证测试（[Check] 阶段）无法执行

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个 Go 1.25.6 的 Dockerfile（`Others/go/1.25.6/24.03-lts-sp4/Dockerfile`）及对应的 README.md、image-info.yml、meta.yml 条目。Docker 镜像的构建（[Build]）和推送（[Push]）阶段均已完成且成功（#7~#11 所有步骤 DONE，`[Build] finished`，`[Push] finished`），失败仅发生在 CI 测试框架对镜像进行健康检查的 [Check] 阶段，因 Runner 缺少 `shunit2` 依赖而崩溃。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题：在运行该 job 的 CI runner 上安装 `shunit2` shell 单元测试框架，或将该 Runner 替换为已预装 `shunit2` 的节点。此问题不需要对 PR 代码做任何修改。

## 需要进一步确认的点
- 确认 `shunit2` 是否应该由 `eulerpublisher` Python 包或 CI 环境初始化脚本自动安装，若是，检查安装流程为何未触发
- 确认同一 CI runner 上其他镜像的 [Check] 阶段是否也因同样原因失败（以排除 runner 环境异常的范围）

## 修复验证要求
无需代码修复，无需额外验证。
