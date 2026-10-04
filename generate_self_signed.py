import subprocess
import os

def generate_certificate():
    if os.path.exists('server.crt') and os.path.exists('server.key'):
        print("SSL certificate files already exist.")
        response = input("Do you want to regenerate them? (y/n): ")
        if response.lower() != 'y':
            print("Keeping existing certificates.")
            return
    
    print("Generating self-signed SSL certificate...")
    print("This will create server.crt and server.key files.")
    
    try:
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', 'server.key', '-out', 'server.crt',
            '-days', '365', '-nodes'
        ], check=True, input=b'\n\n\n\n\n\n\n\n')
        print("\n✓ SSL certificate generated successfully!")
        print("Files created: server.crt, server.key")
    except subprocess.CalledProcessError:
        print("\n✗ Error: OpenSSL command failed.")
        print("Make sure OpenSSL is installed on your system.")
    except FileNotFoundError:
        print("\n✗ Error: OpenSSL not found.")
        print("Please install OpenSSL first:")
        print("  - Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        print("  - Linux: sudo apt-get install openssl")
        print("  - Mac: brew install openssl")

if __name__ == '__main__':
    generate_certificate()

