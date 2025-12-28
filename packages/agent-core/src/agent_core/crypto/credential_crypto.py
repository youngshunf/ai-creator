"""
凭证加密工具 - 使用 AES-256-GCM 加密敏感凭证
@author Ysf
"""

import os
import base64
import secrets
import hashlib
from typing import Tuple, Optional


class CredentialCrypto:
    """
    凭证加密工具

    使用 AES-256-GCM 对称加密保护敏感凭证数据。
    支持：
    - 安全密钥生成
    - 密码派生密钥（PBKDF2）
    - 加密/解密字符串数据
    - 加密/解密二进制数据

    安全特性：
    - AES-256-GCM 认证加密
    - PBKDF2 密钥派生（600000 次迭代）
    - 随机 IV/Nonce
    - 认证标签验证

    使用示例:
        # 使用密码加密
        encrypted = CredentialCrypto.encrypt("api_key_12345", "my_password")
        decrypted = CredentialCrypto.decrypt(encrypted, "my_password")

        # 使用随机密钥
        key = CredentialCrypto.generate_key()
        encrypted = CredentialCrypto.encrypt_with_key("secret", key)
        decrypted = CredentialCrypto.decrypt_with_key(encrypted, key)
    """

    # PBKDF2 迭代次数（OWASP 2023 推荐值）
    PBKDF2_ITERATIONS = 600000

    # 盐长度（字节）
    SALT_LENGTH = 16

    # Nonce/IV 长度（字节，GCM 推荐 12 字节）
    NONCE_LENGTH = 12

    # 认证标签长度（字节）
    TAG_LENGTH = 16

    # AES 密钥长度（字节，256 位）
    KEY_LENGTH = 32

    @classmethod
    def encrypt(cls, plain_text: str, password: str) -> str:
        """
        使用密码加密字符串

        Args:
            plain_text: 明文字符串
            password: 加密密码

        Returns:
            Base64 编码的密文字符串
            格式: base64(salt + nonce + ciphertext + tag)
        """
        # 生成随机盐
        salt = secrets.token_bytes(cls.SALT_LENGTH)

        # 从密码派生密钥
        key = cls.derive_key(password, salt)

        # 加密
        encrypted_data = cls._encrypt_bytes(plain_text.encode("utf-8"), key)

        # 拼接 salt + encrypted_data
        result = salt + encrypted_data

        return base64.b64encode(result).decode("ascii")

    @classmethod
    def decrypt(cls, encrypted_text: str, password: str) -> str:
        """
        使用密码解密字符串

        Args:
            encrypted_text: Base64 编码的密文
            password: 解密密码

        Returns:
            解密后的明文字符串

        Raises:
            ValueError: 解密失败（密码错误或数据损坏）
        """
        try:
            # 解码
            data = base64.b64decode(encrypted_text)

            # 提取盐
            salt = data[: cls.SALT_LENGTH]
            encrypted_data = data[cls.SALT_LENGTH:]

            # 从密码派生密钥
            key = cls.derive_key(password, salt)

            # 解密
            decrypted = cls._decrypt_bytes(encrypted_data, key)

            return decrypted.decode("utf-8")
        except Exception as e:
            raise ValueError(f"解密失败: {e}")

    @classmethod
    def encrypt_with_key(cls, plain_text: str, key: bytes) -> str:
        """
        使用密钥直接加密

        Args:
            plain_text: 明文字符串
            key: 32 字节密钥

        Returns:
            Base64 编码的密文
        """
        if len(key) != cls.KEY_LENGTH:
            raise ValueError(f"密钥长度必须为 {cls.KEY_LENGTH} 字节")

        encrypted_data = cls._encrypt_bytes(plain_text.encode("utf-8"), key)
        return base64.b64encode(encrypted_data).decode("ascii")

    @classmethod
    def decrypt_with_key(cls, encrypted_text: str, key: bytes) -> str:
        """
        使用密钥直接解密

        Args:
            encrypted_text: Base64 编码的密文
            key: 32 字节密钥

        Returns:
            解密后的明文字符串
        """
        if len(key) != cls.KEY_LENGTH:
            raise ValueError(f"密钥长度必须为 {cls.KEY_LENGTH} 字节")

        try:
            encrypted_data = base64.b64decode(encrypted_text)
            decrypted = cls._decrypt_bytes(encrypted_data, key)
            return decrypted.decode("utf-8")
        except Exception as e:
            raise ValueError(f"解密失败: {e}")

    @classmethod
    def encrypt_bytes(cls, data: bytes, password: str) -> bytes:
        """
        加密二进制数据

        Args:
            data: 二进制数据
            password: 加密密码

        Returns:
            加密后的二进制数据（salt + nonce + ciphertext + tag）
        """
        salt = secrets.token_bytes(cls.SALT_LENGTH)
        key = cls.derive_key(password, salt)
        encrypted_data = cls._encrypt_bytes(data, key)
        return salt + encrypted_data

    @classmethod
    def decrypt_bytes(cls, encrypted_data: bytes, password: str) -> bytes:
        """
        解密二进制数据

        Args:
            encrypted_data: 加密的二进制数据
            password: 解密密码

        Returns:
            解密后的二进制数据
        """
        salt = encrypted_data[: cls.SALT_LENGTH]
        data = encrypted_data[cls.SALT_LENGTH:]
        key = cls.derive_key(password, salt)
        return cls._decrypt_bytes(data, key)

    @classmethod
    def generate_key(cls) -> bytes:
        """
        生成安全随机密钥

        Returns:
            32 字节随机密钥
        """
        return secrets.token_bytes(cls.KEY_LENGTH)

    @classmethod
    def generate_key_hex(cls) -> str:
        """
        生成安全随机密钥（十六进制字符串）

        Returns:
            64 字符的十六进制密钥字符串
        """
        return secrets.token_hex(cls.KEY_LENGTH)

    @classmethod
    def derive_key(cls, password: str, salt: bytes) -> bytes:
        """
        从密码派生密钥

        使用 PBKDF2-HMAC-SHA256 进行密钥派生。

        Args:
            password: 用户密码
            salt: 随机盐

        Returns:
            32 字节密钥
        """
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls.PBKDF2_ITERATIONS,
            dklen=cls.KEY_LENGTH,
        )
        return key

    @classmethod
    def _encrypt_bytes(cls, data: bytes, key: bytes) -> bytes:
        """
        内部加密方法（AES-256-GCM）

        Args:
            data: 要加密的数据
            key: 32 字节密钥

        Returns:
            nonce + ciphertext + tag
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ImportError(
                "未安装 cryptography 库，请运行: pip install cryptography"
            )

        # 生成随机 nonce
        nonce = secrets.token_bytes(cls.NONCE_LENGTH)

        # 创建 AESGCM 实例并加密
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)

        # 返回 nonce + ciphertext（包含 tag）
        return nonce + ciphertext

    @classmethod
    def _decrypt_bytes(cls, encrypted_data: bytes, key: bytes) -> bytes:
        """
        内部解密方法（AES-256-GCM）

        Args:
            encrypted_data: nonce + ciphertext + tag
            key: 32 字节密钥

        Returns:
            解密后的数据

        Raises:
            ValueError: 认证失败
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ImportError(
                "未安装 cryptography 库，请运行: pip install cryptography"
            )

        # 提取 nonce 和密文
        nonce = encrypted_data[: cls.NONCE_LENGTH]
        ciphertext = encrypted_data[cls.NONCE_LENGTH:]

        # 创建 AESGCM 实例并解密
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise ValueError(f"解密或认证失败: {e}")

        return plaintext

    @classmethod
    def hash_password(cls, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        哈希密码（用于存储）

        使用 PBKDF2-HMAC-SHA256 进行密码哈希。

        Args:
            password: 用户密码
            salt: 可选的盐，如果不提供则自动生成

        Returns:
            (hash_hex, salt_hex) 元组
        """
        if salt is None:
            salt = secrets.token_bytes(cls.SALT_LENGTH)

        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls.PBKDF2_ITERATIONS,
            dklen=cls.KEY_LENGTH,
        )

        return hash_bytes.hex(), salt.hex()

    @classmethod
    def verify_password(cls, password: str, hash_hex: str, salt_hex: str) -> bool:
        """
        验证密码

        Args:
            password: 待验证的密码
            hash_hex: 存储的密码哈希（十六进制）
            salt_hex: 存储的盐（十六进制）

        Returns:
            True 表示密码正确，False 表示密码错误
        """
        salt = bytes.fromhex(salt_hex)
        computed_hash, _ = cls.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, hash_hex)

    @classmethod
    def secure_random_string(cls, length: int = 32, alphabet: Optional[str] = None) -> str:
        """
        生成安全随机字符串

        Args:
            length: 字符串长度
            alphabet: 字符集，默认为字母数字

        Returns:
            随机字符串
        """
        if alphabet is None:
            alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

        return "".join(secrets.choice(alphabet) for _ in range(length))
