# CI 失败分析报告

## 基本信息
- PR: #2932 — chore(glibc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit 启动失败
- 新模式症状关键词: Error response from daemon, Could not find the file / in container, buildx_buildkit, booting buildkit, docker-container driver

## 根因分析

### 直接错误
```
#0 building with "euler_builder_20260709_205700" instance using docker-container driver
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
- 失败位置: BuildKit 启动阶段（Dockerfile 指令尚未开始执行）
- 失败原因: Docker daemon 在创建 BuildKit 容器 `buildx_buildkit_euler_builder_20260709_2057000` 后无法在容器内定位根目录 `/`，导致 BuildKit 启动失败。该错误发生在 `[internal] booting buildkit` 阶段，属于 Docker daemon / BuildKit 基础设施层面的故障，Dockerfile 中的任何指令（FROM、RUN 等）均尚未被执行。

### 与 PR 变更的关联
**无关。** 此次 PR 仅做如下变更：
1. 新增 `Others/glibc/2.42/24.03-lts-sp4/Dockerfile` — 标准的 glibc 源码编译 Dockerfile
2. 更新 `Others/glibc/README.md`、`Others/glibc/doc/image-info.yml`、`Others/glibc/meta.yml` — 注册新镜像条目

CI 的镜像规范预检阶段已通过（日志中 "The image specification check for releasing on appstore has passed"），Dockerfile 本身也没有任何异常（ARN 参数、多阶段构建、基础镜像引用均为标准写法）。失败发生在 Docker BuildKit 守护进程的容器化启动过程中，与 Dockerfile 内容无关，也与 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
**CI runner 上 BuildKit 状态异常，需清理后重试。** 该错误可能由以下原因导致：
- CI 节点 `ecs-build-docker-x86-01` 上的 Docker daemon 存储驱动（overlay2）存在残留状态或损坏
- `buildx_buildkit_euler_builder_2057000` 容器创建时分配的临时文件系统（snapshot）无法正确挂载根目录
- docker-container driver 的 BuildKit 容器与 Docker daemon 之间的通信出现瞬时异常

**建议操作**: 清理 CI 节点上的残留 BuildKit 容器和构建缓存后重新触发构建（例如 `docker buildx prune -f` 或在 CI 脚本中增加清理步骤）。如仍失败，检查 CI 节点磁盘空间和 Docker daemon 健康状态。

## 需要进一步确认的点
1. CI 节点 `ecs-build-docker-x86-01` 的磁盘空间和 inode 使用情况
2. Docker daemon 日志中是否存在存储驱动（overlay2）相关的错误或警告
3. 该 CI 节点上是否残留同名 BuildKit 容器 `buildx_buildkit_euler_builder_*` 或同名 builder `euler_builder_*` 的孤儿状态
4. 其他 PR 在同一 CI 节点上是否能正常构建（排除节点级故障）
5. 同一次 CI 触发的 aarch64 构建 job（如有）是否也失败，以确定是单节点问题还是平台级问题
