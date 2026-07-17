# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: `shunit2: file not found`, `eulerpublisher`, `test failed`, `[Check]`

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
- 失败位置: CI [Check] 阶段，`eulerpublisher` 测试框架脚本 `common_funs.sh:13`
- 失败原因: CI 测试环境中 `shunit2`（Shell 单元测试框架库）未安装或不在 `PATH` 中，`eulerpublisher` 的测试脚本 `common_funs.sh` 执行 `. shunit2` 时找不到该文件，导致 [Check] 阶段无法启动任何测试即崩溃，所有测试结果为空表。Docker 镜像构建和推送均已成功完成（`[Build] finished`，`[Push] finished`，`#14 DONE`）。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 httpd-foreground 入口脚本）及对应的 README、image-info.yml、meta.yml 元数据更新。Docker 构建完全成功——从源码编译到镜像导出/推送均无任何错误。失败发生在 CI 基础设施的 [Check] 阶段，`eulerpublisher` 测试框架自身的 Shell 依赖 `shunit2` 缺失，与本次 PR 的代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施侧修复**：在 CI runner 上安装 `shunit2` 包，或将 `shunit2` 的安装路径加入 `PATH`。`eulerpublisher` 测试框架的 `common_funs.sh` 中 `. shunit2` 需要 `shunit2` 可被 Shell 的 source 机制找到。这不是 PR 代码的问题，Code Fixer 无需修改任何仓库文件。

## 需要进一步确认的点
1. 确认该 CI runner 上 `shunit2` 是否已安装（`rpm -qa | grep shunit2` 或 `which shunit2`），以及其安装路径是否在 Shell 的 source 搜索路径中。
2. 确认是否是近期 CI 环境变更（如 runner 镜像升级、软件包清理）导致 `shunit2` 被移除。
3. 如果是多架构构建（amd64 + arm64），需确认 aarch64 runner 上是否也存在相同的 `shunit2` 缺失问题——日志中仅看到 x86_64 构建和检查。
