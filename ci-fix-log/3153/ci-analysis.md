# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (无需填写)
- 新模式症状关键词: (无需填写)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075-...-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: PR 修改了仓库根目录下的 `README.md` 和 `README.en.md`，CI 的 appstore 发布规范预检认为这两个文件的路径不符合预期（期望路径为 `/README.md`）。该检查工具 (`update.py`) 对所有 PR 变更文件进行路径校验，当变更涉及根级 README 文件时，会因不属于任何应用镜像目录结构而被判定为路径错误。

### 与 PR 变更的关联
**直接关联**。PR #3153 的唯一改动就是修改 `README.md` 和 `README.en.md` 中"可用镜像的 Tags"列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 三个版本条目，调整 latest 指向）。这两个文件位于仓库根目录，不属于 `{app_category}/{app_name}/` 标准应用镜像目录结构，因此触发了 appstore 发布规范预检的路径校验规则。

## 修复方向

### 方向 1（置信度: 中）
根级 README 文件变更不被 appstore 预检接受。可能的解决方式：
- 检查该 CI 预检步骤是否对纯文档类 PR 有豁免机制（如跳过 appstore 路径校验的判断逻辑），确认是否需要在 CI 脚本中增加对根目录文档文件的豁免规则。
- 若 CI 预检脚本有白名单机制，将 `README.md` 和 `README.en.md` 加入可跳过路径校验的文件列表。
- 若没有豁免机制，则需与 CI 维护者确认纯文档 PR 是否应该走不同的流水线路径（不执行 appstore 发布预检）。

### 方向 2（可选）
如果该 CI 检查的原始意图是确保新增的应用镜像文件遵循正确的目录结构，那么对根级 README 的校验本身可能是一个误报（false positive），属于 CI 脚本逻辑缺陷，需要在 `update.py` 中排除仓库根目录文档文件的检查。

## 需要进一步确认的点
1. `update.py:273` 前后的具体校验逻辑是什么——路径校验规则是硬编码的还是来自配置文件的，以及根级文件（非应用镜像目录）的期望路径是如何定义的。
2. 该 appstore 预检步骤 (`update.py`) 是否有文件白名单或目录白名单机制可以排除根目录文档文件。
3. 该仓库的其他纯文档类 PR（仅修改根级 README）历史上是否也有同样的 CI 失败，以便判断这是新引入的检查规则还是已知行为。
4. `eulerpublisher/update/container/app/update.py:222` 之前 clone 了 sunshuang1866 的仓库，需确认 PR 来自 fork 仓库时路径解析逻辑是否有特殊处理。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不涉及。
