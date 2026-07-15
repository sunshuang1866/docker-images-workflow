# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段执行容器镜像验证测试时，测试辅助脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2` 单元测试框架，但该工具未安装在 CI runner 环境中，导致测试脚本无法运行。

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 仅新增 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Docker 镜像构建（#7–#11 步骤）和推送到 registry 均成功完成（日志中明确显示 `[Build] finished` 和 `[Push] finished`）。失败发生在构建和推送成功之后的 CI [Check] 阶段，原因是 CI runner 环境中缺少 `shunit2` 测试框架，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，需要在 CI runner 环境中安装 `shunit2` 单元测试框架。`shunit2` 是标准的 xUnit 风格 Shell 测试框架，可通过包管理器（如 `apt install shunit2` 或 `dnf install shunit2`）安装，或从 GitHub 仓库（kward/shunit2）获取后放到 PATH 中。此修复应在 CI runner 镜像层面完成，而非在本次 PR 的 Dockerfile 中修改。

## 需要进一步确认的点
1. **shunit2 是否已经安装但在不同路径**：需确认 CI runner 上 `shunit2` 的实际安装路径是否与 `common_funs.sh` 期望的路径不一致（如不同的系统版本可能导致安装路径变化）。
2. **其他 Go 版本镜像是否也受影响**：需确认同一 CI runner 上其他 Go 版本（如 1.25.6-oe2403sp3）的 [Check] 测试是否能正常通过。如果其他版本也失败，则确认为 CI runner 环境全局问题；如果只有本 PR 失败，需进一步调查是否有特定触发条件（如 Tag 格式 `1.25.6-oe2403sp4` 指向了不同的测试分支）。
3. **CI runner 最近是否有变更**：确认 CI runner 环境最近是否经历过系统升级或包移除，导致 `shunit2` 丢失。
