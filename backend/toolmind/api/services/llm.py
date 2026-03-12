from toolmind.database.dao.user_role import UserRoleDao
from toolmind.database.models.role import AdminRole
from toolmind.database.dao.llm import LLMDao
from loguru import logger


class LLMService:

    @classmethod
    def _is_admin(cls, user_id: str) -> bool:
        roles = UserRoleDao.get_user_roles(user_id)
        return any(one.role_id == AdminRole for one in roles)

    @classmethod
    async def create_llm(cls, user_id: str, api_key: str, model: str,
                         base_url: str, provider: str):
        try:
            await LLMDao.create_llm(base_url=base_url, api_key=api_key,
                                    model=model, provider=provider, user_id=user_id)
        except Exception as err:
            raise ValueError(f'Create LLM Appear Err: {err}')

    @classmethod
    async def delete_llm(cls, llm_id: str):
        try:
            await LLMDao.delete_llm(llm_id=llm_id)
        except Exception as err:
            raise ValueError(f'Delete LLM Appear Err: {err}')

    @classmethod
    async def verify_user_permission(cls, llm_id, user_id):
        if cls._is_admin(user_id) or user_id == await cls.get_user_id_by_llm(llm_id):
            pass
        else:
            raise ValueError(f"没有权限访问")

    @classmethod
    async def get_user_id_by_llm(cls, llm_id: str):
        try:
            llm = await LLMDao.get_user_id_by_llm(llm_id)
            return llm.user_id
        except Exception as err:
            raise ValueError(f'Get User Id By LLM Appear Err: {err}')

    @classmethod
    async def update_llm(cls, llm_id: str, model: str, base_url: str, api_key: str, provider: str):
        try:
            await LLMDao.update_llm(llm_id=llm_id, model=model,
                                    base_url=base_url, api_key=api_key, provider=provider)
        except Exception as err:
            raise ValueError(f'Update LLM Appear Err: {err}')

    @classmethod
    async def get_visible_llm(cls, user_id: str):
        try:
            # 当前系统无共享 LLM：可见列表即个人列表
            user_data = await LLMDao.get_llm_by_user(user_id)
            return {"LLM": [data.to_dict() for data in user_data]}
        except Exception as err:
            raise ValueError(f'Get Visible LLM Appear Err: {err}')

    @classmethod
    async def get_llm_by_id(cls, llm_id: str):
        try:
            llms = await LLMDao.get_llm_by_id(llm_id)
            return llms.to_dict()
        except Exception as err:
            raise ValueError(f'Get LLM By Id Appear Err: {err}')

    @classmethod
    async def get_one_llm(cls):
        try:
            llms = await LLMDao.get_all_llm()
            return llms[0].to_dict()
        except Exception as err:
            raise ValueError(f'Get One LLM Appear Err: {err}')

    @classmethod
    async def get_llm_type(cls):
        try:
            llms = await LLMDao.get_all_llm()
            return [llm.to_dict() for llm in llms]
        except Exception as err:
            raise ValueError(f'Get LLM Type Appear Err: {err}')

    @classmethod
    async def get_llm_id_from_name(cls, llm_name, user_id):
        try:
            llm = await LLMDao.get_llm_id_from_name(llm_name, user_id)
            if llm:
                return llm.llm_id
            else:
                return None
        except Exception as err:
            raise ValueError(f'Get LLM ID Err: {err}')
