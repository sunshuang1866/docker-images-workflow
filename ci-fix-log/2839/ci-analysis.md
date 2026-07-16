# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI shunit2 依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上 `eulerpublisher` 测试框架脚本 `common_funs.sh` 第 13 行尝试 source `shunit2`，但该工具未安装在 CI runner 环境中，导致 `[Check]` 阶段的容器验证测试无法启动。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建和推送阶段均已完成并成功：
- PostgreSQL 17.6 源码编译安装成功（`#8 DONE 268.4s`，包括 configure → make → make install 全流程无编译错误）
- `entrypoint.sh` 复制和权限设置成功（`#9 DONE`, `#10 DONE`）
- 镜像导出并推送至 Registry 成功（`#11 DONE 58.0s`）
- `[Build] finished` 和 `[Push] finished` 日志均确认成功

失败仅发生在 PR 代码变更范围之外的 CI `[Check]` 后处理阶段，因 runner 缺少 `shunit2` 导致容器启动验证测试无法执行。PR 新增的 Dockerfile、entrypoint.sh、README.md 和 meta.yml 均无问题。

## 修复方向

### 方向 1（置信度: 高）
联系 CI 基础设施管理员，在 `eulerpublisher` 测试运行的 CI runner 上安装 `shunit2` Shell 单元测试框架。常见安装方式：通过 RPM/DNF 包管理器安装 `shunit2` 包，或从 GitHub 下载并放入 `PATH` 中。此错误与 PR 代码无关，无须修改 Dockerfile 或任何仓库文件。

## 需要进一步确认的点
- 同一 CI runner 上其他同类型 PR（同类应用镜像的新增）是否也出现了同样的 `shunit2` 缺失错误。
- `eulerpublisher` 包版本是否最近更新导致依赖声明不完整（如 `shunit2` 未被列为依赖自动安装）。
