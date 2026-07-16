# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 部分匹配模式39（CI工具依赖缺失）
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 的 `eulerpublisher` 测试框架在 [Check] 阶段加载 `common_funs.sh` 时，第 13 行 `. shunit2` 尝试 source `shunit2`（Shell 单元测试框架），但该文件在 CI runner 上不存在，导致整个测试脚本无法执行，check 结果表为空。

### 与 PR 变更的关联
**本次 PR 的代码变更与 CI 失败无关。** 证据如下：
1. Docker 镜像构建（#10/#11/#12/#13）**全部成功完成**，包括编译 httpd 2.4.66、安装、配置和导出镜像。
2. Docker 镜像推送（#14）**也成功完成**，manifest sha256 已确认。
3. 日志中明确输出 `[Build] finished` 和 `[Push] finished`。
4. 失败仅发生在 CI 编排工具 `eulerpublisher` 的 [Check] 后处理阶段——该阶段调用 `shunit2` 对已构建的镜像运行自动化检查，但 `shunit2` 本身缺失，导致检查脚本在初始化阶段即崩溃，**一个测试检查项都未执行**（结果表完全为空）。

PR 新增的文件（Dockerfile、httpd-foreground、meta.yml 更新、README.md 更新、image-info.yml 更新）均不涉及 CI 工具链配置，不涉及 `shunit2` 的安装或路径。

## 修复方向

### 方向 1（置信度: 中）
CI runner 环境中缺少 `shunit2` 包（Shell 单元测试框架 `shunit2`）。需要在 CI 编排层（Jenkins job 或 runner 镜像）安装 `shunit2`，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能正常 source 该文件。此问题与 PR 代码无关，应由 CI 运维团队修复 runner 环境。

### 方向 2（置信度: 低）
如果 `shunit2` 是 `eulerpublisher` Python 包的附属文件，可能是 `eulerpublisher` 包版本过旧或安装不完整，需要升级/重装 `eulerpublisher` 容器测试组件。

## 需要进一步确认的点
1. 同一 CI runner 上其他 PR（如最近的 httpd 2.4.66 SP2 或类似镜像）的 [Check] 阶段是否也失败？如果其他 PR 的检查也失败，则确认是 CI 基础设施的全局问题。
2. `shunit2` 是否在此 CI runner 的历史环境中存在过？是否是最近 runner 环境变更导致该包丢失？
3. [Check] 阶段对应的测试脚本（`common_funs.sh`）和 `shunit2` 的来源——是 `eulerpublisher` 包自带还是系统层面由运维安装的——以确定正确的修复路径。
4. 如果是 runner 环境的临时问题，重试构建即可通过。
