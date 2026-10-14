---
document_id: gt_5g_network_device_troubleshooting
source_file: 5g_network_device_troubleshooting.html
file_format: html
policy_type: 5g_network_device_troubleshooting
title: "دليل الدعم الفني لشبكات الجيل الخامس 5G وإعدادات الأجهزة و VoLTE - المصرية للاتصالات WE"
page_count: 1
total_sections: 7
total_words: 1522
total_table_cells: 20
total_media_count: 0
critical_entities: ["150 Mbps", "2 Gbps", "30 Mbps", "40 Mbps", "600 Mbps"]
hierarchy:
  - id: sec_0
    title: "Document Header & Metadata"
    order: 0
    page: 1
  - id: sec_1
    title: "دليل خدمة العملاء: حل مشكلات شبكة الجيل الخامس (5G) وضبط نقاط الوصول APN وخدمات VoLTE / VoWiFi"
    order: 1
    page: 1
  - id: sec_2
    title: "1. نظرة عامة ومتطلبات تشغيل شبكة 5G"
    order: 2
    page: 1
  - id: sec_3
    title: "2. جدول الترددات ونطاقات التشغيل المعتمدة في مصر"
    order: 3
    page: 1
  - id: sec_4
    title: "3. خطوات ضبط نقطة الوصول الرسمية (APN Configuration)"
    order: 4
    page: 1
  - id: sec_5
    title: "4. خطوات تفعيل المكالمات الصوتية عبر الجيل الرابع (VoLTE) والواي فاي (VoWiFi)"
    order: 5
    page: 1
  - id: sec_6
    title: "5. English Technical Troubleshooting Matrix for 5G Devices"
    order: 6
    page: 1
---

<!-- section: sec_0 | title: Document Header & Metadata | page: 1 | order: 0 | parent: root -->
## Document Header & Metadata

دليل الدعم الفني لشبكات الجيل الخامس 5G وإعدادات الأجهزة و VoLTE - المصرية للاتصالات WE 
 
 
 
 
 دليل خدمة العملاء: حل مشكلات شبكة الجيل الخامس (5G) وضبط نقاط الوصول APN وخدمات VoLTE / VoWiFi 
 كود السياسة:  WE-POL-5G-NET-2026 |  القسم:  الدعم الفني للشبكات اللاسلكية والهواتف الذكية 
 الإصدار:  3.2 |  تاريخ السريان:  2026 
 1. نظرة عامة ومتطلبات تشغيل شبكة 5G 
 أطلقت الشركة المصرية للاتصالات (WE) خدمات الجيل الخامس 5G بترددات النطاق العريض n78 (3.5 GHz) و n41 لتوفير سرعات فائقة وزمن استجابة فائق الانخفاض. يوضح هذا الدليل لممثلي خدمة العملاء (CSR) كيفية تشخيص أعطال الشبكة وحل مشكلات عدم ظهور إشارة 5G وتفعيل المكالمات الصوتية عالية الدقة VoLTE و VoWiFi. 
 2. جدول الترددات ونطاقات التشغيل المعتمدة في مصر 
 
 
 
 اسم التردد / النطاق 
 رقم النطاق (Band) 
 الاستخدام الرئيسي 
 السرعة القصوى المتوقعة 
 
 
 
 
 3500 MHz (C-Band) 
 n78 (TDD) 
 التغطية الرئيسية لشبكات 5G الخارجية والمناطق الحيوية 
 تصل إلى 1.2 Gbps 
 
 
 2600 MHz 
 n41 (TDD) 
 سعات إضافية لشبكة 5G والمناطق المزدحمة 
 تصل إلى 600 Mbps 
 
 
 1800 MHz 
 Band 3 (FDD) 
 الطبقة التأسيسية لـ 4G LTE ومرساة شبكة 5G NSA 
 تصل إلى 150 Mbps 
 
 
 800 / 900 MHz 
 Band 20 / 8 
 التغطية الداخلية داخل المباني (Indoor Coverage) 
 تصل إلى 40 Mbps 
 
 
 
 3. خطوات ضبط نقطة الوصول الرسمية (APN Configuration) 
 في حال عدم عمل باقة الإنترنت على الهاتف بعد تفعيل الخط، يتعين توجيه العميل لإدخال بيانات APN يدوياً: 
 
        Name: WE Internet 
        APN: we.internet 
        Proxy: Not Set 
        Port: Not Set 
        MCC: 602 
        MNC: 04 
        Authentication Type: None / PAP 
        APN Type: default,supl 
        APN Protocol: IPv4/IPv6 
        APN Roaming Protocol: IPv4
     
 4. خطوات تفعيل المكالمات الصوتية عبر الجيل الرابع (VoLTE) والواي فاي (VoWiFi) 
 تتيح خدمة VoLTE إجراء مكالمات صوتية فائقة الوضوح مع استمرار عمل الإنترنت بسرعة 5G/4G دون انقطاع، بينما تتيح VoWiFi إجراء المكالمات في المناطق ذات التغطية الضعيفة عبر أي شبكة واي فاي منزلية: 
 
 كود التفعيل الذاتي عبر USSD:  يطلب العميل  *400*1#  أو إرسال رسالة نصية مجانية تحتوي على  1  إلى  400 . 
 شروط التفعيل:  وجود شريحة 4G/5G حديثة (USIM) وتحديث نظام تشغيل الهاتف لآخر إصدار داعم لمشغل WE. 
 تفعيل VoWiFi من إعدادات الهاتف:  الدخول إلى  الإعدادات -> الشبكة والإنترنت -> بطاقات SIM -> مكالمات Wi-Fi -> تشغيل . 
 
 
 5. English Technical Troubleshooting Matrix for 5G Devices 
 Scenario A: "5G Icon does not appear on device" 
 
 Verify customer account has an active high-speed mobile data quota via BSS. 
 Verify customer is located within verified 5G coverage zones (Cairo, Giza, Alexandria, New Capital, Sheikh Zayed, New Cairo). 
 Instruct customer: Go to  Settings -> Cellular -> Cellular Data Options -> Voice & Data , and select  5G Auto  or  5G On . 
 Check if device is running Battery Saver mode (Low Power Mode disables 5G on iOS and Android). 
 
 Scenario B: "Slow Data Speeds on 5G (< 30 Mbps)" 
 
 Check Fair Usage Policy (FUP) status. If high-speed quota is 100% consumed, speed throttles to 256 Kbps. 
 Send network profile refresh OTA signal via CSR portal:  Action -> HSS Refresh -> Radio Reset .
دليل الدعم الفني لشبكات الجيل الخامس 5G وإعدادات الأجهزة و VoLTE - المصرية للاتصالات WE
دليل خدمة العملاء: حل مشكلات شبكة الجيل الخامس (5G) وضبط نقاط الوصول APN وخدمات VoLTE / VoWiFi 
 كود السياسة:  WE-POL-5G-NET-2026 |  القسم:  الدعم الفني للشبكات اللاسلكية والهواتف الذكية 
 الإصدار:  3.2 |  تاريخ السريان:  2026 
 1. نظرة عامة ومتطلبات تشغيل شبكة 5G 
 أطلقت الشركة المصرية للاتصالات (WE) خدمات الجيل الخامس 5G بترددات النطاق العريض n78 (3.5 GHz) و n41 لتوفير سرعات فائقة وزمن استجابة فائق الانخفاض. يوضح هذا الدليل لممثلي خدمة العملاء (CSR) كيفية تشخيص أعطال الشبكة وحل مشكلات عدم ظهور إشارة 5G وتفعيل المكالمات الصوتية عالية الدقة VoLTE و VoWiFi. 
 2. جدول الترددات ونطاقات التشغيل المعتمدة في مصر 
 
 
 
 اسم التردد / النطاق 
 رقم النطاق (Band) 
 الاستخدام الرئيسي 
 السرعة القصوى المتوقعة 
 
 
 
 
 3500 MHz (C-Band) 
 n78 (TDD) 
 التغطية الرئيسية لشبكات 5G الخارجية والمناطق الحيوية 
 تصل إلى 1.2 Gbps 
 
 
 2600 MHz 
 n41 (TDD) 
 سعات إضافية لشبكة 5G والمناطق المزدحمة 
 تصل إلى 600 Mbps 
 
 
 1800 MHz 
 Band 3 (FDD) 
 الطبقة التأسيسية لـ 4G LTE ومرساة شبكة 5G NSA 
 تصل إلى 150 Mbps 
 
 
 800 / 900 MHz 
 Band 20 / 8 
 التغطية الداخلية داخل المباني (Indoor Coverage) 
 تصل إلى 40 Mbps 
 
 
 
 3. خطوات ضبط نقطة الوصول الرسمية (APN Configuration) 
 في حال عدم عمل باقة الإنترنت على الهاتف بعد تفعيل الخط، يتعين توجيه العميل لإدخال بيانات APN يدوياً: 
 
        Name: WE Internet 
        APN: we.internet 
        Proxy: Not Set 
        Port: Not Set 
        MCC: 602 
        MNC: 04 
        Authentication Type: None / PAP 
        APN Type: default,supl 
        APN Protocol: IPv4/IPv6 
        APN Roaming Protocol: IPv4
     
 4. خطوات تفعيل المكالمات الصوتية عبر الجيل الرابع (VoLTE) والواي فاي (VoWiFi) 
 تتيح خدمة VoLTE إجراء مكالمات صوتية فائقة الوضوح مع استمرار عمل الإنترنت بسرعة 5G/4G دون انقطاع، بينما تتيح VoWiFi إجراء المكالمات في المناطق ذات التغطية الضعيفة عبر أي شبكة واي فاي منزلية: 
 
 كود التفعيل الذاتي عبر USSD:  يطلب العميل  *400*1#  أو إرسال رسالة نصية مجانية تحتوي على  1  إلى  400 . 
 شروط التفعيل:  وجود شريحة 4G/5G حديثة (USIM) وتحديث نظام تشغيل الهاتف لآخر إصدار داعم لمشغل WE. 
 تفعيل VoWiFi من إعدادات الهاتف:  الدخول إلى  الإعدادات -> الشبكة والإنترنت -> بطاقات SIM -> مكالمات Wi-Fi -> تشغيل . 
 
 
 5. English Technical Troubleshooting Matrix for 5G Devices 
 Scenario A: "5G Icon does not appear on device" 
 
 Verify customer account has an active high-speed mobile data quota via BSS. 
 Verify customer is located within verified 5G coverage zones (Cairo, Giza, Alexandria, New Capital, Sheikh Zayed, New Cairo). 
 Instruct customer: Go to  Settings -> Cellular -> Cellular Data Options -> Voice & Data , and select  5G Auto  or  5G On . 
 Check if device is running Battery Saver mode (Low Power Mode disables 5G on iOS and Android). 
 
 Scenario B: "Slow Data Speeds on 5G (< 30 Mbps)" 
 
 Check Fair Usage Policy (FUP) status. If high-speed quota is 100% consumed, speed throttles to 256 Kbps. 
 Send network profile refresh OTA signal via CSR portal:  Action -> HSS Refresh -> Radio Reset .

<!-- section: sec_1 | title: دليل خدمة العملاء: حل مشكلات شبكة الجيل الخامس (5G) وضبط نقاط الوصول APN وخدمات VoLTE / VoWiFi | page: 1 | order: 1 | parent: root -->
## دليل خدمة العملاء: حل مشكلات شبكة الجيل الخامس (5G) وضبط نقاط الوصول APN وخدمات VoLTE / VoWiFi

كود السياسة:  WE-POL-5G-NET-2026 |  القسم:  الدعم الفني للشبكات اللاسلكية والهواتف الذكية

كود السياسة:

القسم:

الإصدار:  3.2 |  تاريخ السريان:  2026

الإصدار:

تاريخ السريان:

<!-- section: sec_2 | title: 1. نظرة عامة ومتطلبات تشغيل شبكة 5G | page: 1 | order: 2 | parent: root -->
## 1. نظرة عامة ومتطلبات تشغيل شبكة 5G

أطلقت الشركة المصرية للاتصالات (WE) خدمات الجيل الخامس 5G بترددات النطاق العريض n78 (3.5 GHz) و n41 لتوفير سرعات فائقة وزمن استجابة فائق الانخفاض. يوضح هذا الدليل لممثلي خدمة العملاء (CSR) كيفية تشخيص أعطال الشبكة وحل مشكلات عدم ظهور إشارة 5G وتفعيل المكالمات الصوتية عالية الدقة VoLTE و VoWiFi.

<!-- section: sec_3 | title: 2. جدول الترددات ونطاقات التشغيل المعتمدة في مصر | page: 1 | order: 3 | parent: root -->
## 2. جدول الترددات ونطاقات التشغيل المعتمدة في مصر

اسم التردد / النطاق | رقم النطاق (Band) | الاستخدام الرئيسي | السرعة القصوى المتوقعة
--- | --- | --- | ---
3500 MHz (C-Band) | n78 (TDD) | التغطية الرئيسية لشبكات 5G الخارجية والمناطق الحيوية | تصل إلى 1.2 Gbps
2600 MHz | n41 (TDD) | سعات إضافية لشبكة 5G والمناطق المزدحمة | تصل إلى 600 Mbps
1800 MHz | Band 3 (FDD) | الطبقة التأسيسية لـ 4G LTE ومرساة شبكة 5G NSA | تصل إلى 150 Mbps
800 / 900 MHz | Band 20 / 8 | التغطية الداخلية داخل المباني (Indoor Coverage) | تصل إلى 40 Mbps

<!-- section: sec_4 | title: 3. خطوات ضبط نقطة الوصول الرسمية (APN Configuration) | page: 1 | order: 4 | parent: root -->
## 3. خطوات ضبط نقطة الوصول الرسمية (APN Configuration)

في حال عدم عمل باقة الإنترنت على الهاتف بعد تفعيل الخط، يتعين توجيه العميل لإدخال بيانات APN يدوياً:

Name: WE Internet 
        APN: we.internet 
        Proxy: Not Set 
        Port: Not Set 
        MCC: 602 
        MNC: 04 
        Authentication Type: None / PAP 
        APN Type: default,supl 
        APN Protocol: IPv4/IPv6 
        APN Roaming Protocol: IPv4

<!-- section: sec_5 | title: 4. خطوات تفعيل المكالمات الصوتية عبر الجيل الرابع (VoLTE) والواي فاي (VoWiFi) | page: 1 | order: 5 | parent: root -->
## 4. خطوات تفعيل المكالمات الصوتية عبر الجيل الرابع (VoLTE) والواي فاي (VoWiFi)

تتيح خدمة VoLTE إجراء مكالمات صوتية فائقة الوضوح مع استمرار عمل الإنترنت بسرعة 5G/4G دون انقطاع، بينما تتيح VoWiFi إجراء المكالمات في المناطق ذات التغطية الضعيفة عبر أي شبكة واي فاي منزلية:

كود التفعيل الذاتي عبر USSD:  يطلب العميل  *400*1#  أو إرسال رسالة نصية مجانية تحتوي على  1  إلى  400 .

كود التفعيل الذاتي عبر USSD:

*400*1#

1

400

شروط التفعيل:  وجود شريحة 4G/5G حديثة (USIM) وتحديث نظام تشغيل الهاتف لآخر إصدار داعم لمشغل WE.

شروط التفعيل:

تفعيل VoWiFi من إعدادات الهاتف:  الدخول إلى  الإعدادات -> الشبكة والإنترنت -> بطاقات SIM -> مكالمات Wi-Fi -> تشغيل .

تفعيل VoWiFi من إعدادات الهاتف:

الإعدادات -> الشبكة والإنترنت -> بطاقات SIM -> مكالمات Wi-Fi -> تشغيل

<!-- section: sec_6 | title: 5. English Technical Troubleshooting Matrix for 5G Devices | page: 1 | order: 6 | parent: root -->
## 5. English Technical Troubleshooting Matrix for 5G Devices

Scenario A: "5G Icon does not appear on device"

Verify customer account has an active high-speed mobile data quota via BSS.

Verify customer is located within verified 5G coverage zones (Cairo, Giza, Alexandria, New Capital, Sheikh Zayed, New Cairo).

Instruct customer: Go to  Settings -> Cellular -> Cellular Data Options -> Voice & Data , and select  5G Auto  or  5G On .

Settings -> Cellular -> Cellular Data Options -> Voice & Data

5G Auto

5G On

Check if device is running Battery Saver mode (Low Power Mode disables 5G on iOS and Android).

Scenario B: "Slow Data Speeds on 5G (< 30 Mbps)"

Check Fair Usage Policy (FUP) status. If high-speed quota is 100% consumed, speed throttles to 256 Kbps.

Send network profile refresh OTA signal via CSR portal:  Action -> HSS Refresh -> Radio Reset .

Action -> HSS Refresh -> Radio Reset
