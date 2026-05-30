import type { Metadata, Viewport } from 'next'
import { DM_Sans, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { SystemStatusProvider } from '@/components/SystemStatusProvider'
import { ErrorBoundary } from '@/components/ErrorBoundary'

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
  weight: ['300', '400', '500', '600', '700'],
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
  weight: ['400', '500', '600'],
})

export const viewport: Viewport = {
  themeColor: '#09090B',
  width: 'device-width',
  initialScale: 1,
}

export const metadata: Metadata = {
  title: 'AStock 市场认知引擎',
  description: 'A股市场行为逻辑分析系统',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="dark" style={{ colorScheme: 'dark' }}>
      <body className={`${dmSans.variable} ${jetbrainsMono.variable} bg-[hsl(var(--bg-root))] text-foreground`}
        style={{ fontFamily: "var(--font-sans), 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif" }}>
        <div className="noise-overlay" />
        <ErrorBoundary>
          <SystemStatusProvider>
            {children}
          </SystemStatusProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
