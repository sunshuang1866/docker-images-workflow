# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试框架shunit2缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的 [Check] 阶段执行 `common_funs.sh` 时尝试 `. shunit2` 加载 shell 单元测试框架，但 `shunit2` 未安装在当前 CI runner 上，导致测试脚本无法加载，所有检查项为空，[Check] 阶段判定失败。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文件（httpd-foreground、README、image-info.yml、meta.yml）。Docker 构建和推送阶段均已完成并成功（`[Build] finished`、`[Push] finished`），镜像已成功推送到 registry（sha256:b38237a...）。失败仅发生在 `eulerpublisher` 的 [Check] 后置测试阶段，因 CI runner 缺少 `shunit2` 测试框架依赖而无法执行容器验证测试。

## 修复方向

### 方向 1（置信度: 中）
确认 CI runner 的测试环境配置，确保 `shunit2`（shell 单元测试框架）已安装在运行 [Check] 阶段的 runner 上。`shunit2` 通常由系统包管理器安装（如 `dnf install shunit2` 或 `apt install shunit2`），需确认 CI 基础镜像或 runner 初始化脚本中包含了该依赖。若 shunit2 是项目级别的依赖而非系统级，则需检查测试脚本的 `PATH` 或 `SHUNIT2_HOME` 配置是否正确指向 shunit2 的安装路径。

### 方向 2（置信度: 低）
若 shunit2 确实已安装在 runner 上但无法被 sourced，可能是 `common_funs.sh` 中引用 shunit2 的路径假设与 runner 的实际安装路径不匹配。需要确认 `common_funs.sh` 第 13 行是直接 `. shunit2` 还是使用了相对/绝对路径。

## 需要进一步确认的点
1. 同一 CI runner 上其他近期 PR（包括同属 Others 分类的镜像）的 [Check] 阶段是否也失败？如果全部失败，则确认是 runner 基础设施问题（如 shunit2 包被意外移除）。
2. 该 runner 上 `shunit2` 的预期安装路径是什么（`/usr/share/shunit2/shunit2`、`/usr/local/share/shunit2/shunit2` 还是其他）？
3. CI runner 的初始化/置备脚本中是否应包含 `dnf install shunit2` 步骤？若已包含，需检查该 runner 是否被正确置备。
4. 检查 `common_funs.sh` 源码第 13 行的具体语句，确认是 `source shunit2`、`. shunit2` 还是带路径的引用方式，以判断是否需要修改测试脚本路径还是安装 shunit2。

## 修复验证要求
若修复方向为 CI runner 基础设施调整（安装 shunit2），code-fixer 无需处理 Dockerfile 或 PR 文件。若修复方向涉及修改 `common_funs.sh` 或测试框架脚本的 shunit2 引用路径，code-fixer 需在提交前：
1. 获取 `eulerpublisher` 测试框架中 `common_funs.sh` 的实际源码，确认 shunit2 的引用方式和期望路径。
2. 验证修改后的路径在目标 CI runner 上确实存在 shunit2 文件。
