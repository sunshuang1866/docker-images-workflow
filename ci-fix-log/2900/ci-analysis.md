# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 的测试环境（`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`）
- 失败原因: CI [Check] 阶段执行镜像测试时，测试框架 `shunit2`（Shell 单元测试工具）在 CI Runner 上缺失，导致测试脚本无法载入该依赖，整个 Check 阶段失败。Docker 镜像的构建和推送均已成功完成。

### 与 PR 变更的关联
**与 PR 改动无关**。该 PR 仅新增了 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile` 及配套的 `httpd-foreground` 脚本、更新了 README.md、image-info.yml 和 meta.yml。日志显示：
- Docker 镜像构建全部 7 个步骤成功（`#10 DONE`、`#11 DONE`、`#12 DONE`、`#13 DONE`）
- 镜像推送成功（`[Push] finished`、`#14 pushing manifest ... done`）
- 唯一失败发生在 CI 流水线的 [Check] 后置测试阶段，该阶段由 `eulerpublisher` 工具调用 `shunit2` 对容器进行启动和行为验证，但因 Runner 环境中缺少 `shunit2` 而无法执行任何测试用例（Check Result 表为空）

## 修复方向

### 方向 1（置信度: 中）
这是 CI 基础设施问题，**无需修改 PR 代码**。CI Runner 环境缺少 `shunit2` 工具。建议排查方向：
- 检查 CI Runner 是否最近更新/重建后遗漏了 `shunit2` 的安装
- 检查 `eulerpublisher` 测试框架的依赖声明，确认 `shunit2` 是否应作为 Runner 预装依赖
- 对比同仓库其他近期成功通过 [Check] 的镜像构建日志，确认 `shunit2` 缺失是全局问题还是仅影响该 Runner 节点

### 方向 2（置信度: 低）
若确认 `shunit2` 缺失是 Runner 镜像/环境配置问题，可能需要在 CI 编排配置（如 Jenkins pipeline 或 Runner 初始化脚本）中补充 `shunit2` 的安装步骤（例如 `dnf install shunit2` 或从 GitHub 拉取 `shunit2` 脚本）。

## 需要进一步确认的点
1. **确认是否为 Runner 全局问题**：对比同一 Runner 上其他镜像（如同时段构建的其他 PR）的 [Check] 阶段是否也因 `shunit2` 缺失而失败。如果其他镜像的 Check 也失败，则为 CI 基础设施全局故障。
2. **确认 Runner 环境配置历史**：CI Runner 是否最近经历了系统更新、依赖清理或重建，导致 `shunit2` 被移除。
3. **确认 `shunit2` 的预期安装方式**：在 `eulerpublisher` 项目中查找 `shunit2` 的安装/部署文档或初始化脚本，确认其是作为 RPM 包、pip 包还是手动部署脚本提供。
4. **获取历史成功日志对比**：获取该仓库中最近一次 [Check] 阶段成功通过的日志（任意镜像），确认当时 Runner 环境中确实存在 `shunit2`。

## 修复验证要求
无需修复。此故障与 PR 代码变更无关，镜像构建和推送均正确完成。待 CI Runner 的 `shunit2` 依赖恢复后，重新触发 CI 流水线即可验证。
