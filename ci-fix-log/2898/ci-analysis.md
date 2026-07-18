# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39"CI工具依赖缺失"同类但症状不同）
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 `[Check]` 阶段运行时，测试框架脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2`（一个 Shell 单元测试库），但 `shunit2` 在该 CI runner 环境中不存在，导致容器镜像验证步骤失败。

## 与 PR 变更的关联

**与 PR 变更无关**。PR 仅新增了以下文件：
- `Others/go/1.25.6/24.03-lts-sp4/Dockerfile`（新增 Go 1.25.6 的 Dockerfile）
- `Others/go/README.md`（添加一行版本表格条目）
- `Others/go/doc/image-info.yml`（添加一行版本表格条目）
- `Others/go/meta.yml`（添加新版本路径映射）

Docker 镜像构建和推送阶段**全部成功完成**：
- `#7 DONE 67.8s` — 下载并解压 Go 1.25.6
- `#11 exporting to image ... done` — 镜像构建成功
- `#11 pushing layers ... done` — 镜像推送成功
- `[Build] finished` + `[Push] finished` — 构建和推送均确认完成

失败仅发生在构建完成之后的 `[Check]` 容器验证阶段，原因是 CI runner 缺少 `shunit2` 测试框架库，属于 CI 基础设施问题，与 Dockerfile 内容、Go 版本、openEuler SP4 基础镜像无关。

## 修复方向

### 方向 1（置信度: 高）
**确保 CI runner 安装 `shunit2`**：在 openEuler 24.03-LTS-SP4 对应的 aarch64 CI runner（`ecs-build-docker-aarch64` 系列）上安装 `shunit2` 包（可通过 `yum install shunit2` 或从源码安装）。该测试框架是 `eulerpublisher` 的 `[Check]` 阶段执行容器验证测试的必需依赖。

### 方向 2（可选）
**重试 CI**：若 `shunit2` 已在 runner 上安装但运行时仍找不到，可能是 `PATH` 配置或安装了多个 shunit2 版本导致路径解析问题，需排查 runner 上 `shunit2` 的实际安装路径与 `common_funs.sh` 中 `source` 或 `PATH` 查找逻辑。

## 需要进一步确认的点

1. 确认其他 SP4 镜像（如同仓库中其他 `24.03-lts-sp4` 路径的 Dockerfile）的 CI `[Check]` 阶段是否都因同样原因失败——如果是，说明 SP4 的 aarch64 CI runner 普遍缺少 `shunit2`。
2. 确认 `common_funs.sh` 第 13 行的具体写法（是 `source shunit2`、`. shunit2`、还是通过绝对路径引用），以判断是否需要调整加载方式还是纯粹的包缺失。
3. 确认该 CI runner 上 `shunit2` 的可用包名（openEuler 中可能是 `shunit2` 或 `shunit2-standalone`）。

## 修复验证要求
不涉及正则 patch 外部源文件，无需上游文件验证。
