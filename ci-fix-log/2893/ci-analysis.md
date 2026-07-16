# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行容器 [Check] 验证阶段的脚本 `common_funs.sh` 中尝试 source 加载 `shunit2`（Shell 单元测试框架），但该框架未安装在 CI runner 上（`shunit2: file not found`），导致检查步骤直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 变更仅包含以下内容：
1. 新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile
2. 新增 named.conf 配置文件
3. 更新 README.md、doc/image-info.yml、meta.yml 中的版本表格

Docker 镜像的编译构建（422/422 个 meson 目标全部通过）、导出和推送均成功完成：
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功
- 仅 `[Check]` 阶段因 CI 环境缺少 `shunit2` 测试框架而失败

PR 新增的 Dockerfile 和配置文件均不涉及 CI runner 上的 shunit2 安装或配置，该失败是 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
这是一个 CI 基础设施问题，与 PR 代码无关。需要在 CI runner（aarch64 节点 `ecs-build-docker-aarch64-01-sp` 或等价节点）上安装 `shunit2` Shell 测试框架。`shunit2` 通常可通过包管理器安装（如 `yum install shunit2`）或从 GitHub 克隆到 CI 工作目录。修复后重新触发 CI 即可通过。

### 方向 2（置信度: 低）
如果 `shunit2` 本应通过 CI 流水线的前置步骤自动安装但该步骤被跳过或失败，则需要检查 CI 编排配置（Jenkinsfile 或对应 pipeline 脚本）中 `shunit2` 的安装逻辑是否正常工作。

## 需要进一步确认的点
- 确认同类 PR（如其他 24.03-lts-sp4 镜像新增）的 [Check] 阶段是否也因同样的 `shunit2: file not found` 失败，以判断是孤立事件还是系统性 CI 环境问题。
- 确认 CI runner 节点上 `shunit2` 的预期安装路径和安装方式。logs 中使用的路径为 `shunit2`（无绝对路径），说明依赖 `PATH` 环境变量或 `common_funs.sh` 所在目录。
