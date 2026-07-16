# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架文件，导致 eulerpublisher 的 `[Check]` 阶段无法加载测试函数库（`common_funs.sh` 第 13 行 `. shunit2` 执行失败），容器检查流程直接中止。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅为 httpd 新增 openEuler 24.03-LTS-SP4 的 Dockerfile 和配套元数据。Docker 镜像构建阶段 (`[Build]`) 和推送阶段 (`[Push]`) 均已成功完成，所有 7 个 Dockerfile RUN 步骤（源码编译、make install、配置修改、用户创建）均正常退出。失败仅发生在 CI 工具链自身的 `[Check]` 容器验证阶段——测试框架 `shunit2` 未安装在当前 runner 上，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
通知 CI 运维团队在当前构建 runner 上安装 `shunit2` shell 测试框架（通常通过 `dnf install shunit2` 或从 EPEL 源安装）。`shunit2` 是 eulerpublisher 容器检查流程 `common_funs.sh` 的必要依赖，缺失会导致所有需要容器验证的镜像（不只是 httpd）在该 runner 上的 `[Check]` 阶段失败。

## 需要进一步确认的点
- 该 CI runner 是否为新增的 openEuler 24.03-LTS-SP4 专属 runner，环境尚未完整配置（包括 shunit2）；
- 该 runner 上其他镜像（如 httpd 2.4.66-oe2403sp2）的 `[Check]` 阶段是否同样失败，以确认是否为 runner 级别问题而非本次 PR 触发。

## 修复验证要求
无。此失败为 infra-error，无需修改代码。若 CI 运维确认 shunit2 已安装后仍失败，需进一步获取 `[Check]` 阶段的完整测试输出（非仅框架加载错误）以判断容器运行时是否有实际问题。
