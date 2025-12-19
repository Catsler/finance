import axios from 'axios';

const api = axios.create({
    baseURL: '/api/v1',
    timeout: 10000,
});

// Quotes
export const getQuotes = async (symbols) => {
    const response = await api.get('/quotes', {
        params: { symbols: symbols.join(',') }
    });
    return response.data;
};

// Account
export const getAccount = async () => {
    const response = await api.get('/account');
    return response.data;
};

// Positions
export const getPositions = async () => {
    const response = await api.get('/positions');
    return response.data;
};

// Orders
export const getOrders = async (status = null, limit = 200) => {
    const params = { limit };
    if (status) params.status = status;
    const response = await api.get('/orders', { params });
    return response.data.orders || [];
};

export const placeOrder = async (orderData) => {
    const response = await api.post('/orders', orderData);
    return response.data;
};

export const cancelOrder = async (clientOrderId) => {
    const response = await api.post(`/orders/${clientOrderId}/cancel`);
    return response.data;
};

// Fills
export const getFills = async (limit = 500) => {
    const response = await api.get('/fills', { params: { limit } });
    return response.data;
};

// Events
export const getEvents = async (sinceId = null, limit = 500) => {
    const params = { limit };
    if (sinceId) params.since_id = sinceId;
    const response = await api.get('/events', { params });
    return response.data;
};

// Kill Switch
export const getKillSwitch = async () => {
    const response = await api.get('/risk/kill_switch');
    return response.data;
};

export const setKillSwitch = async (enabled) => {
    const response = await api.post('/risk/kill_switch', { enabled });
    return response.data;
};
