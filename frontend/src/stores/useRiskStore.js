import { create } from 'zustand';

export const useRiskStore = create((set) => ({
    killSwitch: false,
    killSwitchUpdatedAt: null,

    setKillSwitch: (enabled, updatedAt) => set({
        killSwitch: enabled,
        killSwitchUpdatedAt: updatedAt
    }),
}));
