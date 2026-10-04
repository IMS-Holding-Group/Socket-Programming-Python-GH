import socket  # مكتبة للتعامل مع الشبكات
import threading  # مكتبة للخيوط المتوازية
import argparse  # مكتبة لمعالجة وسائط سطر الأوامر
import ssl  # مكتبة للتشفير SSL
import os  # مكتبة للتعامل مع نظام التشغيل
import sys  # مكتبة للتعامل مع النظام

class Server:
    def __init__(self, host='0.0.0.0', port=65432, use_ssl=False, mode='threaded', protocol='tcp'):
        self.host = host  # عنوان الاستماع للسيرفر
        self.port = port  # رقم المنفذ
        self.use_ssl = use_ssl  # تفعيل SSL
        self.mode = mode  # وضع تشغيل السيرفر
        self.protocol = protocol  # نوع البروتوكول TCP أو UDP
        self.clients = {}  # قاموس يربط socket باسم المستخدم
        self.client_sockets = []  # قائمة بجميع الـ sockets المتصلة
        self.lock = threading.Lock()  # قفل للخيوط لمنع التعارض
        self.current_client = None  # العميل الحالي (للنمط المتسلسل)
        self.waiting_clients = []  # قائمة العملاء المنتظرين
        
    def start_tcp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # إنشاء socket TCP
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # السماح بإعادة استخدام العنوان
        sock.bind((self.host, self.port))  # ربط السيرفر بالعنوان والمنفذ
        sock.listen(5)  # الاستماع لـ 5 اتصالات في قائمة الانتظار
        
        if self.use_ssl:  # إذا كان SSL مفعل
            if not os.path.exists('server.crt') or not os.path.exists('server.key'):  # التحقق من وجود ملفات SSL
                print("SSL files not found. Run: python generate_self_signed.py")  # رسالة خطأ
                return  # إنهاء الدالة
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)  # إنشاء سياق SSL
            context.load_cert_chain('server.crt', 'server.key')  # تحميل الشهادة والمفتاح
            sock = context.wrap_socket(sock, server_side=True)  # تطبيق SSL على السيرفر
            print(f"SSL TCP Server listening on {self.host}:{self.port}")  # رسالة نجاح SSL
        else:  # إذا لم يكن SSL مفعل
            print(f"TCP Server listening on {self.host}:{self.port}")  # رسالة نجاح عادية
        
        print(f"Mode: {self.mode}")  # طباعة وضع التشغيل
        
        while True:  # حلقة لا نهائية
            try:
                client_socket, address = sock.accept()  # قبول اتصال جديد
                if self.mode == 'threaded':  # إذا كان الوضع threaded
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, address))  # إنشاء thread جديد
                    thread.daemon = True  # جعل الـ thread daemon
                    thread.start()  # بدء الـ thread
                elif self.mode == 'sequential':  # إذا كان الوضع sequential
                    thread = threading.Thread(target=self.handle_sequential, args=(client_socket, address))  # إنشاء thread للوضع المتسلسل
                    thread.daemon = True  # جعل الـ thread daemon
                    thread.start()  # بدء الـ thread
                elif self.mode == 'persistent':  # إذا كان الوضع persistent
                    self.handle_persistent(client_socket, address)  # معالجة المحادثة المستمرة
                    break  # إنهاء الحلقة
                else:  # أي وضع آخر
                    self.handle_client(client_socket, address)  # معالجة العميل مباشرة
            except KeyboardInterrupt:  # إذا ضغط المستخدم Ctrl+C
                print("\nServer shutting down...")  # رسالة إغلاق
                break  # إنهاء الحلقة
            except Exception as e:  # أي خطأ آخر
                print(f"Error: {e}")  # طباعة الخطأ
    
    def start_udp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # إنشاء socket UDP
        sock.bind((self.host, self.port))  # ربط السيرفر بالعنوان والمنفذ
        print(f"UDP Server listening on {self.host}:{self.port}")  # رسالة نجاح
        
        while True:  # حلقة لا نهائية
            try:
                data, address = sock.recvfrom(1024)  # استقبال بيانات UDP
                message = data.decode('utf-8')  # تحويل البيانات إلى نص
                print(f"[UDP] {address}: {message}")  # طباعة الرسالة
                response = f"Server received: {message}"  # إنشاء رد
                sock.sendto(response.encode('utf-8'), address)  # إرسال الرد
            except KeyboardInterrupt:  # إذا ضغط المستخدم Ctrl+C
                print("\nUDP Server shutting down...")  # رسالة إغلاق
                break  # إنهاء الحلقة
            except Exception as e:  # أي خطأ آخر
                print(f"Error: {e}")  # طباعة الخطأ
    
    def broadcast_message(self, message, sender_socket=None):
        # بث الرسالة لجميع العملاء المتصلين عدا المرسل
        with self.lock:  # استخدام القفل لمنع التعارض
            disconnected_clients = []  # قائمة العملاء المنفصلين
            sent_count = 0  # عدد الرسائل المرسلة
            print(f"[DEBUG] Broadcasting '{message}' to {len(self.client_sockets)} clients, excluding sender")  # رسالة تصحيح
            for client_sock in self.client_sockets:  # لكل عميل متصل
                if client_sock != sender_socket:  # إذا لم يكن المرسل
                    try:
                        client_sock.sendall(message.encode('utf-8'))  # إرسال الرسالة
                        sent_count += 1  # زيادة العداد
                        print(f"[DEBUG] Sent to client {client_sock.getpeername() if hasattr(client_sock, 'getpeername') else 'unknown'}")  # رسالة تصحيح
                    except Exception as e:  # إذا حدث خطأ
                        print(f"Error sending to client: {e}")  # طباعة الخطأ
                        disconnected_clients.append(client_sock)  # إضافة للقائمة
                else:
                    print(f"[DEBUG] Skipping sender socket")  # رسالة تصحيح
            
            # طباعة عدد العملاء الذين استلموا الرسالة
            if sent_count > 0:  # إذا كانت هناك رسائل مرسلة
                print(f"Broadcasted message to {sent_count} client(s)")  # رسالة تأكيد
            else:
                print(f"[WARNING] No clients received the message!")  # تحذير
            
            # إزالة العملاء المنفصلين
            for client_sock in disconnected_clients:
                if client_sock in self.client_sockets:
                    self.client_sockets.remove(client_sock)  # إزالته من قائمة الـ sockets
                if client_sock in self.clients:
                    username = self.clients[client_sock]  # الحصول على اسم المستخدم
                    del self.clients[client_sock]  # إزالته من القاموس
                    print(f"Client {username} disconnected (connection error)")  # رسالة انفصال
    
    def handle_client(self, client_socket, address):
        username = None  # اسم المستخدم
        try:
            # إضافة العميل الجديد للقائمة
            with self.lock:  # استخدام القفل
                self.client_sockets.append(client_socket)  # إضافة socket العميل
            
            while True:  # حلقة لا نهائية
                try:
                    data = client_socket.recv(1024).decode('utf-8')  # استقبال البيانات
                    if not data:  # إذا لم تكن هناك بيانات
                        break  # إنهاء الحلقة
                    if data.strip().lower() == 'exit':  # إذا كانت الرسالة exit
                        break  # إنهاء الحلقة
                    
                    print(f"Received from {address}: {data}")  # رسالة تصحيح - استقبال البيانات
                    
                    if ':' in data:  # إذا كانت الرسالة تحتوي على :
                        parts = data.split(':', 1)  # تقسيم الرسالة
                        if len(parts) == 2:  # إذا كان هناك جزءان
                            msg_username = parts[0].strip()  # استخراج اسم المستخدم
                            message = parts[1].strip()  # استخراج الرسالة
                            if username is None:  # إذا لم يكن هناك اسم مستخدم (أول رسالة)
                                username = msg_username  # حفظ اسم المستخدم
                                with self.lock:  # استخدام القفل
                                    self.clients[client_socket] = username  # إضافة العميل للقائمة
                                print(f"Client {address} registered as {username}")  # رسالة تسجيل على السيرفر
                                # إرسال رسالة ترحيب للعميل الجديد
                                client_socket.sendall(f"Welcome {username}! You are connected.".encode('utf-8'))
                                # إعلام العملاء الآخرين بوصول عميل جديد
                                self.broadcast_message(f"{username} joined the chat", client_socket)
                            else:  # إذا كان اسم المستخدم موجود (رسالة عادية)
                                print(f"[{username}] {message}")  # طباعة الرسالة على السيرفر
                                # بث الرسالة لجميع العملاء الآخرين
                                broadcast_msg = f"{username}: {message}"  # شكل الرسالة
                                print(f"Broadcasting: {broadcast_msg}")  # رسالة تصحيح
                                print(f"Total clients: {len(self.client_sockets)}")  # عدد العملاء المتصلين
                                self.broadcast_message(broadcast_msg, client_socket)  # بث الرسالة
                    else:  # إذا لم تكن الرسالة بصيغة USERNAME: message
                        print(f"[{address}] {data}")  # طباعة الرسالة مع العنوان
                        # بث الرسالة لجميع العملاء الآخرين
                        self.broadcast_message(f"[{address}] {data}", client_socket)
                except socket.timeout:  # إذا انتهى الوقت
                    continue  # متابعة الحلقة
                except socket.error as e:  # إذا حدث خطأ في الـ socket
                    print(f"Socket error for {address}: {e}")  # طباعة الخطأ
                    break  # إنهاء الحلقة
        except Exception as e:  # أي خطأ
            print(f"Error handling client {address}: {e}")  # طباعة الخطأ
        finally:  # في النهاية
            try:
                # إعلام العملاء الآخرين بانفصال هذا العميل
                if username:  # إذا كان هناك اسم مستخدم
                    self.broadcast_message(f"{username} left the chat", client_socket)
                client_socket.close()  # إغلاق الاتصال
            except:
                pass  # تجاهل الأخطاء
            with self.lock:  # استخدام القفل
                if client_socket in self.client_sockets:  # إذا كان العميل في القائمة
                    self.client_sockets.remove(client_socket)  # إزالة socket العميل
                if client_socket in self.clients:  # إذا كان العميل في القائمة
                    username = self.clients[client_socket]  # الحصول على اسم المستخدم
                    del self.clients[client_socket]  # إزالة العميل
                    print(f"Client {username} ({address}) disconnected")  # رسالة انفصال
    
    def handle_sequential(self, client_socket, address):
        with self.lock:  # استخدام القفل
            if self.current_client is not None:  # إذا كان هناك عميل حالي
                print(f"Client {address} waiting...")  # رسالة انتظار
                self.waiting_clients.append((client_socket, address))  # إضافة العميل لقائمة الانتظار
                client_socket.sendall("WAIT: Another client is active. Please wait...".encode('utf-8'))  # إرسال رسالة انتظار
                return  # إنهاء الدالة
            self.current_client = address  # جعل هذا العميل هو الحالي
            print(f"Client {address} is now active")  # رسالة تفعيل
            client_socket.sendall("OK: You are connected. Start sending messages.".encode('utf-8'))  # إرسال رسالة موافقة
        
        username = None  # اسم المستخدم
        try:
            while True:  # حلقة لا نهائية
                data = client_socket.recv(1024).decode('utf-8')  # استقبال البيانات
                if not data:  # إذا لم تكن هناك بيانات
                    break  # إنهاء الحلقة
                if data.strip().lower() == 'exit':  # إذا كانت الرسالة exit
                    break  # إنهاء الحلقة
                
                if ':' in data:  # إذا كانت الرسالة تحتوي على :
                    parts = data.split(':', 1)  # تقسيم الرسالة
                    if len(parts) == 2:  # إذا كان هناك جزءان
                        username = parts[0].strip()  # استخراج اسم المستخدم
                        message = parts[1].strip()  # استخراج الرسالة
                        print(f"[{username}] {message}")  # طباعة الرسالة
                        client_socket.sendall(f"Server received: {message}".encode('utf-8'))  # إرسال تأكيد
                else:  # إذا لم تكن الرسالة بصيغة USERNAME: message
                    print(f"[{address}] {data}")  # طباعة الرسالة مع العنوان
        except Exception as e:  # أي خطأ
            print(f"Error: {e}")  # طباعة الخطأ
        finally:  # في النهاية
            with self.lock:  # استخدام القفل
                if self.current_client == address:  # إذا كان هذا العميل هو الحالي
                    self.current_client = None  # إلغاء العميل الحالي
                    print(f"Client {address} disconnected")  # رسالة انفصال
                    if self.waiting_clients:  # إذا كان هناك عملاء في الانتظار
                        next_sock, next_addr = self.waiting_clients.pop(0)  # أخذ أول عميل من قائمة الانتظار
                        thread = threading.Thread(target=self.handle_sequential, args=(next_sock, next_addr))  # إنشاء thread جديد
                        thread.daemon = True  # جعل الـ thread daemon
                        thread.start()  # بدء الـ thread
            try:
                client_socket.close()  # إغلاق الاتصال
            except:
                pass  # تجاهل الأخطاء
    
    def handle_persistent(self, client_socket, address):
        print(f"Client {address} connected")  # رسالة اتصال
        print("Type 'exit' to close server")  # رسالة تعليمات
        
        def receive_thread():  # دالة لاستقبال الرسائل في thread منفصل
            try:
                while True:  # حلقة لا نهائية
                    data = client_socket.recv(1024).decode('utf-8')  # استقبال البيانات
                    if not data:  # إذا لم تكن هناك بيانات
                        break  # إنهاء الحلقة
                    if data.strip().lower() == 'exit':  # إذا كانت الرسالة exit
                        print("\nClient requested exit. Closing server...")  # رسالة إغلاق
                        client_socket.sendall("Server closing...".encode('utf-8'))  # إرسال رسالة إغلاق
                        sys.exit(0)  # إنهاء البرنامج
                    print(f"[Client] {data}")  # طباعة الرسالة
            except:
                pass  # تجاهل الأخطاء
        
        thread = threading.Thread(target=receive_thread)  # إنشاء thread للاستقبال
        thread.daemon = True  # جعل الـ thread daemon
        thread.start()  # بدء الـ thread
        
        try:
            while True:  # حلقة لا نهائية
                response = input("[Server] > ").strip()  # قراءة إدخال من السيرفر
                if response.lower() == 'exit':  # إذا كان الإدخال exit
                    print("Closing server...")  # رسالة إغلاق
                    client_socket.sendall("exit".encode('utf-8'))  # إرسال رسالة exit
                    sys.exit(0)  # إنهاء البرنامج
                if response:  # إذا كان هناك رد
                    client_socket.sendall(response.encode('utf-8'))  # إرسال الرد
        except KeyboardInterrupt:  # إذا ضغط المستخدم Ctrl+C
            sys.exit(0)  # إنهاء البرنامج
    
    def start(self):
        if self.protocol == 'udp':  # إذا كان البروتوكول UDP
            self.start_udp()  # بدء سيرفر UDP
        else:  # إذا كان TCP
            self.start_tcp()  # بدء سيرفر TCP

def main():
    parser = argparse.ArgumentParser(description='Socket Server')  # إنشاء parser للوسائط
    parser.add_argument('--host', default='0.0.0.0', help='Host address')  # إضافة وسيط host
    parser.add_argument('--port', type=int, default=65432, help='Port number')  # إضافة وسيط port
    parser.add_argument('--ssl', action='store_true', help='Enable SSL')  # إضافة وسيط ssl
    parser.add_argument('--mode', choices=['threaded', 'sequential', 'persistent'], default='threaded', help='Server mode')  # إضافة وسيط mode
    parser.add_argument('--protocol', choices=['tcp', 'udp'], default='tcp', help='Protocol type')  # إضافة وسيط protocol
    
    args = parser.parse_args()  # تحليل الوسائط
    
    server = Server(host=args.host, port=args.port, use_ssl=args.ssl, mode=args.mode, protocol=args.protocol)  # إنشاء السيرفر
    server.start()  # بدء السيرفر

if __name__ == '__main__':  # إذا كان الملف يُشغّل مباشرة
    main()  # تشغيل الدالة الرئيسية
