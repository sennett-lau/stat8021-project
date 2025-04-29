const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8021';
const IS_MOCK_API = import.meta.env.VITE_IS_MOCK_API === 'true';

// Function to format API URL correctly - avoids double /api/api issue
const formatApiUrl = (path: string) => {
  // If BACKEND_URL already ends with /api, don't add it again
  if (BACKEND_URL === '/api') {
    return `${BACKEND_URL}${path.startsWith('/') ? path : '/' + path}`;
  }
  return `${BACKEND_URL}/api${path.startsWith('/') ? path : '/' + path}`;
};

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

interface SummaryItem {
  id: number;
  title: string;
  summary: string;
  created_at: string;
  news_articles_ids: number[];
  tldr: string[];
}

interface SummaryResponse {
  total: number;
  offset: number;
  limit: number;
  summaries: SummaryItem[];
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

// Mock data for summaries
const mockSummaryData: SummaryItem[] = [
  {
    id: 1,
    title: "HKUMed Introduces Groundbreaking AI for Thyroid Cancer Diagnosis",
    summary: "The University of Hong Kong's medical school (HKUMed) has introduced a pioneering AI model capable of diagnosing thyroid cancer with more than 90% accuracy, significantly enhancing efficiency by halving clinicians' pre-consultation time. This innovative AI model is trained to analyze and classify stages and risk categories of thyroid cancer, outperforming traditional methods used by healthcare professionals. According to HKUMed, this model represents a major advancement over the existing systems by the American Joint Committee on Cancer and the American Thyroid Association.",
    created_at: "2025-04-26T18:21:42.372227",
    news_articles_ids: [1, 2],
    tldr: [
      "The University of Hong Kong's medical school developed the first AI model able to diagnose thyroid cancer with high accuracy.",
      "The AI model achieves over 90% accuracy and reduces pre-consultation time for clinicians by 50%.",
      "This AI system can classify the stage and risk category of thyroid cancer effectively.",
      "HKUMed's AI model surpasses traditional manual methods for integrating clinical information in efficiency."
    ]
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
    const response = await fetch(formatApiUrl('/news'));
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

export const getNewsById = async (ids: number[]): Promise<NewsResponse> => {
  if (IS_MOCK_API) {
    console.log('Using mock data for getNewsById');
    const filteredNews = mockNewsData.filter(item => ids.includes(Number(item.id)));
    return Promise.resolve({
      total: filteredNews.length,
      offset: 0,
      limit: filteredNews.length,
      articles: filteredNews
    });
  }
  
  try {
    const queryParams = new URLSearchParams();
    const idsString = ids.join(',');
    queryParams.append('ids', idsString);
    
    const response = await fetch(formatApiUrl(`/news?${queryParams.toString()}`));
    if (!response.ok) {
      throw new Error('Failed to fetch news by ids');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching news by ids:', error);
    return {
      total: 0,
      offset: 0,
      limit: 0,
      articles: []
    };
  }
};

export const searchNews = async (query: string, limit?: number): Promise<NewsResponse> => {
  if (IS_MOCK_API) {
    console.log('Using mock data for searchNews');
    return Promise.resolve({
      total: mockNewsData.length,
      offset: 0,
      limit: limit ?? mockNewsData.length,
      articles: mockNewsData.filter(
        item => 
          item.title.toLowerCase().includes(query.toLowerCase()) || 
          item.content.toLowerCase().includes(query.toLowerCase())
      )
    });
  }
  
  try {
    const response = await fetch(formatApiUrl('/news/search'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ q: query, limit: limit })
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

export const getSummaries = async (): Promise<SummaryResponse> => {
  if (IS_MOCK_API) {
    console.log('Using mock data for getSummaries');
    return Promise.resolve({
      total: mockSummaryData.length,
      offset: 0,
      limit: mockSummaryData.length,
      summaries: mockSummaryData
    });
  }
  
  try {
    const response = await fetch(formatApiUrl('/summaries'));
    if (!response.ok) {
      throw new Error('Failed to fetch summaries');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching summaries:', error);
    return {
      total: 0,
      offset: 0,
      limit: 0,
      summaries: []
    };
  }
};

export const searchSummaries = async (query: string, limit?: number): Promise<SummaryResponse> => {
  if (IS_MOCK_API) {
    console.log('Using mock data for searchSummaries');
    return Promise.resolve({
      total: mockSummaryData.length,
      offset: 0,
      limit: limit ?? mockSummaryData.length,
      summaries: mockSummaryData.filter(
        item => 
          item.title.toLowerCase().includes(query.toLowerCase()) || 
          item.summary.toLowerCase().includes(query.toLowerCase())
      )
    });
  }
  
  try {
    const response = await fetch(formatApiUrl('/summaries/search'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ q: query, limit: limit })
    });
    if (!response.ok) {
      throw new Error('Failed to search summaries');
    }
    return await response.json();
  } catch (error) {
    console.error('Error searching summaries:', error);
    return {
      total: 0,
      offset: 0,
      limit: 0,
      summaries: []
    };
  }
};

export type { NewsItem, SummaryItem }; 