# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 检查阶段的测试脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2` 测试框架，但该框架未安装在 CI Runner 环境中，导致检查阶段直接失败。Docker 镜像构建和推送均已成功完成（日志中可见 `[Build] finished`、`[Push] finished`、镜像 manifest 推送成功），Check Results 表格为空（无任何测试项被注册/执行）。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、meta.yml 和 README 条目。Docker 构建阶段（包括 PostgreSQL 源码编译、安装、工具二进制文件拷贝、镜像打包、推送）全部成功完成，未出现任何编译错误或构建失败。失败仅发生在 CI 流水线后置的 `[Check]` 阶段——CI Runner 自身的 `shunit2` 测试框架缺失，是一个基础设施问题。日志中的 2 个 `LegacyKeyValueFormat` 警告（ENV 格式建议）属于非致命提醒，不导致构建失败。

## 修复方向

### 方向 1（置信度: 低）
在 CI Runner 环境中安装 `shunit2` 测试框架。`shunit2` 是 xUnit 风格的 Bash 单元测试框架，可通过以下方式安装：
- openEuler 包管理器：`dnf install shunit2`（如果仓库中存在）
- 或从 GitHub 下载：`wget https://github.com/kward/shunit2/archive/refs/tags/v2.1.8.tar.gz`

但由于不确定 `shunit2` 是作为 CI Runner 的全局依赖还是按需安装，此方向需 CI 平台管理员确认。

### 方向 2（置信度: 低）
如果 `shunit2` 是应用镜像检查脚本的依赖项，可能需要在 Dockerfile 构建阶段或检查脚本的前置步骤中显式安装该框架，而非依赖 CI Runner 全局环境。

## 需要进一步确认的点
1. **CI Runner 上是否应该预装 `shunit2`？** 需确认 CI 平台的 Runner 镜像模板是否遗漏了该包，或者该 Runner 类型本身就不包含 `shunit2`。
2. **同类已有镜像的 Check 是否正常？** 需要检查该 CI 流水线中其他 PR（如已有的 postgres 17.6-oe2403sp2）的 Check 阶段是否也遇到了 `shunit2` 缺失问题，以判断是本次运行的一次性基础设施异常还是系统性问题。
3. **shunit2 的正确安装方式是什么？** 需查看 CI 平台文档或其他正常工作的 app 镜像测试，确认 `shunit2` 应通过何种方式安装（Runner 预装 vs. 测试脚本自举安装）。
