// router/index.ts
import type { RouteRecordRaw } from 'vue-router';
import { createRouter, createWebHistory } from 'vue-router';
import { ChatSidebar as Session, ChatInput as SessionDefaultPage, Sessions as TaskGraphPage } from '../pages/agent';
import { Login, Register } from '../pages/login';
import NotFound from '../pages/not-found';
import {
  Dashboard,
  General as GeneralSettings,
  Settings as Index,
  MCP as McpServer,
  Core as MindConfig,
  LLM as Model,
  Users as UserManagement,
  Search as WebSearchPage
} from '../pages/settings';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/',
    name: 'session',
    component: Session,
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: '',
        name: 'sessionDefaultPage',
        component: SessionDefaultPage,
      },
      {
        path: 'sessions/:session_id?',
        name: 'taskGraphPage',
        component: TaskGraphPage,
      }
    ]
  },
  {
    path: '/settings',
    name: 'index',
    component: Index,
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'mcp',
        name: 'mcp',
        meta: {
          current: 'mcp'
        },
        component: McpServer,
      },
      {
        path: 'model',
        name: 'model',
        meta: {
          current: 'model'
        },
        component: Model,
      },
      {
        path: 'core',
        name: 'core',
        meta: {
          current: 'core'
        },
        component: MindConfig,
      },
      {
        path: 'search',
        name: 'search',
        meta: {
          current: 'search'
        },
        component: WebSearchPage,
      },
      {
        path: 'dashboard',
        name: 'dashboard',
        meta: {
          current: 'dashboard'
        },
        component: Dashboard,
      },
      {
        path: 'general',
        name: 'general',
        meta: {
          current: 'general'
        },
        component: GeneralSettings,
      },
      {
        path: 'users',
        name: 'users',
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
    component: NotFound,
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
