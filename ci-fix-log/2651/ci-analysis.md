# CI 失败分析报告

## 基本信息
- PR: #2651 — 【自动升级】ovirt-engine容器镜像升级至4.5.7版本.
- 失败类型: test-failure
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游测试本地化格式不匹配
- 新模式症状关键词: LocalizedMessageHelperTest, DateTimeFormatter, CLDR, locale, AssertionFailedError, expected but was

## 根因分析

### 直接错误
```
#10 324.5 [ERROR] Failures:
#10 324.5 [ERROR]   LocalizedMessageHelperTest.testForEnglish:41 expected: <Time: Dec 31, 2022, 11:59:59?PM ...> but was: <Time: Dec 31, 2022, 11:59:59 PM ...>
#10 324.5 [ERROR]   LocalizedMessageHelperTest.testForNonTranslatedLanguage:70 expected: <Time: 31 d?c. 2022, 23:59:59 ...> but was: <Time: 31 d?c. 2022 ? 23:59:59 ...>
#10 324.5 [ERROR]   LocalizedMessageHelperTest.testForNotDefaultLanguage:99 expected: <?????: 31 ???. 2022??., 23:59:59 ...> but was: <?????: 31 ???. 2022 ?., 23:59:59 ...>
#10 324.5 [ERROR] Tests run: 136, Failures: 3, Errors: 0, Skipped: 0
#10 324.5 [INFO] oVirt Engine Tools ................................. FAILURE [  3.430 s]
#10 324.5 [INFO] BUILD FAILURE
#10 ERROR: process "/bin/sh -c git clone ... && make clean install-dev PREFIX=\"/usr/local/\"" did not complete successfully: exit code: 2
```

### 根因定位
- 失败位置: `org.ovirt.engine.core.notifier.transport.smtp.LocalizedMessageHelperTest`（上游 ovirt-engine 4.5.7 源码），`testForEnglish:41`、`testForNonTranslatedLanguage:70`、`testForNotDefaultLanguage:99`
- 失败原因: 测试用例中硬编码的日期时间格式期望值与 OpenJDK 11.0.27 在 openEuler 24.03-LTS-SP3 上运行时 `DateTimeFormatter` 实际产生的本地化字符串不一致，差异集中在 Unicode 特殊格式字符（如窄不间断空格、瘦空格等 CLDR 日期格式化分隔符）上

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 ovirt-engine 4.5.7 的 Dockerfile、README 条目和 meta.yml，未修改任何 Java 源代码。该测试失败是上游 ovirt-engine 项目 `LocalizedMessageHelperTest` 自身的问题——测试用例针对特定 CLDR/Java 版本的日期格式化输出编写了硬编码断言，当构建环境使用不同 CLDR 数据版本（openEuler 自带的 JDK 11.0.27）时，本地化字符串中的特殊 Unicode 格式字符发生了变化，导致断言失败。

## 修复方向

### 方向 1（置信度: 中）
在 Dockerfile 的 `make clean install-dev` 之前，通过 patch 或 sed 操作注释掉 `LocalizedMessageHelperTest` 中 3 个失败的测试方法（`testForEnglish`、`testForNonTranslatedLanguage`、`testForNotDefaultLanguage`）。这 3 个测试仅验证邮件通知模板的本地化输出格式，不影响 ovirt-engine 核心功能。

### 方向 2（置信度: 低）
跳过整个 tools 模块的测试运行。在 Maven 构建时添加 `-pl !backend/manager/tools` 参数排除 tools 模块，或使用 `-DskipTests` 跳过所有测试。此方案风险较高，会跳过 tools 模块的全部 136 个测试。

## 需要进一步确认的点

1. **上游 ovirt-engine 4.5.7 源码确认**：需要在 `git clone -b ovirt-engine-4.5.7` 后查看 `backend/manager/tools/src/test/java/org/ovirt/engine/core/notifier/transport/smtp/LocalizedMessageHelperTest.java` 的具体实现，确认测试中硬编码的期望值格式，以及是否已有针对不同 CLDR 版本的兼容处理。
2. **openEuler JDK 11.0.27 的 CLDR 版本**：确认 openEuler 24.03-LTS-SP3 中 `java-11-openjdk-devel` 实际使用的 CLDR（Unicode Common Locale Data Repository）版本号，以判断格式差异是否为已知的 CLDR 版本间变更。
3. **是否可升级 JDK**：排查 JDK 版本升级（如 11.0.30+）是否能解决 CLDR 不匹配问题 — 但需注意模式03的 JDK 404 风险。

## 修复验证要求

若采用方向 1（注释测试方法），code-fixer 必须：
1. 从 `https://github.com/oVirt/ovirt-engine` 的 `ovirt-engine-4.5.7` 分支获取 `LocalizedMessageHelperTest.java` 的实际内容
2. 确认 `testForEnglish`、`testForNonTranslatedLanguage`、`testForNotDefaultLanguage` 三个方法名及所在行号与日志一致
3. 验证 patch 操作（如 `sed` 块注释）不会破坏文件的 Java 语法
4. 重新运行 `make clean install-dev` 确认构建通过
