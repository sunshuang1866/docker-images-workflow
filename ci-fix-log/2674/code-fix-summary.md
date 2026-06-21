# 修复摘要

## 修复的问题
容器在无参数启动时立即退出，导致 `test_spark_container_startup` 测试失败（容器 PID 1 退出、`docker ps` 不可见）。

## 修改的文件
- `Bigdata/spark/4.1.2/24.03-lts-sp3/Dockerfile`: 在 `ENTRYPOINT` 后新增 `CMD ["driver"]` 指令（共 +1 行）

## 修复逻辑
根因：Dockerfile 仅设置了 `ENTRYPOINT ["/opt/entrypoint.sh"]`，无 `CMD`。当 CI check 脚本以 `docker run -d image`（无参数）启动容器时，`entrypoint.sh` 的 `$1` 为空，落入 `*)` 分支执行 `exec "$@"`，由于 `"$@"` 为空，`exec` 成为空操作，脚本结束导致容器 PID 1 退出。

修复：添加 `CMD ["driver"]`。Docker 的 `ENTRYPOINT` + `CMD` 组合模式中，`CMD` 为 `ENTRYPOINT` 提供默认参数。当 K8s operator 显式传入 `driver` 或 `executor` 时，会覆盖 `CMD` 的值，不影响现有 K8s 调度行为。当容器无参数启动时（如 CI 测试），`CMD` 提供默认值 `driver`，`entrypoint.sh` 进入有效的 driver 分支启动 `spark-submit`，容器保持运行。

## 潜在风险
无。`CMD` 只是为 `ENTRYPOINT` 提供默认参数，K8s 调度时显式传入的参数会覆盖 `CMD` 值，不影响现有 Spark-on-K8s 的工作流程。仓库中其他 Spark 版本虽未设置 `CMD`，但同样的问题可能存在于它们的 CI 测试中（如果测试同样以无参数方式启动容器）。