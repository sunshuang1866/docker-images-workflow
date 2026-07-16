# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI缺shunit2依赖
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 的 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（Check 测试阶段）
- 失败原因: CI 检查框架 `eulerpublisher` 的 `common_funs.sh` 第 13 行尝试 source `shunit2`（Shell 单元测试框架），但该依赖在 CI runner 上未安装/不在 PATH 中，导致测试框架无法初始化，所有 Check Items 均未执行，check 表为空

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 构建 7 个步骤全部成功（`#10 DONE 41.6s` 编译+安装、`#11 DONE 0.1s` 配置、`#12 DONE 0.0s` COPY、`#13 DONE 0.1s` chmod），镜像也已成功构建并推送至仓库（`#14 DONE 31.3s`，`[Build] finished`，`[Push] finished`）。失败仅发生在 CI 自有的 [Check] 测试阶段，原因是 CI runner 环境缺少 `shunit2`，与 PR 新增的 httpd 2.4.66 24.03-lts-sp4 Dockerfile 无关。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员需在 CI runner 上安装 `shunit2` 包，使其可在 `PATH` 中被 `common_funs.sh` 的 `source` 命令找到。`shunit2` 是一个 Shell 单元测试框架，通常可通过系统包管理器安装（如 `yum install shunit2` 或 `dnf install shunit2`）。安装后无需修改任何代码或 Dockerfile。

## 需要进一步确认的点
- `shunit2` 在 openEuler 24.03-LTS-SP4 上的包名及可用性（是否为 `shunit2` 或 `shunit`）
- 该 CI runner 上是否之前已安装 `shunit2` 但被误移除，或是否为新增 runner 未完成初始化
- 其他同批次 PR 的 CI Check 是否也报同样错误（若普遍存在则进一步确认为 infra 问题）
