import socket  # مكتبة للتعامل مع الشبكات
import threading  # مكتبة للخيوط المتوازية
import argparse  # مكتبة لمعالجة وسائط سطر الأوامر
import ssl  # مكتبة للتشفير SSL
import sys  # مكتبة للتعامل مع النظام

class Client:
    def __init__(self, host='localhost', port=65432, use_ssl=False, protocol='tcp', mode='normal'):
        self.host = host  # عنوان السيرفر
        self.port = port  # رقم المنفذ
        self.use_ssl = use_ssl  # تفعيل SSL
        self.protocol = protocol  # نوع البروتوكول
        self.mode = mode  # وضع التشغيل
        self.sock = None  # socket الاتصال
        self.running = True  # حالة التشغيل
        
    def connect_tcp(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # إنشاء socket TCP
            # عدم وضع timeout لضمان استمرار الاستماع
            
            if self.use_ssl:  # إذا كان SSL مفعل
                context = ssl.create_default_context()  # إنشاء سياق SSL
                context.check_hostname = False  # تعطيل فحص اسم المضيف
                context.verify_mode = ssl.CERT_NONE  # تعطيل التحقق من الشهادة
                self.sock = context.wrap_socket(self.sock, server_hostname=self.host)  # تطبيق SSL على socket
            
            print(f"Connecting to {self.host}:{self.port}...")  # رسالة محاولة الاتصال
            self.sock.connect((self.host, self.port))  # الاتصال بالسيرفر
            print(f"Connected!")  # رسالة نجاح الاتصال
            return True  # إرجاع نجاح
        except socket.timeout:  # إذا انتهى الوقت
            print(f"Timeout: Server not responding")  # رسالة timeout
            return False  # إرجاع فشل
        except ConnectionRefusedError:  # إذا رُفض الاتصال
            print(f"Connection refused: Server not running")  # رسالة رفض
            return False  # إرجاع فشل
        except socket.gaierror as e:  # خطأ DNS
            print(f"DNS error: {e}")  # رسالة خطأ DNS
            return False  # إرجاع فشل
        except ssl.SSLError as e:  # خطأ SSL
            print(f"SSL error: {e}")  # رسالة خطأ SSL
            return False  # إرجاع فشل
        except Exception as e:  # أي خطأ آخر
            print(f"Connection error: {e}")  # رسالة خطأ عام
            return False  # إرجاع فشل
    
    def connect_udp(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # إنشاء socket UDP
            self.sock.settimeout(5)  # تعيين timeout 5 ثواني
            print(f"UDP Client ready for {self.host}:{self.port}")  # رسالة جاهزية
            return True  # إرجاع نجاح
        except Exception as e:  # أي خطأ
            print(f"Error: {e}")  # رسالة خطأ
            return False  # إرجاع فشل
    
    def run_tcp(self):
        if not self.connect_tcp():  # إذا فشل الاتصال
            return  # إنهاء الدالة
        
        if self.mode == 'level1':  # إذا كان الوضع level1
            messages = [  # قائمة الرسائل
                "Hello from Level 1 Client!",  # الرسالة الأولى
                "This is message number 2",  # الرسالة الثانية
                "Message 3: Testing multiple messages",  # الرسالة الثالثة
                "Final message before closing"  # الرسالة الرابعة
            ]
            print("\nSending multiple messages...")  # رسالة بدء الإرسال
            for i, msg in enumerate(messages, 1):  # تكرار على الرسائل
                try:
                    print(f"[{i}/{len(messages)}] Sending: {msg}")  # طباعة رقم الرسالة
                    self.sock.sendall(msg.encode('utf-8'))  # إرسال الرسالة
                    try:
                        response = self.sock.recv(1024).decode('utf-8')  # استقبال الرد
                        if response:  # إذا كان هناك رد
                            print(f"  → {response}")  # طباعة الرد
                    except:
                        pass  # تجاهل الأخطاء
                except Exception as e:  # أي خطأ
                    print(f"Error: {e}")  # رسالة خطأ
                    break  # إنهاء الحلقة
            print("\nAll messages sent. Closing...")  # رسالة انتهاء
            return  # إنهاء الدالة
        
        username = input("Enter username: ").strip()  # قراءة اسم المستخدم
        if not username:  # إذا لم يكن هناك اسم مستخدم
            print("Username required")  # رسالة خطأ
            self.sock.close()  # إغلاق الاتصال
            return  # إنهاء الدالة
        
        print("Type messages (or 'exit' to quit)")  # رسالة تعليمات
        
        if self.mode == 'persistent':  # إذا كان الوضع persistent
            def receive_thread():  # دالة لاستقبال الرسائل في خيط منفصل
                try:
                    while self.running:  # طالما يعمل الكلاينت
                        data = self.sock.recv(1024).decode('utf-8')  # استقبال البيانات
                        if not data:  # إذا لم تكن هناك بيانات
                            break  # إنهاء الحلقة
                        if 'exit' in data.lower() or 'closing' in data.lower():  # إذا كانت الرسالة exit أو closing
                            print(f"\n[Server] {data}")  # طباعة الرسالة
                            self.running = False  # إيقاف التشغيل
                            sys.exit(0)  # إنهاء البرنامج
                        print(f"\n[Server] {data}")  # طباعة الرسالة
                        print("> ", end='', flush=True)  # طباعة prompt
                except:
                    pass  # تجاهل الأخطاء
            
            thread = threading.Thread(target=receive_thread)  # إنشاء خيط للاستقبال
            thread.daemon = True  # جعل الخيط daemon
            thread.start()  # بدء الخيط
        
        if self.mode == 'sequential':  # إذا كان الوضع sequential
            try:
                initial = self.sock.recv(1024).decode('utf-8')  # استقبال الرسالة الأولى
                print(f"[Server] {initial}")  # طباعة الرسالة
                if "WAIT" in initial:  # إذا كانت الرسالة تحتوي على WAIT
                    print("Waiting for your turn...")  # رسالة انتظار
                    while True:  # حلقة انتظار
                        msg = self.sock.recv(1024).decode('utf-8')  # استقبال الرسائل
                        print(f"[Server] {msg}")  # طباعة الرسالة
                        if "OK" in msg:  # إذا كانت الرسالة تحتوي على OK
                            break  # إنهاء الحلقة
            except:
                pass  # تجاهل الأخطاء
        
        if self.mode == 'normal':  # إذا كان الوضع normal
            def receive_thread():  # دالة لاستقبال الرسائل في خيط منفصل
                try:
                    while self.running:  # طالما يعمل الكلاينت
                        try:
                            data = self.sock.recv(1024).decode('utf-8')  # استقبال البيانات
                            if not data:  # إذا لم تكن هناك بيانات
                                break  # إنهاء الحلقة
                            
                            # إذا كانت الرسالة بصيغة "username: message" (رسالة من عميل آخر)
                            if ':' in data and not data.startswith('[') and 'Welcome' not in data and 'joined' not in data and 'left' not in data:  # إذا كانت رسالة من عميل آخر
                                parts = data.split(':', 1)  # تقسيم الرسالة
                                if len(parts) == 2:  # إذا كان هناك جزءان
                                    sender = parts[0].strip()  # استخراج اسم المرسل
                                    message = parts[1].strip()  # استخراج الرسالة
                                    if sender != username:  # إذا لم تكن من المستخدم نفسه
                                        print(f"\n[{sender}] {message}")  # طباعة الرسالة
                                        print("> ", end='', flush=True)  # طباعة prompt
                                        continue  # متابعة الحلقة
                            
                            # الرسائل الأخرى (رسائل النظام)
                            print(f"\n[Server] {data}")  # طباعة الرسالة
                            print("> ", end='', flush=True)  # طباعة prompt
                        except socket.timeout:  # إذا انتهى الوقت
                            continue  # متابعة الحلقة
                        except Exception as e:  # أي خطأ آخر
                            if self.running:  # طالما يعمل الكلاينت
                                print(f"\n[Error] Receive error: {e}")  # رسالة خطأ
                            break  # إنهاء الحلقة
                except Exception as e:  # أي خطأ آخر
                    if self.running:  # طالما يعمل الكلاينت
                        print(f"\n[Error] Thread error: {e}")  # رسالة خطأ
            
            thread = threading.Thread(target=receive_thread)  # إنشاء خيط للاستقبال
            thread.daemon = True  # جعل الخيط daemon
            thread.start()  # بدء الخيط
        
        try:
            while self.running:  # طالما يعمل الكلاينت
                message = input("> ").strip()  # قراءة الرسالة من المستخدم
                if message.lower() == 'exit':  # إذا كانت الرسالة exit
                    self.running = False  # إيقاف التشغيل
                    self.sock.sendall('exit'.encode('utf-8'))  # إرسال exit
                    break  # إنهاء الحلقة
                if message:  # إذا كانت هناك رسالة
                    formatted = f"{username}: {message}"  # تنسيق الرسالة بصيغة USERNAME: message
                    self.sock.sendall(formatted.encode('utf-8'))  # إرسال الرسالة
        except (EOFError, KeyboardInterrupt):  # إذا ضغط المستخدم Ctrl+C أو EOF
            self.running = False  # إيقاف التشغيل
            try:
                self.sock.sendall('exit'.encode('utf-8'))  # إرسال exit
            except:
                pass  # تجاهل الأخطاء
        
        print("Disconnected")  # رسالة انفصال
    
    def run_udp(self):
        if not self.connect_udp():  # إذا فشل الاتصال
            return  # إنهاء الدالة
        
        print("UDP Client ready. Type messages (or 'exit' to quit)")  # رسالة جاهزية
        
        while True:  # حلقة لا نهائية
            try:
                message = input("UDP> ").strip()  # قراءة الرسالة
                if message.lower() == 'exit':  # إذا كانت الرسالة exit
                    break  # إنهاء الحلقة
                if not message:  # إذا لم تكن هناك رسالة
                    continue  # الانتقال للتكرار التالي
                
                self.sock.sendto(message.encode('utf-8'), (self.host, self.port))  # إرسال الرسالة
                print(f"  → Sent: {message}")  # رسالة إرسال
                
                try:
                    data, addr = self.sock.recvfrom(1024)  # استقبال الرد
                    print(f"  ← {data.decode('utf-8')}")  # طباعة الرد
                except socket.timeout:  # إذا انتهى الوقت
                    print("  ← No response")  # رسالة عدم وجود رد
            except KeyboardInterrupt:  # إذا ضغط المستخدم Ctrl+C
                break  # إنهاء الحلقة
        
        print("UDP Client closed")  # رسالة إغلاق
    
    def run(self):
        if self.protocol == 'udp':  # إذا كان البروتوكول UDP
            self.run_udp()  # تشغيل كلاينت UDP
        else:  # إذا كان TCP
            self.run_tcp()  # تشغيل كلاينت TCP
        
        try:
            if self.sock:  # إذا كان socket موجود
                self.sock.close()  # إغلاق socket
        except:
            pass  # تجاهل الأخطاء

def main():
    parser = argparse.ArgumentParser(description='Socket Client')  # إنشاء parser للوسائط
    parser.add_argument('--host', default='localhost', help='Server host')  # إضافة وسيط host
    parser.add_argument('--port', type=int, default=65432, help='Server port')  # إضافة وسيط port
    parser.add_argument('--ssl', action='store_true', help='Enable SSL')  # إضافة وسيط ssl
    parser.add_argument('--protocol', choices=['tcp', 'udp'], default='tcp', help='Protocol')  # إضافة وسيط protocol
    parser.add_argument('--mode', choices=['normal', 'level1', 'persistent', 'sequential'], default='normal', help='Client mode')  # إضافة وسيط mode
    
    args = parser.parse_args()  # تحليل الوسائط
    
    client = Client(host=args.host, port=args.port, use_ssl=args.ssl, protocol=args.protocol, mode=args.mode)  # إنشاء الكلاينت
    client.run()  # تشغيل الكلاينت

if __name__ == '__main__':  # إذا كان الملف يُشغّل مباشرة
    main()  # تشغيل الدالة الرئيسية
