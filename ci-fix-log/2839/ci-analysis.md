# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI Runner 缺少 shunit2
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
- 失败位置: CI 流水线的 [Check] 阶段（测试验证步骤），非 PR 代码文件
- 失败原因: CI runner 上缺少 `shunit2` Bash 单元测试框架，导致 `common_funs.sh` 在第 13 行执行 `shunit2` 时失败。Docker 镜像的构建（Build）和推送（Push）阶段均已成功完成，Check 结果表格为空（无任何测试实际执行）。

### 与 PR 变更的关联
**与 PR 改动无关**。PR 仅新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、README 条目和 meta.yml 条目。日志显示 Docker 镜像构建和推送均成功：
- `#11 DONE 58.0s`（镜像导出及推送完成）
- `[Build] finished`（构建完成）
- `[Push] finished`（推送完成）

失败发生在 `eulerpublisher` 工具的后处理/验证阶段，`shunit2` 是一个 CI 运行环境的测试依赖，与 PR 提交的 Dockerfile 或脚本内容无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架，或在 `eulerpublisher` 的测试脚本 `common_funs.sh` 中将其声明为依赖并自动安装。此为 CI 基础设施问题，Code Fixer 无需处理 PR 代码。

## 需要进一步确认的点
- 确认 CI runner 节点上 `shunit2` 是否已被安装或在 PATH 中可访问
- 确认 `common_funs.sh` 中 `shunit2` 的引用路径是否正确（是否应为 `source shunit2` 或需要指定绝对路径）
- 确认同类 postgres 镜像（如 17.6-oe2403sp2）的 Check 阶段是否也是同样失败，以判断是 runner 环境全局问题还是仅该新镜像触发

## 修复验证要求
无。此失败为 infra-error，不涉及对 PR 代码文件的修改，无需 code-fixer 进行验证。
