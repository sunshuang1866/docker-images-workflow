# CI 失败分析报告

## 基本信息
- PR: #2651 — 【自动升级】ovirt-engine容器镜像升级至4.5.7版本.
- 失败类型: test-failure
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 本地化测试locale不匹配
- 新模式症状关键词: LocalizedMessageHelperTest, expected, but was, locale, AssertionFailedError, testForEnglish, testForNonTranslatedLanguage, testForNotDefaultLanguage

## 根因分析

### 直接错误
```
#10 348.6 [ERROR] org.ovirt.engine.core.notifier.transport.smtp.LocalizedMessageHelperTest.testForEnglish -- Time elapsed: 0.015 s <<< FAILURE!
#10 348.6 org.opentest4j.AssertionFailedError: 
#10 348.6 expected: <Time: Dec 31, 2022, 11:59:59?PM
#10 348.6 > but was: <Time: Dec 31, 2022, 11:59:59 PM

#10 348.6 [ERROR] org.ovirt.engine.core.notifier.transport.smtp.LocalizedMessageHelperTest.testForNonTranslatedLanguage -- Time elapsed: 0.006 s <<< FAILURE!
#10 348.6 expected: <Time: 31 d?c. 2022, 23:59:59
#10 348.6 > but was: <Time: 31 d?c. 2022 ? 23:59:59

#10 348.6 [ERROR] org.ovirt.engine.core.notifier.transport.smtp.LocalizedMessageHelperTest.testForNotDefaultLanguage -- Time elapsed: 0.005 s <<< FAILURE!
#10 348.6 org.opentest4j.AssertionFailedError:
#10 348.6 expected: <?????: 31 ???. 2022??., 23:59:59
#10 348.6 > but was: <?????: 31 ???. 2022 ?., 23:59:59

#10 348.6 [ERROR] Failures: 
#10 348.6 [ERROR]   LocalizedMessageHelperTest.testForEnglish:41
#10 348.6 [ERROR]   LocalizedMessageHelperTest.testForNonTranslatedLanguage:70
#10 348.6 [ERROR]   LocalizedMessageHelperTest.testForNotDefaultLanguage:99
#10 348.6 [ERROR] Tests run: 136, Failures: 3, Errors: 0, Skipped: 0
#10 348.6 [INFO] oVirt Engine Tools ................................. FAILURE [  3.500 s]
#10 348.6 [INFO] BUILD FAILURE
```

### 根因定位
- 失败位置: `org.ovirt.engine.core.notifier.transport.smtp.LocalizedMessageHelperTest` (ovirt-engine 上游源码，非 PR 引入)
- 失败原因: `LocalizedMessageHelperTest` 中 3 个测试用例全部失败，测试期望的本地化日期/时间格式字符串中包含特殊 Unicode 字符（如窄不间断空格 U+202F、各 locale 特定的日期分隔符），但 JVM 在 openEuler 24.03-lts-sp3 容器环境中实际输出的格式化字符串使用了不同的空格/分隔符字符，导致断言不匹配。

### 与 PR 变更的关联
PR 引入了全新的 `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`（+37 行），以及配套的元数据更新。Dockerfile 中 `make clean install-dev` 触发了 ovirt-engine 上游源码的全量 Maven 构建（含测试）。失败的 `LocalizedMessageHelperTest` 是 ovirt-engine 4.5.7 上游源码中已有的测试，**与 PR 自身代码改动无直接因果关系**，但 PR 选择的 Dockerfile 构建流程（安装的 JDK 版本、locale 包、系统环境）导致了该测试在当前容器环境中失败。

具体可能原因：
- 容器中缺少完整的 glibc locale 数据包（如 `glibc-locale-source`、`glibc-all-langpacks`），导致 JVM 的 `java.text.DateFormat` 等 API 对特定 locale（德语 de-AT、俄语 ru-RU、英语 en-US 等）的格式化输出与测试期望不匹配
- 当前环境未设置 `LANG` / `LC_ALL` 等 locale 环境变量，JVM 使用 fallback locale 数据

## 修复方向

### 方向 1（置信度: 中）
在 Dockerfile 的 `dnf install` 步骤中补充安装 locale 相关包（如 `glibc-locale-source`、`glibc-all-langpacks` 或对应的 `glibc-langpack-*`），并在 `RUN` 中设置 `LANG=en_US.UTF-8` 和 `LC_ALL=en_US.UTF-8` 环境变量，确保 Java 在格式化不同 locale 的日期时间时能获取正确的 locale 数据。

### 方向 2（置信度: 中）
如果方向 1 无法解决（可能是 JDK 自身 locale 数据与测试期望的 CLDR 版本不一致），可在 `make` 构建时通过 Maven 参数跳过 `tools` 模块的测试：`make clean install-dev PREFIX="/usr/local/" MAVEN_OPTS="-DskipTests"` 或设置 `-Dtest=!LocalizedMessageHelperTest` 排除特定测试类。需注意：跳过测试可能掩盖其他真实问题，仅当确认这 3 个测试是已知的 locale 环境敏感测试时才考虑此方向。

### 方向 3（置信度: 低）
检查是否存在 JDK 版本冲突：Dockerfile 同时通过 `dnf install java-11-openjdk-devel` 和 `wget` 安装了两个 JDK（系统 JDK + Adoptium JDK），最终 `JAVA_HOME` 指向 Adoptium JDK。不同的 JDK 发行版可能使用不同的 locale 数据提供者（CLDR vs COMPAT），导致测试期望与实际输出不一致。可尝试只保留一个 JDK 来源（仅用 dnf 安装的系统 JDK 或仅用 Adoptium），验证测试是否通过。

## 需要进一步确认的点
1. 确认 `openeuler/openeuler:24.03-lts-sp3` 基础镜像中 `glibc-locale-source` 或等价包是否可用，若不可用需查找对应的 openEuler locale 包名（可能是 `glibc-langpack-en`、`glibc-langpack-de`、`glibc-langpack-ru` 等）
2. 确认 ovirt-engine 4.5.7 上游的 `LocalizedMessageHelperTest` 是否有已知的 JDK 版本兼容性问题（查阅 ovirt-engine GitHub issues）
3. 确认 Adoptium JDK 11.0.27_6 与 openEuler 系统 JDK 的 `java.locale.providers` 默认值是否相同
4. 若上述均无法解决，需在 ovirt-engine 上游源码的 `LocalizedMessageHelperTest.java:41/70/99` 中查看具体断言逻辑和期望的 Unicode 字符，判断是否为该版本 ovirt-engine 的已知测试缺陷
