# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: "CI测试框架缺失"
- 新模式症状关键词: "shunit2, No such file or directory, common_funs.sh, Check test failed"

## 根因分析

### 直接错误
```
[Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 测试基础框架 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上未安装 `shunit2`（Shell 单元测试框架），导致 `eulerpublisher` 的 [Check] 阶段无法执行容器镜像验证脚本。Docker 镜像的构建和推送步骤（#7–#11）均已成功完成。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和相关元数据文件，且 Docker 镜像构建和推送步骤全部成功（日志显示 `[Build] finished`、`[Push] finished`、镜像 sha256 已生成并推送）。失败发生在 CI 自身的测试框架层——`shunit2` 工具缺失导致无法运行容器功能验证。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 上安装 `shunit2`。`shunit2` 是一个 Shell 单元测试框架，可通过以下方式之一安装：
- 从 EPEL 仓库安装 `shunit2` RPM 包
- 从 GitHub 下载 `shunit2` 脚本并放置到 `PATH` 中
- 将其包含在 `eulerpublisher` Python 包的运行时依赖中

### 方向 2（置信度: 低）
如果 `shunit2` 缺失是 SP4 runner 独有的问题（其他 OS 版本 runner 正常），则可能是 SP4 runner 镜像在构建时遗漏了测试依赖。需检查 SP4 runner 的初始化脚本是否包含了 `shunit2` 安装步骤。

## 需要进一步确认的点
1. 同一 CI 环境中，其他 OS 版本（如 SP3）的 Go 镜像构建是否能通过 [Check] 阶段？若其他版本能通过，则确认是 SP4 runner 环境差异导致。
2. `shunit2` 是最近才从 CI runner 环境中移除的，还是 SP4 runner 从未安装过？
3. `eulerpublisher` 包中 `common_funs.sh` 是否应自带 `shunit2` 或将其列为依赖？
4. 确认容器镜像本身功能正常——即 `shunit2` 安装后，`[Check]` 测试脚本对 Go 1.25.6 镜像的验证是否全部通过。若 shunit2 安装后仍有测试用例失败，则需要进一步分析容器镜像层面的问题。

## 修复验证要求
此失败为 CI 基础设施问题（`infra-error`），Code Fixer 无需修改 Dockerfile 或任何 PR 提交文件。修复应由 CI 运维团队在 runner 环境中补充 `shunit2` 安装。
