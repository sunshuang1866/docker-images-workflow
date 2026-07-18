# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 检查阶段shunit2缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed, Finished: FAILURE

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
- 失败原因: CI 流水线的 `eulerpublisher` 检查测试框架 `common_funs.sh` 在第 13 行尝试加载 `shunit2` 测试库（通过 `. shunit2` source 命令），但 `shunit2` 未安装或不在 `PATH` 中，导致整个 Check 阶段直接崩溃，Check 结果表为空。Docker 镜像的构建和推送在此之前均已成功完成（`[Build] finished`，`[Push] finished`，构建 7/7 步骤全部 `DONE`）。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 HTTPd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套配置文件（`httpd-foreground` 脚本、`meta.yml`、`image-info.yml`、`README.md`）。Docker 构建阶段全部成功（7/7 步骤 DONE，镜像成功推送到 registry），失败发生在 CI 框架的检查测试阶段，属于 CI 基础设施问题。Dockerfile 中唯一的构建警告是 `LegacyKeyValueFormat`（ENV 格式风格建议，非致命错误，不影响构建结果）。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` 测试框架（如在 openEuler 中通过 `yum install shunit2` 或从 `https://github.com/kward/shunit2` 下载安装到 CI runner 的已知路径），确保 `common_funs.sh` 能够成功 source 该库。

### 方向 2（置信度: 中）
若 `shunit2` 已安装在 CI Runner 上但路径非默认，检查 `common_funs.sh` 中的 `PATH` 设置或 `shunit2` 安装路径是否正确，调整 source 路径或 `PATH` 环境变量。

## 需要进一步确认的点
- CI Runner 环境中 `shunit2` 的实际安装状态：是否安装了该包，安装路径是什么。
- 该 CI Check 步骤之前是否对同仓库其他 PR 正常运行过（是否属于本次 CI 环境的偶发退化）。
- Docker 镜像本身的功能正确性：虽然构建和推送成功，但由于 Check 测试未能执行，容器运行时行为（如 `httpd-foreground` 能否正常启动、端口 80 是否监听）未经验证。建议在修复 `shunit2` 后重跑 CI 以确认容器功能测试通过。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。
