# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: "shunit2未安装"
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 阶段执行容器镜像测试时，其测试框架依赖脚本 `common_funs.sh` 尝试 `source shunit2` 但 `shunit2`（Shell 单元测试框架）未安装在 CI Runner 上，导致所有 Check 项均无法执行（Result 表为空），[Check] 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 httpd 2.4.66 on openEuler 24.03-LTS-SP4 的 Dockerfile、辅助脚本及相关元数据文件。Docker 镜像构建和推送均成功完成（`[Build] finished`、`[Push] finished`，Docker BuildKit 步骤 #10-#14 全部 DONE，镜像已成功推送到 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`）。失败发生在 CI 平台自身的测试基础设施层——`shunit2` 工具在 CI Runner 上不可用，属于纯 CI 环境问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 包。`shunit2` 是 Linux 发行版中常见的 Shell 单元测试框架（包名通常为 `shunit2` 或 `shunit`），CI 运维人员需要在执行 `eulerpublisher` 测试的 Runner 镜像/环境中通过包管理器安装此依赖（如 `dnf install shunit2` 或 `apt install shunit2`）。

## 需要进一步确认的点
- 确认该 CI Runner 上是否应该预装 `shunit2`（是否为 Runner 镜像/环境配置遗漏）
- 确认同类已有镜像（如 `2.4.66-oe2403sp2`）在同一次 CI 流水线中的 [Check] 步骤是否也失败——如果也失败，则进一步证实是 Runner 环境级别的 `shunit2` 缺失问题
- 如果仅有该 PR 的 Runner 节点缺少 `shunit2`，需确认该节点是否使用了不同的 Runner 镜像或配置
