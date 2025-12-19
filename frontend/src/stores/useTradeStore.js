import { create } from 'zustand';

export const useTradeStore = create((set) => ({
    orders: [],
    fills: [],
    events: [],
    eventsSinceId: 0,

    setOrders: (orders) => set({ orders }),
    setFills: (fills) => set({ fills }),

    setEvents: (events) => {
        set((state) => {
            const newEvents = [...state.events, ...events];
            const maxId = events.length > 0
                ? Math.max(...events.map(e => e.id || 0))
                : state.eventsSinceId;
            return {
                events: newEvents.slice(-1000), // Keep last 1000
                eventsSinceId: Math.max(state.eventsSinceId, maxId),
            };
        });
    },

    clearEvents: () => set({ events: [], eventsSinceId: 0 }),
}));
