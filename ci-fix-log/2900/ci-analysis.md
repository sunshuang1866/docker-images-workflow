# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39

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
- 失败位置: CI Runner 的 `[Check]` 测试阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架的 `common_funs.sh` 脚本尝试通过 `. shunit2` 引入 shunit2 单元测试框架，但 CI runner 环境中未安装 `shunit2`，导致 shell source 命令失败。Docker 镜像构建（#10 DONE 41.6s）和推送（#14 DONE 31.3s）均已成功完成，Check 表格中三项内容为空，说明测试脚本在初始化阶段就已崩溃，未能执行任何实际检查。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，所有 7 个 Dockerfile RUN 步骤均成功执行（#10～#13 全部 DONE），镜像构建完成后成功推送到 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`。失败发生在 CI 编排工具 `eulerpublisher` 的 `[Check]` 阶段，该阶段尝试在 CI runner 上执行容器功能测试，但因 runner 缺少 `shunit2` 测试框架而崩溃，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**此问题无需修改 PR 代码。** 构建和推送均已成功，CI `[Check]` 阶段失败是因为 runner 环境缺少 `shunit2` shell 测试框架。需要由 CI 运维团队在 runner 镜像中安装 `shunit2` 包，或将该 runner 节点排除在需执行 shunit2 测试的任务调度之外。PR 自身的 Dockerfile、httpd-foreground、meta.yml、README.md、image-info.yml 等变更均正确无误。

## 需要进一步确认的点
- 确认 CI runner 节点上 `shunit2` 的预期安装路径（通常为 `/usr/share/shunit2/shunit2` 或 `/usr/local/bin/shunit2`），以便运维团队补安装。
- 确认其他近期同类 PR（同为 24.03-lts-sp4 上的新镜像）是否也遇到同样的 `[Check]` 阶段 `shunit2` 缺失问题，以判断是偶发性 runner 节点问题还是系统性环境缺失。
