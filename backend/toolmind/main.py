from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pyfiglet import Figlet
from toolmind.middleware import TraceIDMiddleware
from toolmind.settings import app_settings, initialize_app_settings


def register_router(app: FastAPI):
    """注册 API 路由和健康检查接口"""
    from toolmind.api.router import router

    app.include_router(router)

    @app.get("/health")
    def check_health():
        return {"status": "OK"}


def register_middleware(app: FastAPI):
    """注册全局中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TraceIDMiddleware)
    return app


async def init_config():
    """初始化应用配置和数据库"""
    await initialize_app_settings()

    # 导入必须在 settings 初始化之后
    from toolmind.database.init_data import init_database

    await init_database()


def print_logo():
    """在终端打印启动 Logo"""
    f = Figlet(font="slant")
    print(f.renderText("ToolMind"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动前初始化配置"""
    await init_config()
    register_router(app)
    print_logo()
    yield


def create_app():
    """创建并配置 FastAPI 实例"""
    app = FastAPI(
        title=app_settings.server.get("project_name", "ToolMind"),
        lifespan=lifespan,
    )

    # 注册中间件 (中间件不依赖数据库导入)
    register_middleware(app)

    # 配置 AuthJWT
    @AuthJWT.load_config
    def get_config():
        return app_settings

    # 全局异常处理：AuthJWTException
    @app.exception_handler(AuthJWTException)
    def authjwt_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code, content={"detail": exc.message}
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("toolmind.main:app", host="0.0.0.0", port=7860, reload=True)
