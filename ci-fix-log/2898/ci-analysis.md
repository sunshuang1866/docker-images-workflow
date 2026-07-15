# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 环境脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行时的 [Check] 阶段，测试框架脚本 `common_funs.sh` 尝试引入 `shunit2`（Shell 单元测试框架），但该工具未安装于当前 CI runner 环境，导致测试脚本执行失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 以及相应的 README、image-info.yml、meta.yml 元数据更新。Docker 镜像构建（[Build]）和推送（[Push]）阶段均**完全成功**：
- Go 二进制包正常下载、解压并安装
- Docker 镜像成功构建并推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`
- 失败仅发生在后续的 [Check] 测试阶段，系 CI runner 缺少 `shunit2` 依赖所致

## 修复方向

### 方向 1（置信度: 高）
在 CI 构建环境中安装 `shunit2` 包（openEuler 仓库中包名通常为 `shunit2`），确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 执行时能正常 source 到 `shunit2`。

## 需要进一步确认的点
1. 当前 CI runner 是否已安装 `shunit2`，若未安装则需排查是否是该 runner 的环境配置遗漏，还是所有同类 runner 均存在此缺失。
2. 检查同一 PR 在其他架构 runner（如 x86-64）上的 [Check] 结果，确认该问题是否为 aarch64 runner 独有的环境问题。

## 修复验证要求
（无需验证——此为 infra-error，修复涉及 CI 环境配置而非代码修改。）
