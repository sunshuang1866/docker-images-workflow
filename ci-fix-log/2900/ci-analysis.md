# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Check 阶段，`/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在 [Check] 阶段执行容器镜像验证测试时，测试框架脚本 `common_funs.sh` 尝试通过 `. shunit2` 引入 `shunit2` Shell 单元测试框架，但该工具未安装在 CI runner 环境上，导致 Check 阶段直接失败，测试结果表格为空（无任何测试被执行）。

### 与 PR 变更的关联
**与 PR 变更无关。** 日志显示 Docker 镜像构建阶段（步骤 #1 至 #14）全部成功完成——httpd 2.4.66 源码在 openEuler 24.03-lts-sp4 基础镜像上编译通过，镜像成功构建并推送到 registry（`#14 DONE 31.3s`）。失败发生在构建完成之后的 [Check] 测试阶段，`shunit2` 缺失是 CI runner 环境问题，PR 新增的 Dockerfile 及 README/meta.yml 文档更新均无法影响 CI runner 上已安装的系统级工具。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境上安装 `shunit2` Shell 测试框架。`shunit2` 是 `eulerpublisher` 测试套件的运行时依赖，用于执行容器镜像的集成验证测试。需在 CI 构建节点上确保该工具可用（例如通过包管理器安装或预置在 runner 镜像中）。此问题对本次 PR 的所有镜像（包括已存在的其他 httpd 版本）均有影响，非本次 PR 特有问题。

## 需要进一步确认的点
- 确认 `shunit2` 在当前 CI 构建节点的安装状态，检查是否特定于某个 runner 标签/分组。
- 确认相同 CI runner 上其他成功 PR 的 Check 阶段是否也曾使用 `shunit2`，判断是否为近期 CI 环境变更导致。

## 修复验证要求
无需额外验证。此问题为 CI 基础设施依赖缺失，不涉及对 Dockerfile 或源码的任何修改。恢复 `shunit2` 后重新触发 CI 即可验证。
