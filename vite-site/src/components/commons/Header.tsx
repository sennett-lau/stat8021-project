import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <div className="h-full flex items-center justify-between px-6">
      <div className="flex items-center space-x-2">
        <Link to="/" className="text-2xl font-bold text-blue-500">STAT8021</Link>
        <span className="text-gray-500">|</span>
        <span className="text-gray-300">News Portal</span>
      </div>
    </div>
  );
};

export default Header;
