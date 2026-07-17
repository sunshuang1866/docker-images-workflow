# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: `shunit2, file not found, common_funs.sh, Check test failed`

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
- 失败位置: CI Check 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境的测试脚本 `common_funs.sh` 在第 13 行尝试 `. shunit2` 引入 shell 单元测试框架，但该框架未安装在该 CI runner 上（`file not found`），导致 [Check] 阶段在运行任何实际测试之前即崩溃。Check 结果表为空也佐证了没有任何测试用例实际执行。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 HTTPD 2.4.66 的 Dockerfile 及相关元数据文件（`meta.yml`、`README.md`、`image-info.yml`），Docker 镜像构建和推送均完全成功（日志中 `#10 DONE 41.6s`、`[Build] finished`、`[Push] finished`）。失败发生在 CI 管线的 Check 阶段，因测试运行器环境缺少 `shunit2` 工具链导致测试框架无法启动，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 中）
CI 管理员需在运行该检查 job 的 runner 上安装 `shunit2` 软件包（如 `dnf install shunit2` 或 `pip install shunit2`），确保 `common_funs.sh` 能正确定位并 source 该框架。

### 方向 2（置信度: 中）
若 `shunit2` 应以相对路径引用（而非依赖 PATH），则需检查 `common_funs.sh` 所在目录结构，补充缺失的 `shunit2` 脚本文件。

## 需要进一步确认的点
- 该 CI runner 是否为此 PR 触发的特定架构（x86_64）构建节点？确认 `shunit2` 缺失是全局性问题还是仅此节点存在。
- `shunit2` 在 CI 环境中的预期安装路径是什么（是否为 RPM 包、pip 包或检出的脚本文件）？需确认安装方式后再操作。

## 修复验证要求
该失败为 infra-error，Code Fixer 无需修改任何代码。若需要人为介入恢复 CI，验证方式为：在 runner 上安装 `shunit2` 后重新触发该 job，确认 Check 阶段不再报 `shunit2: file not found`。
