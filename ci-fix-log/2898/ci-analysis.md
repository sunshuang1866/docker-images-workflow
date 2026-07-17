# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Check阶段缺少shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 的 [Check] 阶段测试脚本 `common_funs.sh` 在第 13 行尝试 source `shunit2`（Shell 单元测试框架），但 CI 运行环境未安装该工具，导致测试阶段直接报错退出。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile` 及配套的 meta.yml、README.md、image-info.yml 更新。Docker 镜像构建和推送均成功完成：

- `#7 DONE 67.8s` — Go 源码下载/解压
- `#8 DONE 40.5s` — touch + symlink 设置
- `#9 DONE 1.5s` — 构建工具移除
- `#10 DONE 0.0s` — WORKDIR 设置
- `#11 DONE 41.9s` — 镜像导出并推送至 docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64

失败仅发生在构建后 CI 自身的 `[Check]` 测试验证阶段，原因是 CI Runner 环境中 `shunit2` 未安装，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 Shell 单元测试库，应在 `eulerpublisher` 工具的容器测试运行环境中预装。检查 CI 节点配置或 `eulerpublisher` 包的依赖声明，确保 `shunit2` 在测试执行前已安装至 `PATH` 可搜索到的目录或 `common_funs.sh` 指定的 source 路径。

## 需要进一步确认的点
- CI Runner 节点的系统镜像或初始化脚本中是否遗漏了 `shunit2` 的安装步骤。
- 同为 openEuler 24.03-LTS-SP4 的其他镜像（如模式39 提到的 `Others/bisheng-jdk`）当次 CI 是否也因相同原因在 [Check] 阶段失败，以排除该问题是否仅影响新架构 `aarch64` 节点。
