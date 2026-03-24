'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Material } from '@/types';
import { MaterialCard } from '@/components/MaterialCard';
import { Loader2 } from 'lucide-react';

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [myMaterials, setMyMaterials] = useState<Material[]>([]);
  const [isLoadingMaterials, setIsLoadingMaterials] = useState(false);
  const [materialsError, setMaterialsError] = useState<string | null>(null);

  // 获取用户的课件
  useEffect(() => {
    if (!user) return;

    const fetchMyMaterials = async () => {
      setIsLoadingMaterials(true);
      setMaterialsError(null);
      try {
        const response = await api.get<{ items: Material[]; total: number }>(
          `/materials?uploader_id=${user.id}`
        );
        setMyMaterials(response.items);
      } catch (err) {
        console.error('Failed to fetch my materials:', err);
        setMaterialsError(err instanceof Error ? err.message : '获取课件失败');
      } finally {
        setIsLoadingMaterials(false);
      }
    };

    fetchMyMaterials();
  }, [user]);

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-20 sm:pt-24">
        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-stone-800 mb-2">个人中心</h1>
          <p className="text-stone-500">管理您的账户信息和偏好设置</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：用户信息卡片 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-stone-200 p-6">
              <div className="flex flex-col items-center">
                {/* 头像 */}
                <div className="w-24 h-24 rounded-full bg-primary text-white flex items-center justify-center text-3xl font-medium mb-4">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <h2 className="text-xl font-semibold text-stone-800">{user?.name}</h2>
                <p className="text-stone-500 text-sm mt-1">{user?.email}</p>
                <div className="mt-4 flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(!isEditing)}
                  >
                    {isEditing ? '取消编辑' : '编辑资料'}
                  </Button>
                </div>
              </div>

              <div className="mt-6 border-t border-stone-200 pt-6">
                <h3 className="text-sm font-medium text-stone-600 mb-3">账户信息</h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-stone-500">用户ID</span>
                    <span className="text-stone-800">{user?.id}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-stone-500">注册时间</span>
                    <span className="text-stone-800">
                      {user?.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '-'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-stone-500">账户状态</span>
                    <span className="text-green-600">
                      {user?.is_active ? '正常' : '已禁用'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-6 border-t border-stone-200 pt-6">
                <Button
                  variant="outline"
                  className="w-full text-red-600 border-red-200 hover:bg-red-50"
                  onClick={logout}
                >
                  退出登录
                </Button>
              </div>
            </div>
          </div>

          {/* 右侧：内容区域 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 基本信息编辑 */}
            {isEditing && (
              <div className="bg-white rounded-lg shadow-sm border border-stone-200 p-6">
                <h3 className="text-lg font-semibold text-stone-800 mb-4">编辑资料</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-stone-700 mb-1">
                      昵称
                    </label>
                    <Input
                      type="text"
                      defaultValue={user?.name}
                      placeholder="请输入昵称"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-stone-700 mb-1">
                      邮箱
                    </label>
                    <Input
                      type="email"
                      defaultValue={user?.email}
                      disabled
                      className="bg-stone-100"
                    />
                    <p className="text-xs text-stone-500 mt-1">邮箱地址不可修改</p>
                  </div>
                  <div className="flex gap-3 pt-2">
                    <Button>保存修改</Button>
                    <Button variant="outline" onClick={() => setIsEditing(false)}>
                      取消
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* 修改密码 */}
            <div className="bg-white rounded-lg shadow-sm border border-stone-200 p-6">
              <h3 className="text-lg font-semibold text-stone-800 mb-4">修改密码</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">
                    当前密码
                  </label>
                  <Input type="password" placeholder="请输入当前密码" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">
                    新密码
                  </label>
                  <Input type="password" placeholder="请输入新密码（至少8位）" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">
                    确认新密码
                  </label>
                  <Input type="password" placeholder="请再次输入新密码" />
                </div>
                <div className="pt-2">
                  <Button>修改密码</Button>
                </div>
              </div>
            </div>

            {/* 我的课件 */}
            <div className="bg-white rounded-lg shadow-sm border border-stone-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-stone-800">我的课件</h3>
                <Link href="/upload">
                  <Button variant="outline" size="sm">
                    上传新课件
                  </Button>
                </Link>
              </div>

              {isLoadingMaterials ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Loader2 className="w-8 h-8 text-amber-500 animate-spin mb-2" />
                  <p className="text-stone-500 text-sm">加载中...</p>
                </div>
              ) : materialsError ? (
                <div className="text-center py-8 text-red-500">
                  <p>加载失败</p>
                  <p className="text-sm mt-1">{materialsError}</p>
                </div>
              ) : myMaterials.length === 0 ? (
                <div className="text-center py-8 text-stone-500">
                  <p>暂无上传的课件</p>
                  <p className="text-sm mt-1">点击上方按钮上传您的第一个课件</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {myMaterials.map((material) => (
                    <MaterialCard key={material.id} material={material} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
