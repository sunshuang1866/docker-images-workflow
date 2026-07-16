# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（变体）
- 新模式标题: CI缺少shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: CI Runner 测试环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架依赖的 `shunit2`（Shell 单元测试框架）未安装在 Runner 上。Docker 镜像构建（`[Build] finished`）和推送（`[Push] finished`）均成功完成，失败仅发生在 [Check] 阶段的容器验证测试脚本中，因 `common_funs.sh` 无法找到 `shunit2` 导致所有检查项结果为空表。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 PostgreSQL 17.6 on openEuler 24.03-LTS-SP4 的 Dockerfile、entrypoint.sh、README 更新及 meta.yml 注册。Docker 构建阶段全部成功（gcc 编译、`make install` 安装各 pg 二进制工具至 `/usr/local/pgsql/bin/`，最终 `#8 DONE 268.4s`）。失败是 CI Runner 自身缺少 `shunit2` 测试依赖所致，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 包。`shunit2` 是 Shell 应用的 xUnit 测试框架，在 openEuler 中对应的包名可能为 `shunit2` 或需从源码安装。由于 Docker 构建和推送均已完成，镜像本身可以正常使用，该 PR 无需对代码做任何修改。

## 需要进一步确认的点
- 确认 CI Runner 的测试环境是否在其他 PR 中同样缺少 `shunit2`（判断是单次环境问题还是所有 runner 的普遍缺失）。
- 确认 openEuler 仓库中 `shunit2` 的具体包名（可能是 `shunit2` 或 `shunit`），以及安装方式（dnf 安装或手动部署）。
- 若 `shunit2` 在 CI Runner 环境上无法安装，需确认是否有替代的容器验证方案。
