import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import Layout from '@/components/commons/Layout';
import IndexPage from '@/pages/IndexPage';

import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path='/' element={<IndexPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
