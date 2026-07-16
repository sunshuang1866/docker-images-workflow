# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39「CI工具依赖缺失」同属 CI 基础设施问题，但具体缺失组件不同）
- 新模式标题: Check 阶段缺 shunit2
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: CI runner 的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 构建与推送阶段（Build & Push）均成功完成（日志中可见 `#14 DONE 31.3s`、`[Build] finished`、`[Push] finished`），但进入 [Check] 阶段时，测试脚本 `common_funs.sh` 尝试用 `.` 命令加载 `shunit2` 单元测试框架失败——`shunit2` 未安装在当前 CI runner 上。该问题与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 新增的 Dockerfile 构建完全成功（httpd 2.4.66 从源码编译、安装、配置均无报错），所有 7 个 Docker 构建步骤均返回 `DONE`，镜像已成功推送到 registry。失败仅发生在 CI 流水线的镜像验证（Check）阶段，因 runner 环境缺少 `shunit2` 测试框架导致。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境上安装 `shunit2` shell 单元测试框架。openEuler 上可通过 `dnf install shunit2` 或从源码安装（`https://github.com/kward/shunit2`）。该问题需由 CI 基础设施管理员处理，PR 代码无需任何修改。

## 需要进一步确认的点
- 确认 CI runner 镜像/环境中是否应预装 `shunit2`，是否为本次 CI 环境制备时遗漏
- 确认同一批其他 PR（非 httpd）在 Check 阶段是否也有相同错误，以判断是单次 runner 异常还是全局环境问题

