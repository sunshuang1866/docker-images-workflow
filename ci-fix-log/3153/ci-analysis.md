# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档变更触发appstore路径检查
- 新模式症状关键词: Path Error, appstore release specifications, README.md, update.py, expected path

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具，非 PR 修改的文件）
- 失败原因: CI 的 appstore 发布规范预检工具检测到 `README.md` 被修改后，将其作为 appstore 镜像条目进行路径校验。仓库根目录的 `README.md`（`/README.md`）是项目级文档而非 appstore 镜像条目，不符合 appstore 的 `{category}/{image-name}/{version}/{os-version}/` 路径规范，因此路径校验失败。

### 与 PR 变更的关联
PR #3153 仅修改了两个文件——`README.md` 和 `README.en.md`（根目录级别），变更内容为更新基础镜像的可用 tag 列表文档（新增 24.03-lts-sp4、sp3、25.09 等条目，更新 latest 指向）。这些是纯粹的文档更新，不涉及任何 Dockerfile、构建逻辑或镜像发布。CI 失败的根本原因是 appstore 预检工具过于激进地将所有被修改的文件都纳入镜像发布路径规范检查范围，而根目录的文档文件不应受此规则约束。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线配置问题——appstore 发布预检的变更检测范围过宽，将根目录文档文件也纳入了 appstore 镜像路径规范的校验范围。应在 CI 工具（`update.py`）中增加过滤逻辑，排除仅修改根目录非镜像路径下文件的 PR，避免对纯文档变更运行 appstore 路径检查。该问题与 PR 代码变更无关，无需修改 PR 的文件内容。

### 方向 2（置信度: 低）
若 CI 工具的设计意图就是要求在更新基础镜像 tag 文档时必须同步维护 appstore 镜像条目，则需要在对应的 `Base/openeuler/` 路径下补充 appstore 规范要求的镜像元数据文件。但从当前日志看，错误明确指向路径规范而非内容规范，方向 1 的可能性更高。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验的完整逻辑——确认为何 `/README.md` 被判定为路径错误（是否仅检查了绝对路径格式，还是对比了 image-list.yml 中的条目列表）。
2. 同类纯文档 PR 的历史 CI 结果——确认这是此 PR 的首次暴露，还是已知的 CI 流水线固有问题。
3. 根目录 `README.md` 和 `README.en.md` 是否在某个 `image-list.yml` 中被注册为图像条目（若被意外注册，则问题性质变为配置错误而非 infra-error）。
