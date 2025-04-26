import { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { getNewsById, getSummaries, searchSummaries, type NewsItem, type SummaryItem } from '@/utils/api';

const IndexPage = () => {
  const [summaries, setSummaries] = useState<SummaryItem[]>([]);
  const [selectedSummary, setSelectedSummary] = useState<SummaryItem | null>(null);
  const [selectedNewsId, setSelectedNewsId] = useState<number | null>(null);
  const [newsItem, setNewsItem] = useState<NewsItem | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [newsModalOpen, setNewsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchSummaries = async () => {
      const summariesData = await getSummaries();
      setSummaries(summariesData.summaries);
      if (summariesData.summaries.length > 0) {
        setSelectedSummary(summariesData.summaries[0]);
      }
    };

    fetchSummaries();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const results = await searchSummaries(searchQuery);
      setSummaries(results.summaries);
      if (results.summaries.length > 0) {
        setSelectedSummary(results.summaries[0]);
      } else {
        setSelectedSummary(null);
      }
      setSearchOpen(false);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleReset = async () => {
    const summariesData = await getSummaries();
    setSummaries(summariesData.summaries);
    if (summariesData.summaries.length > 0) {
      setSelectedSummary(summariesData.summaries[0]);
    }
    setSearchQuery('');
  };

  const handleNewsClick = async (newsId: number) => {
    setIsLoading(true);
    setSelectedNewsId(newsId);
    try {
      const newsData = await getNewsById([newsId]);
      if (newsData.articles.length > 0) {
        setNewsItem(newsData.articles[0]);
        setNewsModalOpen(true);
      }
    } catch (error) {
      console.error('Failed to fetch news:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).replace(/(\d+)\/(\d+)\/(\d+), (\d+):(\d+):(\d+)/, '$3-$1-$2 $4:$5:$6');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)]">
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <h1 className="text-2xl font-bold text-gray-100">News Portal</h1>
        <button 
          onClick={() => setSearchOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Search
        </button>
      </div>
      
      <div className="flex flex-1 overflow-hidden">
        {/* Summaries List (Left Side) */}
        <div className="w-1/3 border-r border-gray-800 overflow-y-auto p-4 bg-gray-900">
          <div className="mb-4">
            {searchQuery && (
              <div className="flex items-center mb-2">
                <span className="text-sm text-gray-400">Search results for: <span className="font-semibold text-gray-300">{searchQuery}</span></span>
                <button 
                  onClick={handleReset}
                  className="ml-2 text-xs text-blue-400 hover:text-blue-300"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
          {summaries.length > 0 ? (
            <ul className="space-y-2">
              {summaries.map((item) => (
                <li 
                  key={item.id}
                  className={`p-3 rounded-md cursor-pointer transition-colors ${
                    selectedSummary?.id === item.id 
                      ? 'bg-blue-900/30 border-l-4 border-blue-500' 
                      : 'hover:bg-gray-800'
                  }`}
                  onClick={() => setSelectedSummary(item)}
                >
                  <h3 className="text-lg font-medium text-gray-200">{item.title}</h3>
                  <div className="flex items-center text-sm text-gray-400 mt-1">
                    <span className="mr-2">Summary</span>
                    <span>•</span>
                    <span className="ml-2">{formatDate(item.created_at)}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <p>No summaries found</p>
              {searchQuery && (
                <button 
                  onClick={handleReset}
                  className="mt-2 text-blue-400 hover:text-blue-300"
                >
                  Reset search
                </button>
              )}
            </div>
          )}
        </div>
        
        {/* Summary Content (Right Side) */}
        <div className="w-2/3 p-6 overflow-y-auto bg-gray-950">
          {selectedSummary ? (
            <div>
              <h2 className="text-2xl font-bold mb-2 text-gray-100">{selectedSummary.title}</h2>
              <div className="flex items-center text-sm text-gray-400 mb-4">
                <span className="mr-2">Created</span>
                <span>•</span>
                <span className="ml-2">{formatDate(selectedSummary.created_at)}</span>
              </div>
              
              {/* TLDR Section */}
              {selectedSummary.tldr && selectedSummary.tldr.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-xl font-semibold mb-2 text-gray-200">TLDR</h3>
                  <ul className="list-disc pl-5 space-y-1">
                    {selectedSummary.tldr.map((point, index) => (
                      <li key={index} className="text-gray-300">{point}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className="prose prose-invert max-w-none mb-6">
                <p className="text-gray-300">{selectedSummary.summary}</p>
              </div>
              
              {/* Related News Articles */}
              {selectedSummary.news_articles_ids && selectedSummary.news_articles_ids.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold mb-2 text-gray-200">Related News Articles</h3>
                  <ul className="space-y-2">
                    {selectedSummary.news_articles_ids.map((newsId) => (
                      <li key={newsId}>
                        <button
                          onClick={() => handleNewsClick(newsId)}
                          className="text-blue-400 hover:text-blue-300 hover:underline"
                        >
                          Article #{newsId}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <p>Select a summary to view its content</p>
            </div>
          )}
        </div>
      </div>

      {/* Search Modal */}
      <Dialog.Root open={searchOpen} onOpenChange={setSearchOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/70" />
          <Dialog.Content className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-900 rounded-lg shadow-lg p-6 w-[90%] max-w-md border border-gray-700">
            <Dialog.Title className="text-xl font-bold mb-4 text-gray-100">Search Summaries</Dialog.Title>
            <div className="mb-4">
              <textarea 
                className="w-full border border-gray-700 rounded-md p-2 h-24 resize-none bg-gray-800 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter your search query..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Dialog.Close asChild>
                <button className="px-4 py-2 border border-gray-700 rounded-md hover:bg-gray-800 transition-colors text-gray-300">
                  Cancel
                </button>
              </Dialog.Close>
              <button 
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-blue-900 disabled:text-gray-400"
                onClick={handleSearch}
                disabled={isSearching || !searchQuery.trim()}
              >
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* News Article Modal */}
      <Dialog.Root open={newsModalOpen} onOpenChange={setNewsModalOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/70" />
          <Dialog.Content className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-900 rounded-lg shadow-lg p-6 w-[90%] max-w-2xl border border-gray-700 max-h-[80vh] overflow-y-auto">
            {isLoading ? (
              <div className="flex justify-center items-center h-40">
                <p className="text-gray-400">Loading article...</p>
              </div>
            ) : newsItem ? (
              <>
                <Dialog.Title className="text-xl font-bold mb-4 text-gray-100">{newsItem.title}</Dialog.Title>
                <div className="flex items-center text-sm text-gray-400 mb-4">
                  <span className="mr-2">{newsItem.source}</span>
                  <span>•</span>
                  <span className="ml-2">{formatDate(newsItem.pub_date)}</span>
                </div>
                <div className="prose prose-invert max-w-none mb-4">
                  <p className="text-gray-300">{newsItem.content}</p>
                </div>
                {newsItem.link && (
                  <div className="mt-4">
                    <a 
                      href={newsItem.link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 hover:underline"
                    >
                      Read full article
                    </a>
                  </div>
                )}
              </>
            ) : (
              <div className="flex justify-center items-center h-40">
                <p className="text-gray-400">Article not found</p>
              </div>
            )}
            <div className="mt-6 flex justify-end">
              <Dialog.Close asChild>
                <button className="px-4 py-2 border border-gray-700 rounded-md hover:bg-gray-800 transition-colors text-gray-300">
                  Close
                </button>
              </Dialog.Close>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
};

export default IndexPage;
