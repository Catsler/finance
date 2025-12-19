import { create } from 'zustand';

export const useMarketStore = create((set) => ({
    quotesBySymbol: {},
    symbolNames: {}, // Cache for symbol -> name mapping
    lastQuoteFetchAt: null,

    setQuotes: (quotes) => {
        const bySymbol = {};
        const namesUpdate = {};

        quotes.forEach(q => {
            // Normalize: ensure 'last' field exists (backend may return 'price' instead)
            const normalized = {
                ...q,
                last: q.last ?? q.price ?? 0,
                prev_close: q.prev_close ?? 0,
            };
            bySymbol[q.symbol] = normalized;
            if (q.name) namesUpdate[q.symbol] = q.name;
        });

        set((state) => ({
            quotesBySymbol: bySymbol,
            symbolNames: { ...state.symbolNames, ...namesUpdate },
            lastQuoteFetchAt: Date.now()
        }));
    },

    // Helper to get name, fallback to symbol
    getName: (symbol) => {
        const state = useMarketStore.getState(); // Access state directly for helper usage
        return state.symbolNames[symbol] || symbol;
    },

    getQuote: (symbol) => (state) => state.quotesBySymbol[symbol] || null,
}));
