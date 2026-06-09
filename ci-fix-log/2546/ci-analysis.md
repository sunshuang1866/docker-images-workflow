# CI 失败分析报告

## 基本信息
- PR: #2546 — 【自动升级】libyuv容器镜像升级至1948版本.
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 新模式（症状部分匹配 模式13，但根因不同）
- 新模式标题: ENV自引用未定义变量
- 新模式症状关键词: UndefinedVar, LD_LIBRARY_PATH, ENV

## 根因分析

### 直接错误
```
 1 warning found (use --debug to expand):
 - UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 19)
```
以及：
```
WARNING: [Check] File: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/libyuv_test.sh does not exist, no test runs.
```

> **注意**：本次 CI 最终状态为 `Finished: SUCCESS`，构建和推送均成功完成。上述两项为警告级别问题，未阻塞流水线，但属于代码质量问题，可能在未来或更严格的 CI 配置中被视为错误。

### 根因定位
- **失败位置**: `Others/libyuv/1948/24.03-lts-sp3/Dockerfile:19`
- **失败原因**: Dockerfile 中 `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build:$LD_LIBRARY_PATH` 在一个全新的构建阶段中自引用了 `$LD_LIBRARY_PATH`。由于该变量此前从未在同一构建阶段被定义，BuildKit 检测到对未定义变量的引用，产生 `UndefinedVar` 警告。

### 与 PR 变更的关联
- PR 新增了 `Others/libyuv/1948/24.03-lts-sp3/Dockerfile`（新文件，21 行），该 Dockerfile 的第 19 行直接触发了此警告。
- PR 同时更新了 `Others/libyuv/README.md`、`Others/libyuv/doc/image-info.yml`、`Others/libyuv/meta.yml`，这些元数据文件的修改与警告无关。
- 警告 100% 由本次 PR 的新增代码引起。

## 修复方向

### 方向 1（置信度: 高）
**显式初始化为空后再拼接，消除对未定义变量的引用。**

在 `ENV LD_LIBRARY_PATH=...` 之前新增一行 `ENV LD_LIBRARY_PATH=""`，或在同一 `ENV` 中将路径写为硬编码绝对路径（不依赖已有环境变量），例如 `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build`。这样 BuildKit 不会触发 UndefinedVar 警告。

### 方向 2（置信度: 中）
**使用容器运行时的动态拼接替代构建时 ENV 拼接。**

将 ENV 形式的拼接改为在 `CMD`/`ENTRYPOINT` 启动脚本中动态设置，或利用 `/etc/ld.so.conf.d/` 添加库路径后执行 `ldconfig`，从而完全避免在 ENV 中引用未定义变量。

### 方向 3 — 测试文件缺失（置信度: 高）
**补充 `libyuv_test.sh` 测试文件。**

CI 在 Check 阶段报告 `libyuv_test.sh` 不存在，导致未运行任何测试。按照项目规范，应在 `Others/libyuv/` 目录下补充该测试脚本，以确保镜像功能经过验证。

## 需要进一步确认的点
- `$LD_LIBRARY_PATH` 自引用写成 `/usr/local/lib:/libyuv/build:$LD_LIBRARY_PATH` 的意图是否是为了保留基础镜像中已存在的库路径？如果是，需要确认基础镜像 `openeuler/openeuler:24.03-lts-sp3` 是否预置了 `LD_LIBRARY_PATH`，以及是否需要继承其值。
- 项目中其他类似 Dockerfile（如同目录下的 `1934/24.03-lts-sp3/Dockerfile`）是如何处理 `LD_LIBRARY_PATH` 设置的，可作为参考对照。
