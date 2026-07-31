"""密码加密工具 - 使用bcrypt进行密码哈希"""
import bcrypt


def hash_password(password: str) -> str:
    """
    使用bcrypt对密码进行哈希

    Args:
        password: 明文密码

    Returns:
        密码哈希值（字符串格式）
    """
    # bcrypt.hashpw 需要bytes输入，返回bytes
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    Args:
        plain_password: 明文密码
        hashed_password: 存储的哈希密码

    Returns:
        密码是否匹配
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)
