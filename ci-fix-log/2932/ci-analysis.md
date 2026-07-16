# CI 失败分析报告

## 基本信息
- PR: #2932 — chore(glibc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: BuildKit启动失败
- 新模式症状关键词: Could not find the file / in container, buildx_buildkit, booting buildkit, Error response from daemon

## 根因分析

### 直接错误
```
#1 [internal] booting buildkit
#1 pulling image moby/buildkit:buildx-stable-1
#1 pulling image moby/buildkit:buildx-stable-1 1.7s done
#1 creating container buildx_buildkit_euler_builder_20260709_2057000 0.1s done
#1 ERROR: Error response from daemon: Could not find the file / in container buildx_buildkit_euler_builder_20260709_2057000
------
 > [internal] booting buildkit:
------
ERROR: Error response from daemon: Could not find the file / in container buildx_buildkit_euler_builder_20260709_2057000
euler_builder_20260709_205700 removed
```

### 根因定位
- 失败位置: `/home/jenkins/agent-working-dir/workspace/multiarch/openeuler/x86-64/openeuler-docker-images`（CI runner, x86-64 架构）
- 失败原因: Docker BuildKit builder 容器（`buildx_buildkit_euler_builder_20260709_2057000`）在 CI runner 上启动后，Docker daemon 无法访问其根文件系统 `/`，导致 buildx 实例创建失败。实际的 Dockerfile 构建过程从未开始执行。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 证据如下：
1. CI 预检阶段的 `eulerpublisher` 镜像规范检查已经通过（日志：`The image specification check for releasing on appstore has passed.`），证明新增的 Dockerfile、meta.yml、image-info.yml、README.md 均通过格式校验。
2. 错误发生在 buildx builder 实例的**内部基础设施层**（`[internal] booting buildkit`），此时 `moby/buildkit:buildx-stable-1` 镜像已拉取成功、容器已创建，但 Docker daemon 在尝试与容器交互时失败。
3. PR 新增的 Dockerfile 内容从未被送往 BuildKit 进行解析和执行。

## 修复方向

### 方向 1（置信度: 低）
CI runner（`ecs-build-docker-x86-hk`）上的 Docker daemon 状态异常或 buildx builder 实例残留。建议：
- 重试 CI job（重新触发构建流水线），排除一次性的 Docker daemon 临时故障。
- 若重试后仍然失败，检查 runner 的 Docker daemon 日志（`journalctl -u docker`），确认存储驱动（overlay2/devicemapper）是否正常，确认 `buildx_buildkit_*` 容器是否有残留未清理的僵尸容器。

### 方向 2（可选，置信度: 低）
若重试后 BuildKit 成功启动但构建本身失败，则可能需要检查 Dockerfile 中的构建依赖是否完整（如 glibc 编译可能需要 `texinfo`、`gawk`、`python3-devel` 等包），但当前日志不包含任何 Dockerfile 构建阶段的输出，无法判断。

## 需要进一步确认的点
1. **获取 CI runner 的 Docker daemon 日志**：确认 `buildx_buildkit_euler_builder_20260709_2057000` 容器为何无法使用根文件系统（可能是 overlay 挂载失败、存储驱动 bug、或容器创建后立即崩溃）。
2. **确认 runner 磁盘空间和 inode 状态**：`docker system df` 显示存在 1 个 14.85GB 的 Local Volume，需确认磁盘是否接近满载。
3. **检查是否有残留的 buildx builder 实例**：在 runner 上运行 `docker buildx ls`，清理旧的 builder（`docker buildx rm`）后重试。
4. **重试构建**：若一次性故障，重新触发 CI 即可通过；若持续失败，需要 runner 管理员介入排查 Docker 环境。
