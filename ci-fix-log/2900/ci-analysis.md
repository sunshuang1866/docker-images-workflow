# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI缺少shunit2测试依赖
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境的 `common_funs.sh` 测试脚本尝试 `source shunit2` 但 `shunit2` 测试框架未安装或不在 `PATH` 中，导致测试脚本无法初始化。镜像构建和推送均已成功完成（`[Build] finished`、`[Push] finished`），失败仅发生在 [Check] 阶段的测试框架初始化环节。检查结果表完全为空，说明没有任何测试能够执行。

### 与 PR 变更的关联
此失败与 PR 代码变更**完全无关**。PR 仅新增了 httpd 2.4.66 的 openEuler 24.03-LTS-SP4 Dockerfile 及相关元数据文件（meta.yml、README.md、image-info.yml），Docker 镜像已成功构建并推送（`#10 DONE 41.6s`，`#14 DONE 31.3s`）。失败源于 CI 测试运行器自身缺少 `shunit2` 依赖，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI 构建节点的测试环境中安装 `shunit2` 测试框架（可通过 `dnf install shunit2` 或从 GitHub 克隆 shunit2 仓库并加入 `PATH`），确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 中的 `source shunit2` 能正常加载。这不是 PR 代码层面的修复，需由 CI 基础设施管理员处理。

## 需要进一步确认的点
- 确认 CI runner 上 `shunit2` 是否应该已预装（检查其他 PR 的同类镜像 Check 阶段是否正常通过），如果其他 PR 的 Check 也失败，说明是全局 CI 环境问题；如果仅此 PR 失败，则可能是 runner 分配到了未配置的节点。
- 确认 `common_funs.sh:13` 中 `shunit2` 的预期安装路径（是通过 `PATH` 引用还是硬编码路径）。
