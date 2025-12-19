import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PaperDashboard from './pages/PaperDashboard';
import RealDashboardSkeleton from './pages/RealDashboardSkeleton';

const App = () => {
    return (
        <BrowserRouter>
            <Routes>
                {/* Root redirects to Paper mode by default */}
                <Route path="/" element={<Navigate to="/paper/dashboard" replace />} />

                {/* Paper Trading World */}
                <Route path="/paper/dashboard" element={<PaperDashboard />} />

                {/* Real Trading World (Isolated Skeleton) */}
                <Route path="/real/dashboard" element={<RealDashboardSkeleton />} />

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/paper/dashboard" replace />} />
            </Routes>
        </BrowserRouter>
    );
};

export default App;
