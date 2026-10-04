import socket  # مكتبة للتعامل مع الشبكات
import threading  # مكتبة للخيوط المتوازية
import tkinter as tk  # مكتبة للواجهة الرسومية
from tkinter import scrolledtext, messagebox  # مكونات الواجهة
import argparse  # مكتبة لمعالجة وسائط سطر الأوامر

class GUIClient:
    def __init__(self, host='localhost', port=65432, use_ssl=False):
        self.host = host  # عنوان السيرفر
        self.port = port  # رقم المنفذ
        self.use_ssl = use_ssl  # تفعيل SSL
        self.sock = None  # الـ socket
        self.running = False  # حالة الاتصال
        self.username = None  # اسم المستخدم
        
        self.root = tk.Tk()  # إنشاء نافذة جديدة
        self.root.title("Socket Client")  # عنوان النافذة
        self.root.geometry("600x500")  # حجم النافذة
        
        self.setup_ui()  # إنشاء الواجهة
        
    def setup_ui(self):
        top_frame = tk.Frame(self.root)  # إنشاء إطار علوي
        top_frame.pack(pady=10)  # وضعه مع مسافة
        
        tk.Label(top_frame, text="Username:").pack(side=tk.LEFT, padx=5)  # نص "Username"
        self.username_entry = tk.Entry(top_frame, width=20)  # حقل إدخال اسم المستخدم
        self.username_entry.pack(side=tk.LEFT, padx=5)  # وضعه على اليسار
        
        self.connect_btn = tk.Button(top_frame, text="Connect", command=self.connect_to_server)  # زر الاتصال
        self.connect_btn.pack(side=tk.LEFT, padx=5)  # وضعه على اليسار
        
        self.disconnect_btn = tk.Button(top_frame, text="Disconnect", command=self.disconnect, state=tk.DISABLED)  # زر الانفصال
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)  # وضعه على اليسار
        
        self.status_label = tk.Label(top_frame, text="Disconnected", fg="red")  # نص الحالة
        self.status_label.pack(side=tk.LEFT, padx=10)  # وضعه على اليسار
        
        self.chat_area = scrolledtext.ScrolledText(self.root, state=tk.DISABLED, wrap=tk.WORD)  # منطقة المحادثة
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)  # ملء المساحة
        
        bottom_frame = tk.Frame(self.root)  # إنشاء إطار سفلي
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)  # وضعه في الأسفل
        
        tk.Label(bottom_frame, text="Message:").pack(side=tk.LEFT)  # نص "Message"
        self.message_entry = tk.Entry(bottom_frame)  # حقل إدخال الرسالة
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)  # ملء المساحة
        self.message_entry.bind('<Return>', lambda e: self.send_message())  # Enter يرسل الرسالة
        
        self.send_btn = tk.Button(bottom_frame, text="Send", command=self.send_message, state=tk.DISABLED)  # زر الإرسال
        self.send_btn.pack(side=tk.LEFT)  # وضعه على اليسار
        
    def add_message(self, message, sender="System"):
        self.chat_area.config(state=tk.NORMAL)  # تفعيل منطقة المحادثة
        self.chat_area.insert(tk.END, f"[{sender}] {message}\n")  # إضافة الرسالة
        self.chat_area.config(state=tk.DISABLED)  # تعطيل منطقة المحادثة
        self.chat_area.see(tk.END)  # الانتقال لآخر سطر
        
    def connect_to_server(self):
        username = self.username_entry.get().strip()  # الحصول على اسم المستخدم
        if not username:  # إذا لم يكن هناك اسم
            messagebox.showerror("Error", "Please enter a username")  # رسالة خطأ
            return  # إنهاء الدالة
        
        self.username = username  # حفظ اسم المستخدم
        
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # إنشاء socket TCP
            # عدم وضع timeout لضمان استمرار الاستماع
            
            if self.use_ssl:  # إذا كان SSL مفعل
                import ssl  # استيراد SSL
                context = ssl.create_default_context()  # إنشاء سياق SSL
                context.check_hostname = False  # عدم فحص اسم المضيف
                context.verify_mode = ssl.CERT_NONE  # عدم فحص الشهادة
                self.sock = context.wrap_socket(self.sock, server_hostname=self.host)  # تطبيق SSL
            
            self.sock.connect((self.host, self.port))  # الاتصال بالسيرفر
            self.running = True  # تفعيل حالة الاتصال
            
            self.connect_btn.config(state=tk.DISABLED)  # تعطيل زر الاتصال
            self.disconnect_btn.config(state=tk.NORMAL)  # تفعيل زر الانفصال
            self.send_btn.config(state=tk.NORMAL)  # تفعيل زر الإرسال
            self.username_entry.config(state=tk.DISABLED)  # تعطيل حقل اسم المستخدم
            self.status_label.config(text="Connected", fg="green")  # تغيير الحالة إلى "Connected"
            
            self.add_message(f"Connected to {self.host}:{self.port}", "System")  # رسالة اتصال
            
            receive_thread = threading.Thread(target=self.receive_messages)  # إنشاء thread للاستقبال
            receive_thread.daemon = True  # جعل الـ thread daemon
            receive_thread.start()  # بدء الـ thread
            
        except ConnectionRefusedError:  # إذا رُفض الاتصال
            messagebox.showerror("Connection Error", f"Could not connect to server at {self.host}:{self.port}\nMake sure the server is running.")  # رسالة خطأ
        except Exception as e:  # أي خطأ آخر
            messagebox.showerror("Error", f"Connection error: {e}")  # رسالة خطأ
            self.running = False  # تعطيل حالة الاتصال
            if self.sock:  # إذا كان الـ socket موجود
                try:
                    self.sock.close()  # إغلاقه
                except:
                    pass  # تجاهل الأخطاء
                self.sock = None  # جعله None
    
    def disconnect(self):
        self.running = False  # تعطيل حالة الاتصال
        if self.sock:  # إذا كان الـ socket موجود
            try:
                self.sock.sendall('exit'.encode('utf-8'))  # إرسال "exit"
                self.sock.close()  # إغلاق الاتصال
            except:
                pass  # تجاهل الأخطاء
            self.sock = None  # جعله None
        
        self.connect_btn.config(state=tk.NORMAL)  # تفعيل زر الاتصال
        self.disconnect_btn.config(state=tk.DISABLED)  # تعطيل زر الانفصال
        self.send_btn.config(state=tk.DISABLED)  # تعطيل زر الإرسال
        self.username_entry.config(state=tk.NORMAL)  # تفعيل حقل اسم المستخدم
        self.status_label.config(text="Disconnected", fg="red")  # تغيير الحالة إلى "Disconnected"
        self.add_message("Disconnected from server", "System")  # رسالة انفصال
    
    def receive_messages(self):
        print(f"[DEBUG] Receive thread started for {self.username}")  # رسالة تصحيح
        try:
            while self.running:  # طالما الاتصال نشط
                try:
                    print(f"[DEBUG] Waiting for data... (username: {self.username})")  # رسالة تصحيح
                    data = self.sock.recv(1024).decode('utf-8')  # استقبال البيانات
                    if not data:  # إذا لم تكن هناك بيانات
                        print(f"[DEBUG] No data received, breaking")  # رسالة تصحيح
                        break  # إنهاء الحلقة
                    
                    print(f"[DEBUG] Received: {data} (username: {self.username})")  # رسالة تصحيح
                    
                    # إذا كانت الرسالة تحتوي على "joined" أو "left" (رسائل دخول/خروج)
                    if 'joined the chat' in data or 'left the chat' in data:  # إذا كانت رسالة دخول أو خروج
                        print(f"[DEBUG] System message: {data}")  # رسالة تصحيح
                        self.root.after(0, self.add_message, data, "System")  # إضافة الرسالة كرسالة نظام
                        continue  # متابعة الحلقة
                    
                    # إذا كانت الرسالة تحتوي على "Welcome" (رسالة ترحيب)
                    if 'Welcome' in data:  # إذا كانت رسالة ترحيب
                        print(f"[DEBUG] Welcome message: {data}")  # رسالة تصحيح
                        self.root.after(0, self.add_message, data, "System")  # إضافة الرسالة كرسالة نظام
                        continue  # متابعة الحلقة
                    
                    # إذا كانت الرسالة بصيغة "username: message" (رسالة من عميل آخر)
                    if ':' in data:  # إذا كانت الرسالة تحتوي على :
                        parts = data.split(':', 1)  # تقسيم الرسالة
                        if len(parts) == 2:  # إذا كان هناك جزءان
                            sender = parts[0].strip()  # استخراج اسم المرسل
                            message = parts[1].strip()  # استخراج الرسالة
                            print(f"[DEBUG] Parsed - Sender: '{sender}', Message: '{message}', My username: '{self.username}'")  # رسالة تصحيح
                            # إذا كانت الرسالة من المستخدم نفسه، لا يتم عرضها (لأنها معروضة بالفعل)
                            if sender != self.username:  # إذا لم تكن من المستخدم نفسه
                                # إضافة الرسالة في الواجهة بنفس شكل السيرفر [username] message
                                print(f"[DEBUG] Adding message from {sender} to UI")  # رسالة تصحيح
                                self.root.after(0, self.add_message, message, sender)  # إضافة الرسالة
                            else:
                                print(f"[DEBUG] Ignoring own message from {sender}")  # رسالة تصحيح
                            continue  # متابعة الحلقة
                    
                    # الرسائل الأخرى (رسائل النظام)
                    print(f"[DEBUG] Other message: {data}")  # رسالة تصحيح
                    self.root.after(0, self.add_message, data, "System")  # إضافة الرسالة
                except socket.timeout:  # إذا انتهى الوقت
                    print(f"[DEBUG] Socket timeout")  # رسالة تصحيح
                    continue  # متابعة الحلقة
                except Exception as e:  # أي خطأ آخر
                    print(f"[DEBUG] Exception in receive: {e} (type: {type(e).__name__})")  # رسالة تصحيح
                    import traceback
                    traceback.print_exc()  # طباعة تفاصيل الخطأ
                    if self.running:  # طالما الاتصال نشط
                        self.root.after(0, self.add_message, f"Receive error: {e}", "Error")  # رسالة خطأ
                    break  # إنهاء الحلقة
        except Exception as e:  # أي خطأ آخر
            print(f"[DEBUG] Exception in receive_messages: {e}")  # رسالة تصحيح
            import traceback
            traceback.print_exc()  # طباعة تفاصيل الخطأ
            if self.running:  # طالما الاتصال نشط
                self.root.after(0, self.add_message, f"Receive thread error: {e}", "Error")  # رسالة خطأ
        
        print(f"[DEBUG] Receive thread ended for {self.username}")  # رسالة تصحيح
        if self.running:  # طالما الاتصال نشط
            self.root.after(0, self.disconnect)  # قطع الاتصال
    
    def send_message(self):
        if not self.running or not self.sock:  # إذا لم يكن الاتصال نشط
            return  # إنهاء الدالة
        
        message = self.message_entry.get().strip()  # الحصول على الرسالة
        if not message:  # إذا لم تكن هناك رسالة
            return  # إنهاء الدالة
        
        if message.lower() == 'exit':  # إذا كانت الرسالة "exit"
            self.disconnect()  # قطع الاتصال
            return  # إنهاء الدالة
        
        formatted_message = f"{self.username}: {message}"  # تنسيق الرسالة
        try:
            self.sock.sendall(formatted_message.encode('utf-8'))  # إرسال الرسالة
            self.add_message(message, "You")  # إضافة الرسالة في المحادثة
            self.message_entry.delete(0, tk.END)  # مسح حقل الإدخال
        except Exception as e:  # أي خطأ
            self.add_message(f"Send error: {e}", "Error")  # رسالة خطأ
            self.disconnect()  # قطع الاتصال
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # عند إغلاق النافذة
        self.root.mainloop()  # بدء الحلقة الرئيسية
    
    def on_closing(self):
        if self.running:  # طالما الاتصال نشط
            self.disconnect()  # قطع الاتصال
        self.root.destroy()  # تدمير النافذة

def main():
    parser = argparse.ArgumentParser(description='GUI TCP Client')  # إنشاء parser للوسائط
    parser.add_argument('--host', default='localhost', help='Server host address')  # إضافة وسيط host
    parser.add_argument('--port', type=int, default=65432, help='Server port number')  # إضافة وسيط port
    parser.add_argument('--ssl', action='store_true', help='Enable SSL')  # إضافة وسيط ssl
    
    args = parser.parse_args()  # تحليل الوسائط
    
    client = GUIClient(host=args.host, port=args.port, use_ssl=args.ssl)  # إنشاء الكلاينت
    client.run()  # تشغيل الكلاينت

if __name__ == '__main__':  # إذا كان الملف يُشغّل مباشرة
    main()  # تشغيل الدالة الرئيسية
