# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 的 `[Check]` 阶段，`/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI Runner 上执行镜像验收测试时，`common_funs.sh` 脚本尝试通过 `. shunit2` 引入 `shunit2` Shell 单元测试框架，但该框架未安装在 CI Runner 的预期路径中，导致测试表为空、[Check] 阶段返回失败

### 与 PR 变更的关联
**与 PR 变更无关**。Docker 镜像构建（7 个 RUN 步骤全部完成）、导出、推送均成功（`[Build] finished` / `[Push] finished`）。失败仅发生在 CI Runner 的 `[Check]` 后处理阶段——由于 CI Runner 自身缺少 `shunit2` 测试框架依赖，导致无法对已成功构建的镜像执行验收测试。PR 新增的 Dockerfile、httpd-foreground 脚本、meta.yml 和文档条目均正确，无语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。此失败为 CI 基础设施问题（CI Runner 缺少 `shunit2` Shell 测试框架）。需联系 CI 运维团队在 Runner 上安装或配置 `shunit2`（通常通过 `dnf install shunit2` 或克隆 `https://github.com/kward/shunit2` 到 Runner 的预期路径 `/usr/local/etc/eulerpublisher/tests/container/common/` 下），然后重试该 workflow。

## 需要进一步确认的点
- CI Runner 上 `shunit2` 的预期安装路径与当前实际路径
- CI Runner 上是否曾安装过 `shunit2`（是否为近期变更导致卸载）
- 同一 CI Runner 上其他镜像的 Check 是否也因相同原因失败（以确认是单 runner 问题还是全局 CI 环境问题）

## 修复验证要求
此失败为 infra-error，修复方向不涉及正则 patch 外部源文件，无需额外验证步骤。CI 运维在 Runner 上安装 `shunit2` 后重跑 workflow 即可验证。
