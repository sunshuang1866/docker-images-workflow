# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（YAML / 元数据文件错误 — CI appstore 路径校验失败）
- 新模式标题: (不适用，已匹配已有模式)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 eulerpublisher 工具对 PR 变更文件 `README.md`（仓库根目录）执行了 appstore 发布规范路径校验，校验路径解析异常（工具内部将 diff 路径 `README.md` 与期望路径 `/README.md` 进行比较后误判为不匹配），导致根目录文档变更触发了本不该运行的 appstore 发布规范预检。

### 与 PR 变更的关联
PR 变更仅涉及仓库根目录的 `README.md` 和 `README.en.md`，更新了基础镜像可用 tag 列表（新增 24.03-lts-sp4/sp3/sp2、25.09 等条目，修正 latest 指向 URL）。所有改动均为纯文档内容变更，不涉及任何 Dockerfile、meta.yml、image-info.yml 等应用镜像构建文件。CI 的 eulerpublisher appstore 发布规范校验本应对文档类 PR 跳过或判定为通过（根目录 README 不属于任何应用镜像的 appstore 元数据），但工具未能正确处理该场景，导致误报 FAILURE。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线配置问题——eulerpublisher 工具在检测到 PR diff 仅含根目录文档文件（`README.md`、`README.en.md`）时，应跳过 appstore 发布规范校验。需在 CI 编排逻辑（或 update.py 中）增加变更文件类型的判断：若 PR 仅涉及根级 `README*.md` 文件（无 Dockerfile / meta.yml / image-info.yml 变更），则直接放行，不执行 appstore 路径校验。

### 方向 2（置信度: 低）
eulerpublisher 工具路径解析缺陷——update.py 内部在比较"变更文件路径"与"期望路径"时可能存在路径前缀处理不一致（diff 路径 `README.md` 无前导 `/`，而期望路径为 `/README.md`），导致字符串比较失败。若此推断成立，需修复 update.py 中的路径归一化逻辑。

## 需要进一步确认的点
- eulerpublisher 工具中 `update.py` 第 273 行附近的路径校验逻辑具体实现，确认是路径前缀问题还是校验规则设计问题
- CI 流水线中 appstore 校验步骤的触发条件（是否会因检测到任何 `README.md` 变更就执行校验，还是误触发了针对根目录文件的校验）
- 同类纯文档 PR（如 PR #2308）是否也触发了同样的 appstore 路径校验失败，以判断这是新引入的回归还是长期存在的 CI 问题

## 修复验证要求
不适用——本 PR 的 CI 失败为 infra-error，失败原因是 CI 工具对根目录文档文件的路径校验行为不当，无需修改任何 Dockerfile、patch 或上游源码。修复方向涉及 CI 流水线配置或 eulerpublisher 工具代码的调整，不属于正则 patch 外部源文件场景。
