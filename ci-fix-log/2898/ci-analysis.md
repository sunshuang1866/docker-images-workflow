# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39「CI工具依赖缺失」同类）
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段运行容器测试时，测试脚本 `common_funs.sh` 尝试加载 `shunit2` shell 测试框架，但该框架未安装在 CI runner 环境中（`No such file or directory`），导致整个 Check 阶段失败。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了一个标准的 Go 1.25.6 Dockerfile（针对 openEuler 24.03-LTS-SP4），以及更新了 `README.md`、`image-info.yml`、`meta.yml` 三条元数据。Docker 镜像的 **构建**（#7-#11 所有步骤）和**推送**均已完成且成功：

- `#7 DONE 67.8s` — Go 源码下载解压成功
- `#8 DONE 40.5s` — touch/链接步骤成功
- `#9 DONE 1.5s` — 清理步骤成功
- `#11 exporting to image ... DONE 41.9s` — 镜像导出与推送成功
- `[Build] finished` + `[Push] finished` — 构建与推送阶段顺利完成

失败发生在构建/推送完成之后的 `[Check]` 测试阶段，根因是 CI runner 缺少 `shunit2` 依赖，与 PR 的 Dockerfile 代码变更无任何关系。

## 修复方向

### 方向 1（置信度: 高）
**在 CI runner 环境中安装 `shunit2`。** 在运行 `eulerpublisher` 的 CI 节点上安装 `shunit2` shell 测试框架（可通过系统包管理器或 Git clone 方式安装），确保 `common_funs.sh:13` 能正常加载该框架。

### 方向 2（置信度: 低）
**检查 eulerpublisher 测试脚本的 `shunit2` 加载路径。** 确认 `common_funs.sh` 中 `shunit2` 的引用路径是否正确，是否存在路径拼接错误导致加载失败（可能性较低，因 Go 镜像的其他 openEuler 版本在过去也存在并通过了相同测试）。

## 需要进一步确认的点
1. 该 CI runner 节点上其他已存在的 Go 镜像（如 `1.25.6-oe2403sp3`）的 Check 阶段是否正常通过？若 SP3 能通过而 SP4 不能，则需排查是否存在路径初始化差异。
2. `shunit2` 是 CI runner 环境预装依赖还是需要由测试流程自行安装？确认安装机制后执行对应修复。
3. （低优先级）该 runner 架构是否为 aarch64 专用节点，是否存在架构相关差异导致 `shunit2` 缺失。

## 修复验证要求
Code-fixer 无需处理本 issue。本失败属于 CI 基础设施问题（`infra-error`），需由 CI 运维团队在 runner 节点上安装 `shunit2` 后重试构建。
