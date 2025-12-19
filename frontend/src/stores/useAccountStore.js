import { create } from 'zustand';

export const useAccountStore = create((set) => ({
    account: null,
    positionsBySymbol: {},

    setAccount: (account) => set({ account }),

    setPositions: (positions) => {
        const bySymbol = {};
        positions.forEach(p => {
            bySymbol[p.symbol] = p;
        });
        set({ positionsBySymbol: bySymbol });
    },

    getPosition: (symbol) => (state) => state.positionsBySymbol[symbol] || null,
}));
