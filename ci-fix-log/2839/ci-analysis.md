# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式（部分参考模式39）
- 新模式标题: CI测试框架缺依赖
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的测试脚本 `common_funs.sh` 第 13 行尝试 `source shunit2`，但 `shunit2`（Shell 单元测试库）未安装/未配置在 CI Runner 的 `PATH` 中，导致 Check 阶段测试框架无法初始化。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增以下 4 个文件：
1. `Database/postgres/17.6/24.03-lts-sp4/Dockerfile`（新 Dockerfile）
2. `Database/postgres/17.6/24.03-lts-sp4/entrypoint.sh`（新 entrypoint 脚本）
3. `Database/postgres/README.md`（文档更新，新增一行表格条目）
4. `Database/postgres/meta.yml`（元数据，新增 2 行镜像条目）

Docker 镜像构建和推送阶段全部成功完成（`[Build] finished` → `[Push] finished`，镜像已成功推送到 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`）。失败发生在构建之后的 [Check] 阶段，该阶段由 CI 编排工具 `eulerpublisher` 负责运行容器功能测试——但其自身的测试依赖 `shunit2` 在 CI Runner 上缺失，导致测试框架无法启动，所有测试用例均未实际执行（Check Results 表格为空即为明证）。

## 修复方向

### 方向 1（置信度: 中）
在 CI Runner 上安装 `shunit2`。这是 CI 基础设施层面的依赖缺失，应由 CI 运维团队在 Runner 镜像或测试环境中确保 `shunit2` 可用（例如 `dnf install shunit2` 或手动部署到 `/usr/local/etc/eulerpublisher/tests/` 路径下）。

### 方向 2（置信度: 低）
若 `shunit2` 本应由某个更上层的 CI 初始化步骤（如 job 编排脚本、pre-check hook）负责安装/准备，则需检查该初始化步骤是否被跳过或失败。

## 需要进一步确认的点
1. 确认 CI Runner（本次使用 x86_64 runner）上是否安装了 `shunit2` 包，若未安装则需补充。
2. 确认 `eulerpublisher` 测试框架的初始化流程是否正确执行，`shunit2` 是否本应由前序步骤部署到指定路径。
3. 确认同一仓库中其他 postgres 变体（如 `17.6-oe2403sp2`、`17.5-oe2403sp1`）的 CI Check 阶段是否也存在同样的 `shunit2` 缺失问题——若均存在，则证实为 CI 基础设施全局问题。
