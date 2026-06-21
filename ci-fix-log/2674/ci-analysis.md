# CI 失败分析报告

## 基本信息
- PR: #2674 — 【自动升级】spark容器镜像升级至4.1.2版本.
- 失败类型: runtime-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 容器启动即退出
- 新模式症状关键词: `container_status: false`, `No such object`, `failed to start container`, `Spark did not start within the allocated time`

## 根因分析

### 直接错误
```
test_spark_container_startup
container_status: false
Error: No such object: 2faa4a407c70d009e34e7145f5e416cd29aeb9a2e1d3b11de791c6d81d069978
container_status:
Error: No such object: 2faa4a407c70d009e34e7145f5e416cd29aeb9a2e1d3b11de791c6d81d069978
...（重复多次）
ASSERT:ERROR, failed to start container 2faa4a407c70d009e34e7145f5e416cd29aeb9a2e1d3b11de791c6d81d069978 in 60 seconds
ASSERT:Spark did not start within the allocated time.
shunit2:ERROR test_spark_container_startup() returned non-zero return code.
FAILED (failures=3)
[Check] test failed
```

### 根因定位
- 失败位置: `Bigdata/spark/4.1.2/24.03-lts-sp3/Dockerfile` + `entrypoint.sh`（组合问题）
- 失败原因: 容器启动测试中，容器被创建后立即退出（`container_status: false`），随后被 Docker 清理（`Error: No such object`），导致 60 秒超时检测失败。根因极可能是 Dockerfile 仅有 `ENTRYPOINT` 而**缺少 `CMD` 指令**，entrypoint.sh 在无参数时走到 `*) exec "$@"` 分支，`$@` 为空导致脚本立即结束、容器退出。

### 与 PR 变更的关联
本次 PR 新增了完整的 Spark 4.1.2 Dockerfile 和 entrypoint.sh。Dockerfile 中仅声明了 `ENTRYPOINT ["/opt/entrypoint.sh"]` 而未声明 `CMD`。entrypoint.sh 的 case 分支在无参数时执行 `exec "$@"`（空操作），脚本随即退出，容器无法保持运行状态。

此外，日志中出现了一个值得注意的差异：构建日志显示 step 4/10 安装了 tini（`/usr/bin/tini`），但 PR diff 中的 Dockerfile 并未包含 tini 安装步骤。这意味着 CI 流水线可能对 Dockerfile 有额外的注入/模板化处理，或提供的 diff 与实际构建版本不完全一致。不过该差异不是本次失败的直接原因——启动失败发生在 [Check] 阶段（容器启动测试），而 [Build] 和 [Push] 阶段均已成功。

## 修复方向

### 方向 1（置信度: 中）
在 Dockerfile 中补充 `CMD` 指令，使容器在无外部参数时也有一个保持运行的默认命令。参考同仓库其他 Spark 版本（如 4.0.1、3.3.2）的 Dockerfile，确认它们是否包含 `CMD` 以及其具体值（常见为 `spark-shell` 或其他长驻命令）。同时确认 CI 容器启动测试的预期行为——是依赖 Dockerfile 的 CMD 还是向容器传参。

### 方向 2（置信度: 低）
entrypoint.sh 中的 JAVA_HOME 自动探测逻辑使用了 `set -eo pipefail` 组合，若 `grep 'java.home'` 未匹配到 java 输出（可能因 aarch64 环境 Java 输出格式差异），脚本会在此处提前退出。需在 aarch64 环境中验证 `java -XshowSettings:properties -version 2>&1 > /dev/null | grep 'java.home'` 是否能正确匹配输出。

## 需要进一步确认的点
1. **CI 容器启动测试的传参方式**：测试 `test_spark_container_startup` 在启动容器时是否传参？若传参（如 `driver`），entrypoint 的 case 分支应能正确进入 exec 逻辑，则根因在其他处。需获取测试代码或日志中 `docker run` 的完整命令行。
2. **同仓库其他 Spark 版本的 Dockerfile 对比**：检查 `Bigdata/spark/4.0.1/24.03-lts-sp2/Dockerfile` 和 `Bigdata/spark/3.3.2/22.03-lts/Dockerfile` 是否声明了 `CMD`，以及 entrypoint.sh 是否相同。这有助于确认当前是否为 "缺失 CMD" 问题。
3. **tini 安装步骤的差异**：PR diff 中不含 tini 安装，但构建日志包含。需确认 CI 流水线是否自动注入 tini 步骤，还是 diff 未反映最终提交的完整 Dockerfile。若 CI 有自动注入，需确认注入逻辑无误。
4. **aarch64 环境下 JAVA_HOME 探测**：在 aarch64 容器内手动运行 `java -XshowSettings:properties -version 2>&1 > /dev/null | grep 'java.home' | awk '{print $3}'`，确认能否正确提取 Java 安装路径。

## 修复验证要求
1. 修复后，在 aarch64 和 amd64 环境下分别执行 `docker run -d <image>` 验证容器能保持运行 ≥ 60 秒。
2. 对比同仓库已有 Spark 版本的 Dockerfile（4.0.1-oe2403sp2、3.3.2-22.03-lts），确保 entrypoint.sh 和 CMD 配置保持一致。
3. 若 CI 确有 Dockerfile 模板注入逻辑，需在注入后的完整 Dockerfile 上验证修复。
