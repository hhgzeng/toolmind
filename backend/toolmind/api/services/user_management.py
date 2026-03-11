from typing import Dict, Any, List

from toolmind.database.dao.user import UserDao
from toolmind.database.dao.user_role import UserRoleDao
from toolmind.database.models.role import AdminRole, DefaultRole
from toolmind.api.services.user import UserService
from toolmind.schema.schemas import resp_200, resp_500
from loguru import logger
from toolmind.database.session import session_getter


class UserManagementService:

    @classmethod
    def get_user_list(cls, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """获取所有用户列表，包含角色和禁用状态，支持分页"""
        users = UserDao.get_all_users(page, limit)
        # 简单取一下总数
        total = len(UserDao.get_user_number())
        
        user_list = []
        for u in users:
            roles = UserRoleDao.get_user_roles(u.user_id)
            is_admin = any(r.role_id == AdminRole for r in roles)
            role_type = "admin" if is_admin else "user"
            
            user_list.append({
                "user_id": u.user_id,
                "user_name": u.user_name,
                "role": role_type,
                "is_disabled": u.delete,
                "create_time": u.create_time.isoformat() if u.create_time else None
            })
            
        return {
            "total": total,
            "items": user_list,
            "page": page,
            "limit": limit
        }

    @classmethod
    def update_user_password(cls, user_id: str, new_password: str):
        """管理员重置用户密码"""
        user = UserDao.get_user(user_id)
        if not user:
            return resp_500(message="用户不存在")
            
        try:
            encrypted_password = UserService.encrypt_sha256_password(new_password)
            UserDao.update_user(user_id=user.user_id, user_name=user.user_name, user_password=encrypted_password)
            return resp_200(message="密码修改成功")
        except Exception as e:
            logger.error(f"Failed to update password for user {user_id}: {e}")
            return resp_500(message="修改密码失败")

    @classmethod
    def update_user_role(cls, user_id: str, new_role: str):
        """修改用户角色 (admin/user)"""
        if new_role not in ["admin", "user"]:
            return resp_500(message="角色参数无效")
            
        user = UserDao.get_user(user_id)
        if not user:
            return resp_500(message="用户不存在")
            
        # 防止删除最后一个超级管理员（可选的安全防范）
        if user_id == "1" and new_role == "user":
            return resp_500(message="无法撤销超级管理员的权限")
            
        try:
            # 清除所有现有角色
            roles = UserRoleDao.get_user_roles(user_id)
            if roles:
                UserRoleDao.delete_user_roles(user_id, [r.role_id for r in roles])
                
            # 重新分配
            if new_role == "admin":
                UserRoleDao.set_admin_user(user_id)
            else:
                UserRoleDao.add_user_roles(user_id, [DefaultRole])
            return resp_200(message="角色修改成功")
        except Exception as e:
            logger.error(f"Failed to update role for user {user_id}: {e}")
            return resp_500(message="角色修改失败")

    @classmethod
    def toggle_user_status(cls, user_id: str, enable: bool):
        """启用或禁用账号 (修改 delete 字段)"""
        user = UserDao.get_user(user_id)
        if not user:
            return resp_500(message="用户不存在")
            
        if user_id == "1" and not enable:
            return resp_500(message="无法禁用超级管理员账号")
            
        try:
            with session_getter() as session:
                user.delete = not enable 
                session.add(user)
                session.commit()
            return resp_200(message="状态修改成功")
        except Exception as e:
            logger.error(f"Failed to toggle status for user {user_id}: {e}")
            return resp_500(message="状态修改失败")
