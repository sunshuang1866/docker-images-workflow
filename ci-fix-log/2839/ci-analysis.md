# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试阶段的 runner 环境中未安装 `shunit2` Shell 单元测试框架，导致 `[Check]` 阶段无法执行容器的启动验证测试。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，以及 README.md 和 meta.yml 的元数据更新。日志显示所有构建步骤均成功完成：

- PostgreSQL 源码编译成功（`make -j "$(nproc)" && make install` 全部通过）
- Docker 镜像构建成功（`#8 DONE 268.4s`）
- 镜像层导出和推送成功（`#11 exporting to image ... DONE 58.0s`）
- `[Build] finished` 和 `[Push] finished` 均正常输出

失败仅发生在构建完成后的 `[Check]` 测试验证阶段，原因是 CI runner 环境缺少 `shunit2` 测试框架，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
CI 运维人员在测试 runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 Shell 单元测试库，可通过以下方式安装：
- 在 runner 的依赖清单中添加 `shunit2` 包的安装
- 或确保 `common_funs.sh` 脚本中 `source` 或 `.` 引用 `shunit2` 时能找到其安装路径

此问题与 PR 代码无关，不需要对 Dockerfile 或任何仓库文件进行修改。

## 需要进一步确认的点
1. 确认 `shunit2` 是 CI runner 的预装依赖还是需要在此仓库的 CI 配置中显式声明
2. 检查同类镜像（如 postgres 的其他版本/openEuler 其他版本的 Dockerfile）的 CI `[Check]` 阶段是否也因同样原因失败——如果是，说明这是一个全局性的 CI 环境问题
3. 确认 `shunit2` 的预期安装路径和版本要求
