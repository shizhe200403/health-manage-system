"""
支付宝 SDK 封装。
使用 python-alipay-sdk 库（pip install python-alipay-sdk）。

密钥有两种配置方式（优先使用文件路径方式）：

方式 A（推荐，生产环境）：将 pem 文件挂载到容器，通过文件路径读取
    ALIPAY_PRIVATE_KEY_FILE  — 应用私钥 pem 文件的绝对路径（PKCS8）
    ALIPAY_PUBLIC_KEY_FILE   — 支付宝公钥 pem 文件的绝对路径

方式 B（备用）：直接在 env 中存裸密钥字符串
    ALIPAY_PRIVATE_KEY       — 应用私钥（PKCS8 裸串，不含 header/footer）
    ALIPAY_PUBLIC_KEY        — 支付宝公钥（裸串，不含 header/footer）

其他配置项：
    ALIPAY_APP_ID            — 支付宝开放平台 APPID
    ALIPAY_SANDBOX           — true → 沙箱; false（默认）→ 正式环境
"""
import textwrap

from django.conf import settings


def _read_key(file_env: str, raw_env: str, header: str, footer: str) -> str:
    """
    优先从文件路径读取完整 PEM（含 header/footer）；
    否则从裸字符串重建 PEM。
    """
    file_path = getattr(settings, file_env, "")
    if file_path:
        with open(file_path, "r") as f:
            return f.read().strip()

    raw = getattr(settings, raw_env, "").strip().replace(" ", "").replace("\n", "")
    body = "\n".join(textwrap.wrap(raw, 64))
    return f"{header}\n{body}\n{footer}"


def get_alipay_client():
    """
    返回配置好的 AliPay 实例。
    若未配置 ALIPAY_APP_ID 则抛出 RuntimeError。
    """
    from alipay import AliPay

    app_id = getattr(settings, "ALIPAY_APP_ID", "")
    if not app_id:
        raise RuntimeError("支付宝未配置：请在环境变量中设置 ALIPAY_APP_ID 等参数。")

    app_private_key_string = _read_key(
        "ALIPAY_PRIVATE_KEY_FILE", "ALIPAY_PRIVATE_KEY",
        "-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----",
    )
    alipay_public_key_string = _read_key(
        "ALIPAY_PUBLIC_KEY_FILE", "ALIPAY_PUBLIC_KEY",
        "-----BEGIN PUBLIC KEY-----", "-----END PUBLIC KEY-----",
    )

    sandbox = getattr(settings, "ALIPAY_SANDBOX", False)

    client = AliPay(
        appid=app_id,
        app_notify_url=None,
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",
        debug=sandbox,
    )
    return client, sandbox

