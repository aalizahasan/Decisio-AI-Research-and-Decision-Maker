import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import { Header } from './components/Header';
import { DecisionForm } from './components/DecisionForm';
import { HistorySidebar } from './components/HistorySidebar';
import { Footer } from './components/Footer';

export const App: React.FC = () => {
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<number | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  const handleSelectAnalysis = (id: number) => {
    setSelectedAnalysisId(id);
  };

  const handleNewAnalysis = () => {
    setSelectedAnalysisId(null);
  };

  const handleAnalysisSaved = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <AuthProvider>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Header />
        <main style={{ flex: 1 }}>
          <div className="container workspace-layout">
            <HistorySidebar
              selectedId={selectedAnalysisId}
              onSelectAnalysis={handleSelectAnalysis}
              onNewAnalysis={handleNewAnalysis}
              refreshTrigger={refreshTrigger}
            />
            <DecisionForm
              activeAnalysisId={selectedAnalysisId}
              onAnalysisSaved={handleAnalysisSaved}
              onNewAnalysis={handleNewAnalysis}
            />
          </div>
        </main>
        <Footer />
      </div>
    </AuthProvider>
  );
};

export default App;
