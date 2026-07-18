# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI检查阶段缺少shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在 [Check] 阶段执行 `common_funs.sh` 时，脚本尝试通过 `. shunit2` 加载 `shunit2` shell 单元测试库，但该库未安装在 CI runner 环境中（不在 PATH 中），导致脚本执行失败。

### 与 PR 变更的关联
**与 PR 变更无关。**

PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件，以及更新了 README.md、image-info.yml、meta.yml 元数据。日志显示：
- Docker 镜像构建全部 6 个步骤均成功完成（`#9 DONE 41.4s` 到 `#12 DONE 0.1s`）
- 镜像导出与推送也成功完成（`#13 DONE 36.0s`，`[Build] finished`，`[Push] finished`）
- 失败发生在构建和推送全部完成之后的 [Check] 阶段，由 CI 测试框架自身的依赖缺失引发

失败与 PR 中的 Dockerfile 内容、依赖包、构建脚本、配置文件均无关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架。`shunit2` 是一个标准的 shell 单元测试库，需要在 CI runner 的测试环境中确保该依赖可用（例如通过包管理器安装或在 CI 初始化脚本中预先部署）。此修复属于 CI 基础设施层面，Code Fixer 无需修改任何 PR 代码。

## 需要进一步确认的点
- 本次失败的 runner 是 aarch64 架构（从推送镜像标签 `9.21.23-oe2403sp4-aarch64` 可知）。x86_64 架构的同镜像构建是否也存在相同问题，需要查看对应 runner 的日志。
- CI 环境中 `shunit2` 的预期安装路径和安装方式（是系统包、pip 包还是自行部署的脚本），需与 CI 维护团队确认。
- 历史上同类仓库的 CI 是否也出现过 shunit2 缺失问题（与模式39的 `distroless` 模块缺失本质同类——均为 CI 工具依赖缺失），若频繁出现，建议 CI 团队在 runner 初始化脚本中预装该依赖。
