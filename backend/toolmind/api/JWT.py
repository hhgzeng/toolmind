from pydantic.v1 import BaseSettings


# 定义 Pydantic 的 BaseSettings 类
class Settings(BaseSettings):
    authjwt_secret_key: str = "secret"
    authjwt_token_location: list = ["cookies", "headers"]
    authjwt_cookie_csrf_protect: bool = False


# 配置JWT token的有效期
ACCESS_TOKEN_EXPIRE_TIME = 86400
