# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner — `/usr/local/etc/eulerpublisher/tests/container/../common/common_funs.sh:13`
- 失败原因: CI 运行环境的测试框架依赖 `shunit2` 未安装或不可用，导致 `eulerpublisher` 在对已构建成功的镜像执行 `[Check]`（容器功能测试）阶段时脚本加载失败。Docker 镜像的构建和推送阶段均已成功完成。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，以及配套的 README.md、image-info.yml、meta.yml 更新。Docker 构建（Build）和推送（Push）阶段均成功完成（`[Build] finished`、`[Push] finished`），失败发生在 CI 运行器自身的测试执行框架中，属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 测试框架。该工具是 `eulerpublisher` 容器镜像 Check 阶段执行功能测试所必须的依赖。需确保 CI 运行器镜像或节点预装了 `shunit2`（例如通过 `dnf install shunit2` 或从 GitHub 获取），使 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 第 13 行的 `shunit2` 加载能够成功。

### 方向 2（可选，置信度: 低）
如果 `shunit2` 已安装在 Runner 上但仍报错，需检查 `common_funs.sh` 中 `shunit2` 的引用路径或 `PATH` 环境变量配置是否正确。

## 需要进一步确认的点
1. CI Runner 节点上是否已安装 `shunit2` ？执行 `which shunit2` 或 `rpm -q shunit2` 确认。
2. 其他 Go 版本（如 `1.25.6-oe2403sp3`）的构建是否也在此 Runner 上执行？若否，可能仅该 Runner 配置遗漏了 `shunit2`；若是，则可能是最近 Runner 环境变更导致依赖丢失。
3. `shunit2` 的来源：是通过系统包管理器安装（如 `dnf install shunit2`）还是作为 `eulerpublisher` 的 bundled 依赖？需确认正确的安装方式。
