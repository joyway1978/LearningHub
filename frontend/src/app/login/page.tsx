import { Suspense } from 'react';
import { Metadata } from 'next';
import { LoginForm } from './LoginForm';
import { Loader2 } from 'lucide-react';

export const metadata: Metadata = {
  title: '登录 - AI Learning Platform',
  description: '登录您的AI Learning账号',
};

export const dynamic = 'force-dynamic';

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#fafaf9] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
