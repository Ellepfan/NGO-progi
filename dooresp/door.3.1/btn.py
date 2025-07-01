from cryptography.fernet import Fernet
key = Fernet.generate_key()  # Пример: b'ваш_секретный_ключ_32_байта=='
print(key)



cipher = Fernet(key)
encrypted_url = cipher.encrypt(b"http://192.168.9.50/switch/lsink_dor/turn_on")
print(encrypted_url)