# CI 失败分析报告

## 基本信息
- PR: #2674 — 【自动升级】spark容器镜像升级至4.1.2版本.
- 失败类型: runtime-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 容器启动后立即退出
- 新模式症状关键词: No such object, failed to start container, Spark did not start within the allocated time, container_status: false

## 根因分析

### 直接错误
```
test_spark_container_startup
container_status: false
Error: No such object: 2faa4a407c70d009e34e7145f5e416cd29aeb9a2e1d3b11de791c6d81d069978
...（重复数十次，check 脚本轮询容器状态失败）...
ASSERT:ERROR, failed to start container 2faa4a407c70d009e34e7145f5e416cd29aeb9a2e1d3b11de791c6d81d069978 in 60 seconds
ASSERT:Spark did not start within the allocated time.
shunit2:ERROR test_spark_container_startup() returned non-zero return code.
FAILED (failures=3)
[Check] test failed
```

### 根因定位
- 失败位置: `Bigdata/spark/4.1.2/24.03-lts-sp3/Dockerfile` + `entrypoint.sh`（运行时阶段）
- 失败原因: Docker 镜像构建成功（10/10 步骤均通过），但在 CI [Check] 阶段的 `test_spark_container_startup` 测试中，容器被创建后几乎立即退出/消失，导致 check 脚本无法获取容器状态（"No such object"持续出现），最终在 60 秒超时后判定失败。

### 与 PR 变更的关联

PR 新增了 Spark 4.1.2 的 Dockerfile 和 entrypoint.sh。构建阶段完全成功（日志中 dnf 安装、gosu/tini 下载、spark 解压、镜像推送均无报错），失败仅发生在**容器运行时启动阶段**。以下是与本 PR 强相关的疑点：

1. **Dockerfile 缺少 CMD 指令**：Dockerfile 只设置了 `ENTRYPOINT ["/opt/entrypoint.sh"]`，但没有设置 `CMD`。若 CI check 脚本以无额外参数方式启动容器（如 `docker run -d image`），entrypoint.sh 将收到空参数。

2. **entrypoint.sh 对无参数场景无有效处理**：entrypoint.sh 的 `case "$1" in` 仅匹配 `driver` 和 `executor` 两个分支，当 `$1` 为空时落入 `*)` 分支执行 `exec "$@"`。由于无参数时 `"$@"` 展开为空，`exec` 命令成为空操作，脚本随即结束，容器 PID 1 退出，容器停止。这会导致容器被创建后立即变为 exited 状态，与日志中"No such object"（容器已不存在）的现象吻合。

3. **Dockerfile diff 与 build log 存在不一致**：构建日志中步骤 #10 安装了 tini（`wget ... tini-arm64`），但 PR diff 中并未出现该 RUN 步骤。这表明 diff 与实际情况可能有差异，需进一步确认 Dockerfile 的最终内容。

## 修复方向

### 方向 1（置信度: 中）
为 Dockerfile 添加 `CMD` 指令，使容器在无参数启动时有默认的前台进程保持运行。例如设置 `CMD ["driver"]` 或 `CMD ["spark-shell"]`，确保 entrypoint.sh 进入有效的执行分支。

### 方向 2（置信度: 低）
如果 CI 的 check 脚本确实传入了 `driver` 参数，则问题可能在于运行时环境变量缺失（如 `SPARK_DRIVER_BIND_ADDRESS`、`SPARK_DRIVER_URL` 等 K8s 专属变量为空导致 spark-submit 启动失败）。需查看 check 测试脚本的实际调用方式方能确认。

## 需要进一步确认的点

1. **CI check 脚本的具体实现**：`test_spark_container_startup` 是以什么参数启动容器的（`docker run image` 还是 `docker run image driver`）？这直接决定集装箱的入口行为路径。
2. **Dockerfile 的最终完整内容**：构建日志显示有 10 个步骤（含 tini 安装），但 PR diff 中缺少 tini 安装步骤。需确认 Dockerfile 的实际内容是否与 diff 一致。
3. **同版本其他 Spark 镜像的 CMD/ENTRYPOINT 配置**：可参考仓库中已有的 Spark 3.3.x / 4.0.x Dockerfile 的 ENTRYPOINT 和 CMD 设置方式，判断是否有遗漏。
4. **amd64 架构的构建结果**：当前日志仅包含 aarch64 架构，若 amd64 也失败，可能指向共性问题；若 amd64 成功，则问题可能与架构相关。

## 修复验证要求

若修复方向 1（添加 CMD），code-fixer 必须在提交前：
- 确认仓库中已有 Spark 版本（如 `Bigdata/spark/4.0.1/24.03-lts-sp2/Dockerfile`）的 CMD/ENTRYPOINT 配置模式，确保与现有规范一致。
- 验证添加 CMD 后，容器能够在前台持续运行（`docker run -d image` 后 `docker ps` 可见容器 running 状态）。
