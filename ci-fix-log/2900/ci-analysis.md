# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试框架脚本 `common_funs.sh` 第 13 行尝试通过 `.` (source) 加载 `shunit2` shell 单元测试框架，但该依赖未安装在 CI runner 上，导致整个 Check（镜像验证测试）阶段无法执行，测试结果表格为空，`eulerpublisher` 将 Check 阶段标记为失败。

### 与 PR 变更的关联
与 PR 变更**无关**。证据：
1. Docker 镜像构建阶段（`#9` ~ `#13`）全部成功完成（所有 RUN 步骤均显示 `DONE`，无任何编译或运行时错误）。
2. 镜像推送阶段（`#14 exporting to image` + pushing layers）成功完成，镜像已推送至 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`。
3. 失败仅发生在 Build/Push 之后的 `[Check]` 测试验证阶段，根因是 CI runner 环境缺少 `shunit2` 包——一个与 PR 代码完全无关的测试框架依赖。
4. PR 仅新增一个 Dockerfile、一个 `httpd-foreground` 辅助脚本，以及更新 README/meta/image-info 元数据文件，不涉及 CI 测试框架配置。

## 修复方向

### 方向 1（置信度: 高——面向 infra 团队）
在 CI runner 上安装 `shunit2` 包。`shunit2` 是 xUnit 风格的 shell 单元测试框架，常见于发行版仓库（如 `shunit2` 或 `shUnit2` 包名），安装后 Check 阶段即可正常执行。

### 方向 2（置信度: 低——面向 PR 作者）
确认该 CI runner 是否属于本 PR 专用的新 runner（例如因 openEuler 24.03-LTS-SP4 新增了专属构建节点），若为新 runner 镜像，其初始化脚本可能遗漏了 `shunit2` 的预装步骤。

## 需要进一步确认的点
1. `common_funs.sh` 脚本中 `shunit2` 的期望安装路径是什么（是否仅需 `yum install shunit2` 还是需从特定路径 source）。
2. 同仓库其他近期 PR 的 Check 阶段是否也出现相同 `shunit2: file not found` 错误——若为普遍现象则确认为 CI 环境退化；若仅影响本 PR，需排查 runner 调度或环境差异。

## 修复验证要求
（不适用——本失败为 infra-error，与 PR 代码无关，Code Fixer 无需处理。）
