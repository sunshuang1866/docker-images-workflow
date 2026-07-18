# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
#14 DONE 31.3s
euler_builder_20260710_091535 removed
2026-07-10 09:18:18,406 - INFO - [Build] finished
2026-07-10 09:18:18,406 - INFO - [Push] finished
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
- 失败位置: CI Runner 测试脚本 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 在 Docker 镜像构建和推送均成功完成后，进入后置 `[Check]` 阶段时，测试脚本尝试通过 `. shunit2` 加载 `shunit2` 单元测试框架，但该框架未安装在 CI runner 上，导致测试完全无法执行，Check 结果表为空，整个 job 被标记为 FAILURE。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文件（httpd-foreground 启动脚本、meta.yml、README.md、image-info.yml）。Docker 镜像的构建和推送阶段均 100% 成功完成（Build + Push 共计 14 个 Docker buildx 步骤全部 DONE）。失败发生在 `eulerpublisher` 工具的容器检查阶段，系 CI 基础设施缺少 `shunit2` 依赖所致，不是 PR 代码变更可以解决的问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 的操作系统上安装 `shunit2` 测试框架。openEuler 系统中可通过 `dnf install shunit2` 安装。这是 CI 运维层面的修复，需要联系 CI 平台管理员处理。

### 方向 2（置信度: 低）
如果确认 CI runner 上不应依赖系统级安装的 `shunit2`，则需修改 `eulerpublisher` 测试脚本 `common_funs.sh`，将 `shunit2` 的来源改为项目内嵌或 pip 安装的版本，确保测试框架自包含在 CI 环境中。

## 需要进一步确认的点
1. 同一 CI runner 上其他 PR（特别是同样使用 openEuler 24.03-LTS-SP4 的镜像）是否也遇到相同的 `shunit2: file not found` 错误。如果是，说明这是 CI 环境的系统性问题；如果不是，需调查本次运行 runner 的环境差异。
2. `shunit2` 是否本应作为 `eulerpublisher` 的依赖自动安装到 CI runner？如果是，需检查 `eulerpublisher` 包的依赖声明（setup.py/pyproject.toml）中是否遗漏了 `shunit2`。
3. 该 CI runner 的管理方式和可用软件源，确认安装 `shunit2` 的可行性。
