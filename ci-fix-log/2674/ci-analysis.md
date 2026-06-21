# CI 失败分析报告

## 基本信息
- PR: #2674 — 【自动升级】spark容器镜像升级至4.1.2版本.
- 失败类型: runtime-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 缺少tini运行时依赖
- 新模式症状关键词: `No such object`, `container_status: false`, `failed to start container`, `Spark did not start within the allocated time`, `tini`

## 根因分析

### 直接错误
```
test_spark_container_startup
container_status: false
Error: No such object: 38ef938aa84930cef72bd98f1a5c9d2edfd06466504d95627f33aae697e9b51c
...
ASSERT:ERROR, failed to start container 38ef938aa84930cef72bd98f1a5c9d2edfd06466504d95627f33aae697e9b51c in 60 seconds
ASSERT:Spark did not start within the allocated time.
shunit2:ERROR test_spark_container_startup() returned non-zero return code.
FAILED (failures=3)
2026-06-21 08:44:03,497 - CRITICAL - [Check] test failed
Finished: FAILURE
```

### 根因定位
- 失败位置: `Bigdata/spark/4.1.2/24.03-lts-sp3/Dockerfile:18`（`dnf install` 步骤）
- 失败原因: Dockerfile 的 `dnf install` 命令未安装 `tini` 包，但 `entrypoint.sh` 在第 104 行和第 121 行均通过 `exec $(switch_spark_if_root) /usr/bin/tini -s -- "${CMD[@]}"` 引用 `/usr/bin/tini`，导致容器启动后 `exec` 找不到 `tini` 而立即退出，测试脚本在 60 秒内轮询容器状态始终得到 `false`/`No such object`。

### 与 PR 变更的关联
本次 PR 新增了 `Bigdata/spark/4.1.2/24.03-lts-sp3/Dockerfile` 和 `Bigdata/spark/4.1.2/24.03-lts-sp3/entrypoint.sh` 两个文件。Dockerfile 的依赖安装步骤遗漏了 `tini` 包，而 entrypoint.sh 在 driver 和 executor 模式下均通过 `/usr/bin/tini` 作为 init 进程启动 Spark 组件。容器启动后 `exec` 执行 `tini` 失败导致立即退出，触发 Check 阶段的 `test_spark_container_startup` 测试超时失败。此失败由本次 PR 新增代码直接引起。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的第一个 `dnf install` 命令中添加 `tini` 包（openEuler 24.03-LTS-SP3 仓库提供的包名为 `tini`），确保容器运行时 `/usr/bin/tini` 可用。修改位置为 `Dockerfile:18` 行附近 `dnf install -y gnupg2 wget bash krb5 procps net-tools shadow dpkg java-11-openjdk`，在其中追加 `tini`。

## 需要进一步确认的点
- 确认 `tini` 包在 openEuler 24.03-LTS-SP3 aarch64 仓库中的确切包名（预期为 `tini`，但需验证是否有版本后缀或其他命名差异）。
- 确认 entrypoint.sh 中是否还有其他运行时依赖（如 `getent`）在 openEuler 基础镜像中默认缺失（日志中 `getent` 的错误被 `&> /dev/null` 静默，但正常路径下容器不会因此退出）。

## 修复验证要求
code-fixer 修改 Dockerfile 后，需确保：
1. `tini` 包确实存在于 openEuler 24.03-LTS-SP3 的 dnf 仓库中（可通过基础镜像内 `dnf search tini` 验证）。
2. 若 `tini` 在 openEuler 中不可用，需参考 Apache Spark 官方 Dockerfile 的做法，从 GitHub Release 下载 tini 静态二进制（如 `https://github.com/krallin/tini/releases/download/v0.19.0/tini-arm64`）并放入 `/usr/bin/tini`。
