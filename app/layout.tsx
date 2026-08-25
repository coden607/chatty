import './globals.css';

export const metadata = {
  title: 'CHATTY Automation Dashboard',
  description: 'Production dashboard for the CHATTY automation system.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
