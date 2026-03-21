// router/index.ts
import type { RouteRecordRaw } from 'vue-router';
import { createRouter, createWebHistory } from 'vue-router';
import { ChatInput, ChatSidebar, Sessions } from '../pages/agent';
import { Login, Register } from '../pages/login';

import {
  AgentConfig,
  Dashboard,
  GeneralSettings,
  MCPServer,
  Model,
  Settings,
  UserManagement,
  WebSearch
} from '../pages/settings';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/',
    name: 'ChatSidebar',
    component: ChatSidebar,
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'ChatInput',
        component: ChatInput,
      },
      {
        path: 'sessions/:session_id?',
        name: 'Sessions',
        component: Sessions,
      }
    ]
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    redirect: '/settings/general',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'mcp',
        name: 'MCPServer',
        meta: {
          current: 'mcp'
        },
        component: MCPServer,
      },
      {
        path: 'model',
        name: 'Model',
        meta: {
          current: 'model'
        },
        component: Model,
      },
      {
        path: 'config',
        name: 'AgentConfig',
        meta: {
          current: 'config'
        },
        component: AgentConfig,
      },
      {
        path: 'search',
        name: 'WebSearch',
        meta: {
          current: 'search'
        },
        component: WebSearch,
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        meta: {
          current: 'dashboard'
        },
        component: Dashboard,
      },
      {
        path: 'general',
        name: 'GeneralSettings',
        meta: {
          current: 'general'
        },
        component: GeneralSettings,
      },
      {
        path: 'users',
        name: 'UserManagement',
        meta: {
          current: 'users'
        },
        component: UserManagement,
      }
    ]
  },
  {
    path: '/:catchAll(.*)',
    name: 'not-found',
    redirect: '/',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes: routes as RouteRecordRaw[],
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');

  // 如果目标路由需要认证
  if (to.meta.requiresAuth) {
    if (token) {
      // 已登录，允许访问
      next();
    } else {
      // 未登录，跳转到登录页
      next('/login');
    }
  } else {
    // 不需要认证的路由（如登录页）
    if (to.path === '/login' && token) {
      // 已登录用户访问登录页，重定向到主页
      next('/');
    } else {
      next();
    }
  }
});

export default router;
