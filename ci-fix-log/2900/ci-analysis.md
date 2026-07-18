# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI runner 上 eulerpublisher 测试脚本内部）
- 失败原因: CI runner 上 `eulerpublisher` 工具包在执行 `[Check]` 阶段时，`common_funs.sh` 脚本尝试 `source shunit2`（shell 单元测试框架），但 `shunit2` 未安装或不在预期路径下（PATH / 脚本所在目录均未找到），导致检查框架无法初始化，检查结果表为空，`eulerpublisher` 判定检查失败。

### 与 PR 变更的关联
**与 PR 无关。** Docker 镜像构建（#9–#10 make/install）和推送（#14 push）阶段均全部成功：
- `[Build] finished` — 所有 7 个 RUN 步骤均执行完毕，无任何编译或配置错误
- `[Push] finished` — 镜像 `httpd:2.4.66-oe2403sp4-x86_64` 成功推送到 registry
- 失败发生在构建+推送完成之后的 `eulerpublisher [Check]` 测试阶段，属于 CI 测试基础设施的依赖缺失问题

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 包（shell 单元测试框架）。在 openEuler 环境中可通过 `dnf install shunit2` 安装，或确保 eulerpublisher 工具包的部署流程将 `shunit2` 作为必需依赖纳入部署脚本/CI 镜像中。

## 需要进一步确认的点
1. 确认 CI runner 的 base 镜像或部署脚本中是否遗漏了 `shunit2` 包的安装
2. 确认同仓库其他 PR 的 CI 流程是否也报相同的 `shunit2: file not found` 错误（以判断是否为 runner 环境近期变化的系统性故障）
