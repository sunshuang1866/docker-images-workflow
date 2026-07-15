# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, CRITICAL: [Check] test failed

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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段的测试脚本 `common_funs.sh` 试图通过 `. shunit2` 命令加载 shell 单元测试框架 `shunit2`，但该文件在 CI runner 上不存在（未安装），导致测试框架初始化失败，所有检查项均为空，最终标记构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 证据如下：

1. **Docker 构建完全成功**：所有 7 个构建步骤（`#9` 到 `#13`）均已完成（`DONE`），镜像成功导出并推送到 registry（`exporting manifest list sha256:... done`，`[Push] finished`）。
2. **失败发生在构建之后的 [Check] 阶段**：日志明确显示 `[Build] finished` → `[Push] finished` → `[Check] checking ...` → `[Check] test failed`。Check 阶段使用的 `shunit2` 框架是 CI runner 自身的基础设施依赖，与该 PR 新增的 httpd Dockerfile 无关。
3. **Check 表格为空**：在 `shunit2` 加载失败后，所有检查项（`Check Items`）及其描述和结果全部为空，说明测试用例
   本身根本没有执行，失败原因纯粹是测试框架缺失，而非任何测试用例的实际失败。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境上安装 `shunit2` shell 单元测试框架。`shunit2` 可从其官方 GitHub 仓库（`kward/shunit2`）获取，安装后确保 `common_funs.sh` 中的 `. shunit2` 能通过 `PATH` 或绝对路径定位到该文件。此类基础设施问题需联系 CI 运维团队处理，Code Fixer 无需修改任何代码。

## 需要进一步确认的点

1. 确认该失败是偶发性（该 runner 恰好缺少 shunit2）还是系统性（所有 Check 阶段的 runner 均缺少 shunit2）。
2. 确认如果 shunit2 正确安装，httpd 镜像的 Check 测试本身是否会通过（因为构建日志中有一个非致命的 Dockerfile lint 警告：`LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)`，但该警告不会导致构建失败）。
