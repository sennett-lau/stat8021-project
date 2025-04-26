import { ReactNode } from 'react';

import Header from './Header';

type Props = {
  children: ReactNode;
};

const Layout = (props: Props) => {
  const { children } = props;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="fixed top-0 left-0 right-0 h-20 bg-gray-950 border-b border-gray-800 z-50">
        <Header />
      </header>
      <main className="pt-20">{children}</main>
    </div>
  );
};

export default Layout;
