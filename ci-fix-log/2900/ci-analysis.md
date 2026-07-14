# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架缺失 shunit2
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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI 编排工具 eulerpublisher 的测试框架脚本）
- 失败原因: CI runner 环境中缺少 `shunit2`（TAP-compliant Shell 单元测试框架）。`common_funs.sh` 脚本第 13 行尝试通过 `source`（`.`）命令加载 `shunit2`，但该工具未安装在 CI runner 上，导致所有 Check 项无法定义，Check 阶段直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建（make && make install）和推送均成功完成（`[Build] finished`、`[Push] finished`、`#14 DONE 31.3s`）。失败发生在 eulerpublisher CI 工具的后置 Check 阶段，原因是 CI runner 环境基础设施缺少 `shunit2` 测试框架，而非 Dockerfile 或构建逻辑有任何问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。例如在 openEuler 24.03 上可通过 `dnf install shunit2` 或手动将 `shunit2` 脚本部署到 CI runner 的 `PATH` 中。此问题与 PR 代码无关，属于 CI 基础设施维护范围。

### 方向 2（置信度: 低）
如果 CI runner 短期无法安装 shunit2，可检查 `eulerpublisher` 的 Check 阶段是否有跳过机制（如环境变量开关），在确认构建和推送成功后允许 Check 阶段被暂时容忍/绕过。

## 需要进一步确认的点
- 确认 CI runner 的操作系统版本和可用包源中是否包含 `shunit2` 包。
- 确认是否其他同类 PR（同仓库中其他最近成功的 PR）也遇到了相同的 shunit2 缺失问题，还是仅本次运行出现。
- 确认 eulerpublisher 的 check 测试框架是否有替代品或已规划迁移到其他测试框架。
