from toolmind.database.models.user import AdminUser, SystemUser
from toolmind.database.dao.llm import LLMDao
from loguru import logger

# 仅支持 LLM 类型（已不做 RAG，无 Embedding/Reranker）
LLM_TYPE_LIST = ['LLM']


class LLMService:

    @classmethod
    async def create_llm(cls, user_id: str, api_key: str, model: str,
                         base_url: str, provider: str, llm_type: str = 'LLM'):
        try:
            await LLMDao.create_llm(base_url=base_url, api_key=api_key,
                                    model=model, provider=provider, user_id=user_id, llm_type='LLM')
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
        if user_id == AdminUser or user_id == await cls.get_user_id_by_llm(llm_id):
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
    async def update_llm(cls, llm_id: str, model: str, base_url: str, api_key: str, provider: str, llm_type: str = 'LLM'):
        try:
            await LLMDao.update_llm(llm_id=llm_id, model=model, llm_type='LLM',
                                    base_url=base_url, api_key=api_key, provider=provider)
        except Exception as err:
            raise ValueError(f'Update LLM Appear Err: {err}')

    @classmethod
    async def get_personal_llm(cls, user_id: str):
        try:
            llm_data = await LLMDao.get_llm_by_user(user_id)
            result = []
            for data in llm_data:
                d = data.to_dict()
                if d["user_id"] == SystemUser:
                    d["api_key"] = "************"
                result.append(d)
            return {"LLM": result}
        except Exception as err:
            raise ValueError(f'Get Personal LLM Appear Err: {err}')

    @classmethod
    async def get_visible_llm(cls, user_id: str):
        try:
            user_data = await LLMDao.get_llm_by_user(user_id)
            system_data = await LLMDao.get_llm_by_user(SystemUser)
            result = []
            for data in (user_data + system_data):
                d = data.to_dict()
                if d["user_id"] == SystemUser:
                    d["api_key"] = "************"
                result.append(d)
            return {"LLM": result}
        except Exception as err:
            raise ValueError(f'Get Visible LLM Appear Err: {err}')

    @classmethod
    async def get_all_llm(cls, user_id: str = None):
        try:
            llm_data = await LLMDao.get_all_llm()
            result = []
            for data in llm_data:
                d = data.to_dict()
                d["api_key"] = "************"
                result.append(d)
            return {"LLM": result}
        except Exception as err:
            raise ValueError(f'Get All LLM Appear Err: {err}')

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
            llms = await LLMDao.get_llm_by_type(llm_type='LLM')
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
                llm = await LLMDao.get_llm_id_from_name(llm_name, SystemUser)
                return llm.llm_id
        except Exception as err:
            raise ValueError(f'Get LLM ID Err: {err}')
