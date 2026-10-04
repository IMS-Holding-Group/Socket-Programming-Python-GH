# Socket Programming Python - GH

## 1. ما هو المشروع؟

مشروع برمجة مقابس بايثون: خادم `server.py` وعميل طرفية `client.py` وعميل رسومي `gui_client.py` ومولّد شهادة `generate_self_signed.py`. README السابق في المجلد يشرح المستويات والمنافذ، والأوامر فيه تطابق وسائط argparse في الكود.

## 2. لماذا يوجد هذا المشروع؟

استنتاج من الكود: التمارين تغطي TCP وUDP، وعدة رسائل، ومحادثة تبقى مفتوحة، وخدمة عميل واحد ثم التالي، وخيوطاً لأكثر من عميل، وصيغة رسالة `username: message`، وTLS عند تمرير `--ssl`.

## 3. من يستخدمه؟

من يشغّل الخادم ثم العميل على الجهاز نفسه أو عبر عنوان IP. حسابات تطبيق مخزنة غير موجودة. اسم المستخدم يُكتب في جلسة العميل ضمن صيغة الرسالة.

## 4. ماذا يستطيع النظام أن يفعل؟

وسائط الخادم: `--host` الافتراضي 0.0.0.0، `--port` الافتراضي 65432، `--ssl`، `--mode` بقيم threaded (الافتراضي) أو sequential أو persistent، `--protocol` بقيم tcp (الافتراضي) أو udp.
وسائط العميل: `--host` localhost، `--port` 65432، `--ssl`، `--protocol` tcp أو udp، `--mode` normal (الافتراضي) أو level1 أو persistent أو sequential.
الواجهة `gui_client.py` عميل TCP بحقل رسائل وخيار SSL، بمكتبة tkinter.
`generate_self_signed.py` ينشئ `server.crt` و`server.key` عبر أمر openssl إن وُجد.

## 5. كيف يعمل النظام؟

صنف `Server` يفتح TCP ويستمع لطابور 5، أو UDP. مع SSL يحمّل الشهادة إن وُجد الملفان. العميل `Client` يتصل ويرسل حسب الوضع. في المسار النصي تُنسَّق الرسالة `username: message`. الخادم يرحّب بـ `Welcome {username}! You are connected.` أو يرد `Server received`. الوضع sequential يرسل `WAIT: Another client is active` ثم `OK: You are connected`. الوضع persistent يغلق عند exit.

## 6. أمثلة واقعية

Level 1 من README السابق: `python server.py` ثم `python client.py --mode level1` لإرسال عدة رسائل. UDP: المنفذ 65433 في أمثلة README مع `--protocol udp`. المحادثة المستمرة: المنفذ 65434 و`--mode persistent`. التسلسل: المنفذ 65435 و`--mode sequential`. مثال LAN في README يستخدم العنوان 192.168.1.100 كعنوان توضيحي للاستبدال.

## 7. رحلة المستخدم

تشغيل الخادم أولاً كما تذكر ملاحظات README السابق. ثم العميل أو الواجهة. كتابة الرسائل حتى إنهاء الوضع. لـ SSL: تشغيل المولّد ثم `--ssl` على الطرفين.

## 8. الوحدات والأقسام

| الملف | الدور |
| --- | --- |
| server.py | صنف Server |
| client.py | صنف Client |
| gui_client.py | صنف GUIClient عبر tkinter |
| generate_self_signed.py | openssl للشهادة |
| README.md السابق | أوامر المستويات |

## 9. الشركات والكيانات

غير موجود في الملفات الحالية.

## 10. الصلاحيات

أدوار تطبيق غير موجودة. من يصل إلى المنفذ المفتوح يستطيع الاتصال حسب وضع الخادم.

## 11. الأتمتة وWorkflows

خيوط `threading` في الوضع threaded. طابور مهام خارجي غير موجود.

## 12. التكامل بين الوحدات

العميل والواجهة يرسلان إلى الخادم نفسه. الشهادة التي يكتبها المولّد هي التي يحمّلها الخادم عند `--ssl`.

## 13. المصطلحات

| الوضع | المعنى في الكود |
| --- | --- |
| threaded | عملاء متزامنون بالخيوط، وهو الافتراضي |
| sequential | عميل واحد ثم التالي مع رسالة WAIT |
| persistent | اتصال يبقى وexit يغلق |
| level1 | وضع عميل لإرسال عدة رسائل |
| USERNAME: message | صيغة النص في العميل |

## 14. الأسئلة الشائعة

**هل أبدأ بالعميل؟** ملاحظات README السابق: ابدأ بالخادم.

**هل الواجهة تدعم UDP؟** `gui_client.py` ينشئ SOCK_STREAM. UDP في server.py وclient.py.

## 15. Architecture

```
client.py أو gui_client.py
  -> TCP أو UDP
  -> server.py (threaded | sequential | persistent)
  -> رد نصي
ومع --ssl:
  generate_self_signed.py -> server.crt + server.key
  -> ssl.wrap على المقبس
```

## 16. Tech Stack

Python: socket وthreading وargparse وssl وtkinter. openssl خارجي لإنشاء الشهادة. إصدار Python غير مكتوب في requirements لأن الملف غير موجود.

## 17. Project Structure

```
Socket Programming Python - GH/
  server.py
  client.py
  gui_client.py
  generate_self_signed.py
  README.md
```
ملفا الشهادة يُنشآن عند تشغيل المولّد وليسا جزءاً من المصدر حتى تُشغَّل الأداة.

## 18. Frontend

عميل طرفية وعميل tkinter (`scrolledtext` و`messagebox`). Enter في حقل الواجهة يستدعي الإرسال. الخادم بلا واجهة.

## 19. Backend

الأصناف Server وClient وGUIClient. نقطة الدخول `main` في كل ملف عبر argparse إلا أن الواجهة تبني النافذة بعد قراءة الوسائط.

## 20. Request Flow

```
python server.py --mode threaded --port 65432
python client.py --mode level1
  -> TCP connect
  -> send messages
  -> server recv 1024 and reply
SSL:
  context CLIENT_AUTH على الخادم ويحمّل server.crt وserver.key
  العميل context افتراضي مع CERT_NONE
```

## 21. Database

غير موجود في الملفات الحالية. الرسائل في الذاكرة أثناء الاتصال.

## 22. API

واجهة HTTP غير موجودة. التحكم بوسائط سطر الأوامر وبرسائل النص على المقبس.

## 23. Authentication & Authorization

تسجيل دخول تطبيق غير موجود. SSL اختياري. العميل يضبط `verify_mode = ssl.CERT_NONE` عند `--ssl`، أي يتخطى التحقق من الشهادة.

## 24. Security

SSL عبر ملفات الشهادة عند الطلب. العميل لا يتحقق من الشهادة (CERT_NONE). مهلة وأخطاء socket وDNS وSSL مذكورة في README السابق وموجودة كالتقاطات في client.py (`socket.timeout` و`socket.gaierror` و`ssl.SSLError`). حد محاولات دخول غير موجود.

## 25. Configuration

القيم الافتراضية للمضيف والمنفذ والوضع داخل argparse. مسارا الشهادة `server.crt` و`server.key` في مجلد التشغيل. أسرار بيئة غير موجودة. المفتاح الخاص الناتج من openssl يبقى ملفاً محلياً وقيمته غير منسوخة هنا.

## 26. Integrations

برنامج openssl على الجهاز لإنشاء الشهادة. شبكة LAN عند تغيير `--host` كما في README السابق.

## 27. Scheduled Jobs

غير موجود في الملفات الحالية.

## 28. File Storage

ملفا الشهادة في مجلد التشغيل بعد التوليد. تخزين رسائل على قرص غير موجود.

## 29. Logging & Monitoring

الطباعة على الطرفية وأخطاء الواجهة عبر messagebox. نظام مراقبة خارجي غير موجود.

## 30. Installation

1. تثبيت Python وopenssl عند الحاجة لـ SSL.
2. `python server.py`
3. `python client.py --mode level1`
أوامر UDP والمحادثة والتسلسل والـ SSL كما في README السابق داخل المجلد (منافذ الأمثلة 65432 و65433 و65434 و65435).

## 31. Development Guide

وضع خادم جديد يُضاف إلى choices في argparse ثم فرع في صنف Server. حقل واجهة جديد في `GUIClient`.

## 32. Deployment

الخادم يربط 0.0.0.0 افتراضياً فيقبل الاتصالات على الواجهات. شهادات إنتاج من جهة موثوقة وخطوات نشر خدمة غير موجودة في الملفات.

## 33. Backup & Recovery

غير موجود في الملفات الحالية.

## 34. Troubleshooting

| العرض | ما يطابق الكود أو README السابق |
| --- | --- |
| فشل SSL | غياب server.crt أو server.key |
| CERT بلا تحقق | CERT_NONE في العميل |
| العميل الثاني ينتظر | وضع sequential ورسالة WAIT |
| openssl غير معروف | المولّد يطبع تلميح التثبيت |

## 35. Dependencies

مكتبات Python القياسية: socket وthreading وargparse وssl وtkinter وsubprocess في المولّد. openssl خارجي. إصدار المتطلبات غير مثبت في ملف.

## 36. Known Limitations

عميل الواجهة TCP فقط ويتخطى التحقق من الشهادة مثل عميل الطرفية. الشهادة ذاتية التوقيع عند استخدام المولّد. ملف requirements غير موجود.

## 37. Current System State

| الحالة | التفصيل |
| --- | --- |
| موجود | خادم وعميل طرفية وواجهة وشهادات اختيارية |
| موثق سابقاً | مستويات المنافذ في README.md |
| غير موجود | قاعدة وواجهة ويب |

## 38. Architecture Decisions

استنتاج من الكود: الأوضاع وسائط `--mode` و`--protocol` حتى يغطي ملف خادم واحد التمارين. الواجهة tkinter منفصلة عن عميل الطرفية.

## 39. سجل التغييرات

أرقام إصدارات حزم غير موجودة. README السابق داخل المجلد يوثق أوامر المستويات ويبقى مصدراً لتلك الأوامر.

## System Overview

```
generate_self_signed.py -> server.crt / server.key
client.py أو gui_client.py
  -> TCP/UDP
  -> server.py
     threaded | sequential | persistent
```

## Quick Reference

| الجزء | التقنية | الموقع | الوظيفة |
| --- | --- | --- | --- |
| الخادم | Python socket | server.py | TCP/UDP والأوضاع وSSL |
| العميل | Python socket | client.py | أوضاع level1 وغيرها |
| الواجهة | tkinter | gui_client.py | عميل TCP رسومي |
| الشهادة | openssl | generate_self_signed.py | server.crt وserver.key |

## Quick Start

شغّل `python server.py` ثم `python client.py --mode level1`.

## For Non-Technical Users

برنامجان يتبادلان الرسائل عبر الشبكة على جهازك، مع خيار قفل SSL وواجهة نافذة للكتابة.

## For Developers

الأصناف Server وClient وGUIClient. الافتراضي TCP على 65432 والوضع threaded. SSL يحمّل server.crt وserver.key والعميل يستخدم CERT_NONE.
