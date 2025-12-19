import { create } from 'zustand';

export const useAppStore = create((set) => ({
    activeSymbol: '002812.SZ',
    // 12只KDJ策略模拟盘股票
    watchlistSymbols: [
        '002812.SZ', '300568.SZ', '300750.SZ', '002594.SZ',
        '601012.SH', '600519.SH', '000858.SZ', '300059.SZ',
        '002475.SZ', '300760.SZ', '600309.SH', '000333.SZ'
    ],
    lastError: null,

    setActiveSymbol: (symbol) => set({ activeSymbol: symbol }),
    setError: (error) => set({ lastError: error }),
    clearError: () => set({ lastError: null }),
}));
