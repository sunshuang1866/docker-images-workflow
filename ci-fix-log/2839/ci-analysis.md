# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher

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
- 失败位置: CI 运行器上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 第 13 行
- 失败原因: CI 测试框架 `eulerpublisher` 在执行容器镜像检查测试（`[Check]` 阶段）时，依赖的 `shunit2` shell 单元测试库未安装在 CI runner 上，导致检查脚本的测试函数无法加载，所有测试项均未执行（Check Items 表格为空），整体判定为失败。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh，并更新了 README.md 和 meta.yml。Docker 镜像构建与推送阶段已成功完成（`#8 DONE 268.4s`，`[Build] finished`，`[Push] finished`），失败仅发生在 CI 测试框架的后处理/检查阶段，根因为 `shunit2` 库在 CI runner 上缺失，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI runner 上安装 `shunit2` shell 单元测试框架。在 CI 运行器环境（`/usr/local/etc/eulerpublisher/tests/container/common/`）中部署 `shunit2` 脚本，确保 `common_funs.sh:13` 能够成功 source 该库文件。此为纯基础设施维护，Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 `shunit2` 在 CI runner 上的预期安装路径（`common_funs.sh` 第 13 行的实际 source 路径）
- 确认 `shunit2` 是应从系统包管理器安装（如 `dnf install shunit2`）还是作为独立脚本部署
- 若该 CI runner 上其他 PR 的 Check 阶段均失败（同系统性问题），则可确认为近期 CI 环境变更导致 `shunit2` 丢失
