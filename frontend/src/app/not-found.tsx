export const dynamic = 'force-dynamic';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#fafaf9] flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-[#1a1a2e] mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-[#1c1917] mb-4">页面未找到</h2>
        <p className="text-[#78716c] mb-8">抱歉，您访问的页面不存在。</p>
        <a
          href="/"
          className="inline-block px-6 py-3 bg-[#1a1a2e] text-white rounded-md hover:bg-[#2d2d44] transition-colors"
        >
          返回首页
        </a>
      </div>
    </div>
  );
}
