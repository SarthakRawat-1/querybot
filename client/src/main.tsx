import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'sonner';

import App from './App.tsx';
import ErrorBoundary from '@/components/ErrorBoundary';
import ThemeProvider from '@/components/theme/ThemeProvider';
import { TooltipProvider } from '@/components/ui/tooltip';
import './index.css';

// without importing the store into the client and creating a cycle.

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

createRoot(container).render(
  <ErrorBoundary>
    <ThemeProvider>
      <TooltipProvider>
        <BrowserRouter>
          <App />
          <Toaster position="top-right" richColors closeButton />
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  </ErrorBoundary>
);
