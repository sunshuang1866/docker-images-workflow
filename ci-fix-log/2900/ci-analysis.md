# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI缺shunit2测试框架
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
- 失败位置: CI 测试运行器上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行器的 `eulerpublisher` 工具在进行 `[Check]` 阶段测试时，其测试脚本 `common_funs.sh` 尝试通过 `.` (source) 加载 `shunit2` 测试框架库，但该库文件在 CI 运行器环境中不存在，导致整个 Check 阶段初始化失败。

### 与 PR 变更的关联
- **Docker 镜像构建和推送均成功完成**：日志中所有 `RUN` 步骤（`#9` 至 `#13`）均以 `DONE` 结束，`[Build] finished` 和 `[Push] finished` 正常输出。
- **PR 变更仅为新增 openEuler 24.03-LTS-SP4 的 Dockerfile 及配套文件**（`httpd-foreground` 启动脚本、`meta.yml` 条目、`README.md` 和 `image-info.yml` 的版本条目更新），不涉及任何 CI 基础设施配置。
- **失败发生在 CI 测试框架自检阶段**：`shunit2` 缺失导致测试框架无法初始化，并非因为容器镜像内容或 Dockerfile 语法问题。
- **结论**：本次失败与 PR 代码变更无关，属于 CI 运行器环境问题。

## 修复方向

### 方向 1（置信度: 高 — 若确认 CI 环境问题）
在 CI 运行器（runner）上安装 `shunit2` 测试框架。`shunit2` 是一个 Shell 单元测试库，通常可通过以下方式之一解决：
- 在 CI 运行器环境配置中确保 `shunit2` 已安装（如通过 `dnf install shunit2` 或 `pip install shunit2`）
- 检查 `eulerpublisher` 工具的依赖声明，确保 `shunit2` 被列为必需依赖

### 方向 2（置信度: 低 — 若为环境隔离导致）
若该 CI job 使用了与其他 job 不同的运行器节点（例如专用于 SP4 镜像构建的新节点），可能需要单独为该节点补充 `shunit2` 依赖。

## 需要进一步确认的点
1. `shunit2` 在 CI 环境中是应当由系统预装还是由 `eulerpublisher` 工具自带的依赖？需查阅 `eulerpublisher` 包的 `setup.py`/`pyproject.toml` 确认其依赖声明。
2. 该 CI 失败是否在重试后仍然复现（用于区分一次性环境异常与系统性环境缺失）？
3. 其他基于 openEuler 24.03-lts-sp4 基础镜像的 Dockerfile（如本次同批新增的 PR）是否也出现相同的 `shunit2: file not found` 错误？若全部出现，则确认是 SP4 运行器节点的通用环境问题。
