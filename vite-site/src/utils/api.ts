const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8021';
const IS_MOCK_API = import.meta.env.VITE_IS_MOCK_API === 'true';

interface NewsItem {
  id: string;
  title: string;
  content: string;
  pub_date: string;
  link: string;
  source: string;
}

interface NewsResponse {
  total: number;
  offset: number;
  limit: number;
  articles: NewsItem[];
}

// Mock data for development
const mockNewsData: NewsItem[] = [
  {
    id: '1',
    title: 'New Research in Statistics Released',
    content: 'A groundbreaking research paper on statistical methods has been published in the Journal of Statistical Sciences. The paper introduces novel approaches to multivariate analysis that could revolutionize the field.',
    pub_date: '2025-12-04T14:27:00',
    link: 'https://example.com/news/1',
    source: 'Journal of Statistical Sciences'
  },
  {
    id: '2',
    title: 'STAT8021 Course Updates',
    content: 'The STAT8021 course will be incorporating new practical sessions focused on hands-on data analysis using modern tools. Students are encouraged to prepare by reviewing the recommended reading material.',
    pub_date: '2025-12-04T14:27:00',
    link: 'https://example.com/news/2',
    source: 'University of Edinburgh'
  },
  {
    id: '3',
    title: 'Statistical Conference Announced',
    content: 'The International Statistical Conference will be held next month, featuring keynote speakers from leading universities. Registration is now open for both in-person and virtual attendance.',
    pub_date: '2025-12-04T14:27:00',
    link: 'https://example.com/news/3',
    source: 'International Statistical Conference'
  },
  {
    id: '4',
    title: 'New Data Visualization Tool Released',
    content: 'A new open-source tool for statistical data visualization has been released. The tool offers interactive features and supports multiple data formats, making it easier for researchers to present their findings.',
    pub_date: '2025-12-04T14:27:00',
    link: 'https://example.com/news/4',
    source: 'Technology'
  },
  {
    id: '5',
    title: 'Job Opportunities in Statistical Analysis',
    content: 'Several positions for statistical analysts have opened up at major research institutions. Candidates with experience in computational statistics and machine learning are particularly sought after.',
    pub_date: '2025-12-04T14:27:00',
    link: 'https://example.com/news/5',
    source: 'Career'
  }
];

export const getNews = async (): Promise<NewsResponse> => {
  if (IS_MOCK_API) {
    console.log('Using mock data for getNews');
    return Promise.resolve({
      total: mockNewsData.length,
      offset: 0,
      limit: mockNewsData.length,
      articles: mockNewsData
    });
  }
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/news`);
    if (!response.ok) {
      throw new Error('Failed to fetch news');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching news:', error);
    return {
      total: 0,
      offset: 0,
      limit: 0,
      articles: []
    };
  }
};

export const searchNews = async (query: string): Promise<NewsResponse> => {
  if (IS_MOCK_API) {
    console.log('Using mock data for searchNews');
    return Promise.resolve({
      total: mockNewsData.length,
      offset: 0,
      limit: mockNewsData.length,
      articles: mockNewsData.filter(
        item => 
          item.title.toLowerCase().includes(query.toLowerCase()) || 
          item.content.toLowerCase().includes(query.toLowerCase())
      )
    });
  }
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/news/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ q: query })
    });
    if (!response.ok) {
      throw new Error('Failed to search news');
    }
    return await response.json();
  } catch (error) {
    console.error('Error searching news:', error);
    return {
      total: 0,
      offset: 0,
      limit: 0,
      articles: []
    };
  }
};

export type { NewsItem }; 