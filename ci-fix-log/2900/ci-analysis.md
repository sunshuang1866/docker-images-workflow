# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
[Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: CI 宿主机 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试环境的 `common_funs.sh` 脚本尝试通过 `. shunit2` 加载 shell 单元测试框架，但 CI runner 节点上未安装 `shunit2`，导致 `[Check]` 阶段无法执行任何测试用例（测试结果表格为空）并报 CRITICAL 错误。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2900 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、`httpd-foreground` 启动脚本，以及相关 metadata 更新（README.md、image-info.yml、meta.yml）。Docker 镜像的构建阶段（`[Build]`）和推送阶段（`[Push]`）均已成功完成：

- `#10 DONE 41.6s` — make && make install 完成
- `#11 DONE 0.1s` — sed 配置修改完成
- `#14 exporting to image` 及 `#14 pushing layers 15.8s done` — 镜像导出和推送成功
- `[Build] finished` / `[Push] finished` — CI 确认构建和推送成功

失败仅发生在 CI 后置 `[Check]` 阶段的测试框架加载环节，属于 CI 基础设施层面缺失 `shunit2` 工具的问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 节点上安装 `shunit2` shell 测试框架包。在 openEuler 上可通过 `dnf install shunit2` 或从源码安装。这是 CI 运维层面的修复，**不需要对 Dockerfile 或任何仓库文件做任何修改**。

## 需要进一步确认的点
1. 其他 PR 是否也出现了相同的 `shunit2: file not found` 错误？如果是，则说明 CI runner 环境整体缺少该依赖，需要统一安装。
2. `shunit2` 是否是 CI runner 标准镜像的一部分？如果是，此错误说明当前 runner 镜像版本与测试脚本不匹配。

## 修复验证要求
N/A — 本失败属于 infra-error，不需要修改代码仓库中的任何文件。
