# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, check test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 运行器上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 阶段测试脚本 `common_funs.sh` 尝试引入 `shunit2`（bash 单元测试框架），但该工具未安装在 CI runner 上，导致测试框架无法启动。Docker 镜像的构建和推送本身均成功完成（步骤 #7-#11 全部 DONE，日志显示 `[Build] finished`、`[Push] finished`）。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Docker 构建过程完全成功，所有 RUN 步骤均正常完成，镜像已成功推送至 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。失败发生在 CI 后置检查阶段的测试基础设施层面。

## 修复方向

### 方向 1（置信度: 高）
CI runner 上缺少 `shunit2` 测试框架。需在 CI 运行器环境中安装 `shunit2`（可通过 `dnf install shunit2` 或 `pip install shunit2`，取决于所使用的 shunit2 发行版），或者将 `common_funs.sh` 改为使用 CI runner 上已有的测试工具。

PR 本身无需任何代码修改。

## 需要进一步确认的点
- 确认 CI runner 上 `shunit2` 应如何安装（dnf 包名、pip 包名，或从源码部署的路径）
- 确认其他同类型镜像（如 24.03-lts-sp3 的 Go 镜像）的 [Check] 阶段是否也因同样原因失败，还是仅本次出现
- 确认最近 CI runner 环境是否有变更导致 `shunit2` 被移除
