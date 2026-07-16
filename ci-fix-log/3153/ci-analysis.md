# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...-update.py[line:356]-INFO: Difference: ["README.md"]
2026-07-14 11:28:17,832-...-update.py[line:222]-INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-14 11:28:17,839-...-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）检测到 PR 变更了根目录下的 `README.md`，将其作为 appstore 上架条目进行校验，但该文件不在 appstore 期望的镜像层级目录（如 `Category/Image/Version/Dockerfile`）下，路径校验失败。

### 与 PR 变更的关联
此 PR 仅修改了根目录的 `README.md` 和 `README.en.md`（更新可用基础镜像 tags 列表），属于纯文档变更，不涉及任何应用镜像 Dockerfile 或元数据文件的增改。CI 的 appstore 预检工具会扫描 PR diff 中所有变更文件并逐项校验是否符合上架规范——`README.md` 作为根级文档文件并不符合 appstore 镜像条目所需的 `{category}/{image-name}/{version}/{os-version}/` 目录结构规范，因此触发路径错误。**该失败由 PR 变更触发，但并非 PR 内容有误，而是 CI 检查工具未对纯文档类 PR 做豁免处理。**

## 修复方向

### 方向 1（置信度: 高）
CI appstore 预检工具 `eulerpublisher/update/container/app/update.py` 应增加对纯文档文件（根级 `README.md`、`README.en.md`、`.md` 文档等）的过滤/豁免逻辑：在扫描 PR diff 变更文件时，对不在镜像分类目录（`Bigdata/`、`AI/`、`Database/`、`Cloud/`、`Storage/`、`HPC/`、`Others/`、`Distroless/`、`Base/` 等）下的文件跳过 appstore 规范校验。这类文件不涉及镜像上架，不应阻塞 CI。

### 方向 2（置信度: 低）
若 CI 工具代码不可修改，可改变 PR 提交策略：将文档类变更与镜像类变更拆分为独立 PR，文档 PR 跳过 x86-64/aarch64 架构构建 job（需 CI 流水线层面支持条件跳过）。

## 需要进一步确认的点
1. CI 流水线配置中是否已存在对文档类 PR 的条件跳过逻辑（如按变更文件路径过滤触发 job），若有则可能是该规则未覆盖根级 `README.md`。
2. `eulerpublisher/update/container/app/update.py` 第 222-273 行的规格校验逻辑具体如何判断"期望路径"——确认 `/README.md` 这个期望值是从何推导出来的（是硬编码的路径白名单，还是基于 `image-list.yml` 动态生成）。

## 修复验证要求
（无——本报告不涉及正则 patch 外部源文件，且根因定位为 CI 工具逻辑问题而非 PR 代码错误。）
