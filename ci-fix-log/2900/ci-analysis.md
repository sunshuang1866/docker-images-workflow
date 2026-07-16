# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, CRITICAL: [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI Check 阶段）
- 失败原因: CI 测试框架 `eulerpublisher` 在 [Check] 阶段依赖 `shunit2` shell 测试框架，但 CI runner 上未安装该工具，`common_funs.sh` 第 13 行 `. shunit2` 无法找到该文件，导致 Check 脚本执行失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建（编号 #1 至 #10 的所有 RUN 步骤均 DONE）、推送（`[Push] finished`）均已成功完成。日志中清晰显示：
- `[Build] finished` — 构建成功
- `[Push] finished` — 推送成功
- 所有 Docker 构建步骤以 `#10 DONE 41.6s`、`#11 DONE 0.1s`、`#12 DONE 0.0s`、`#13 DONE 0.1s`、`#14 DONE 31.3s` 完成
- 失败发生在构建和推送完成**之后**的 Check 测试阶段，因 CI runner 环境缺少 `shunit2` 包

日志开头的 "Error lines" 部分（`httpd-2.4.66/docs/error/...` 等）为 tar 解压过程中正常列出的文件路径，**并非错误信息**，不影响构建结果。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架。`shunit2` 是 `eulerpublisher` 容器镜像 Check 流程的运行时依赖 — 对于 openEuler 系统，可通过 `dnf install shunit2` 或从 GitHub（`https://github.com/kward/shunit2`）手动部署到 runner 的 `PATH` 中。

## 需要进一步确认的点
- CI runner 上 `shunit2` 是否已安装但不在 `PATH` 中（检查 `/usr/share/shunit2/`、`/usr/local/share/shunit2/` 等常见路径）
- 该 PR 对应的其他架构 runner（如 aarch64）是否已通过 Check 阶段（日志中仅显示 x86_64）
- `eulerpublisher` 的 Check 配置中是否可以通过环境变量指定 `shunit2` 路径（如 `SHUNIT2_HOME`），从而无需全局安装
