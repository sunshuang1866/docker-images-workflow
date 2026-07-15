# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺shunit2
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上 j空心ulerpublisher 测试框架内部 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 阶段加载测试脚本时，`common_funs.sh` 尝试 source `shunit2`（Shell 单元测试框架），但该框架未安装在 CI runner 上，导致容器自检失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 构建完全成功：
- Docker 镜像全部 6 个构建步骤（#9 至 #12）均返回 `DONE`，meson 编译 422/422 目标全部完成
- 镜像已成功导出并推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`
- 日志明确显示 `[Build] finished` 和 `[Push] finished` 在 `[Check] test failed` 之前
- 失败仅发生在 CI 自身的测试框架后处理阶段，与 Dockerfile 中的包安装、编译、配置无关

## 修复方向

### 方向 1（置信度: 高）
CI Runner 环境缺少 `shunit2` Shell 测试框架。需要在 CI 构建节点的运行环境中安装 `shunit2`（如通过 `dnf install shunit2` 或 `pip install shunit2`），确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 可以正确 source 该框架。此修复由 CI 基础设施团队执行，Code Fixer 无需处理。

## 需要进一步确认的点
- 需确认 `shunit2` 是 openEuler 24.03-LTS 仓库中的可用包，还是需要通过其他方式（如 pip、手动安装）部署到 CI runner
- 确认该 CI runner 上其他应用镜像的 [Check] 阶段是否也受此次 shunit2 缺失影响（判断是本次 runner 配置问题还是全局问题）
- 需确认 x86_64 架构的 CI job 是否也遇到相同错误（当前日志仅包含 aarch64 架构的构建记录），若 x86_64 侧也能构建成功但 [Check] 同样失败，进一步确认为 infra 问题
