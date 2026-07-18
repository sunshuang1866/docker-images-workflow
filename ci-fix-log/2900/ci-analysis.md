# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` shell 单元测试框架文件，导致 `eulerpublisher` 的 [Check] 阶段无法加载测试库，检查表为空、测试直接失败。

### 与 PR 变更的关联
与 PR 变更**无关**。Docker 镜像构建（`#10 DONE 41.6s`）和推送（`#14 DONE 31.3s`）均成功完成。PR 新增的 Dockerfile 在 openEuler 24.03-LTS-SP4 基础镜像上成功编译安装 httpd 2.4.66，所有 7 个 Dockerfile RUN 步骤均通过。失败发生在 CI 编排工具 `eulerpublisher` 的容器镜像验证阶段，因 runner 环境缺少 `shunit2` 依赖而崩溃。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题——在 CI runner 上安装 `shunit2`（Shell 单元测试框架，通常通过 `dnf install shunit2` 或发行版包管理器获取），确保 `/usr/local/etc/eulerpublisher/tests/common/common_funs.sh` 第 13 行的 `. shunit2` source 命令能找到该文件。

### 方向 2（置信度: 低）
如果 `shunit2` 已安装但路径不对，可能需要修正 `common_funs.sh` 中的 `shunit2` 引用路径，或设置 `PATH` / `SHUNIT2_HOME` 环境变量指向正确的安装位置。

## 需要进一步确认的点
1. CI runner 上是否安装了 `shunit2` 包？运行 `which shunit2` 或 `dnf list installed | grep shunit2` 确认。
2. 该 runner 是否为本次 PR 新引入的节点（如 24.03-lts-sp4 专用 runner），镜像配置中遗漏了 `shunit2` 依赖？
3. 同一仓库中其他已成功构建的 openEuler 24.03-LTS-SP4 镜像（如果有）在 [Check] 阶段是否出现过同样的问题——可据此判断是本次 runner 单例问题还是 SP4 镜像通用缺失。
4. 确认 `aarch64` 架构构建 job 的日志是否也存在同样问题，以及是否有其他下游架构构建 job 的失败（当前日志仅展示 x86_64 架构的 check 失败）。

## 修复验证要求
无需 code-fixer 处理——此类 CI 基础设施问题应由 CI 运维团队在 runner 环境层面修复，不涉及代码或 Dockerfile 修改。
