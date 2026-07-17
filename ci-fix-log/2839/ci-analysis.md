# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 工具链内置测试脚本）
- 失败原因: CI [Check] 阶段运行的测试脚本 `common_funs.sh` 尝试加载 `shunit2`（Shell 单元测试框架），但该框架在 CI runner 上未安装或路径不可达，导致测试脚本加载失败，未执行任何检查项即报错退出。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，Docker 构建和镜像推送均成功完成（`#8 DONE 268.4s`、`#11 DONE 58.0s`、`[Build] finished`、`[Push] finished`）。失败仅发生在 `eulerpublisher` CI 工具的 [Check] 后处理阶段，属于 CI 基础设施环境问题（测试框架 shunit2 缺失），跟 PR 的代码变更内容无任何关联。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 环境中安装 shunit2 Shell 单元测试框架。shunit2 可通过包管理器（如 `dnf install shunit2`）或从 GitHub 下载（`https://github.com/kward/shunit2`）并放置到 CI 测试脚本可加载的路径（如 `/usr/local/etc/eulerpublisher/tests/` 或 `/usr/local/bin/`）。安装后需验证 `source shunit2` 可正常加载。

### 方向 2（置信度: 低）
如果 shunit2 已在 CI runner 上安装但路径配置错误，需检查 `common_funs.sh` 中第 13 行 `shunit2` 的加载方式（是 `source shunit2`、`. shunit2` 还是指定了相对路径），确认 shunit2 实际安装路径与脚本预期路径一致。

## 需要进一步确认的点
1. 同一时间段同一类别的其他 PR（如 Database/postgres 其他版本）是否也遇到相同的 `shunit2: No such file or directory` 错误——如果是，说明是 CI runner 环境整体性问题，非本 PR 独有。
2. shunit2 是否已在 CI runner 上安装（`which shunit2` 或 `dnf list installed | grep shunit2`），如果已安装但报错，需检查 `common_funs.sh` 中的 `PATH` 或 `source` 路径是否正确。
3. 是否存在针对 postgres 镜像的特定 check 脚本，以及该类脚本是否需要额外的环境变量或预置文件。
