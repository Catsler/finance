import React from 'react';
import { Card, List, Input, Tag } from 'antd';
import { useAppStore } from '../stores/useAppStore';
import { useMarketStore } from '../stores/useMarketStore';

const { Search } = Input;

const WatchlistPanel = () => {
    const { activeSymbol, watchlistSymbols, setActiveSymbol } = useAppStore();
    const quotesBySymbol = useMarketStore((state) => state.quotesBySymbol);

    return (
        <Card
            title="监控列表"
            size="small"
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, overflowY: 'auto', padding: '8px 4px' }}
        >
            <Search
                placeholder="搜索股票"
                style={{ marginBottom: 8 }}
                disabled
            />
            <List
                size="small"
                dataSource={watchlistSymbols}
                renderItem={(symbol) => {
                    const quote = quotesBySymbol[symbol];
                    const isActive = symbol === activeSymbol;
                    const change = quote?.last && quote?.prev_close
                        ? ((quote.last - quote.prev_close) / quote.prev_close * 100).toFixed(2)
                        : '0.00';
                    const changeColor = parseFloat(change) >= 0 ? '#cf1322' : '#3f8600';

                    return (
                        <List.Item
                            onClick={() => setActiveSymbol(symbol)}
                            style={{
                                cursor: 'pointer',
                                background: isActive ? '#e6f7ff' : 'transparent',
                                padding: '8px 12px',
                            }}
                        >
                            <div style={{ flex: 1 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontWeight: 'bold' }}>{useMarketStore.getState().getName(symbol)}</span>
                                    <span style={{ fontSize: 12, color: '#999' }}>{symbol}</span>
                                </div>
                                <div style={{ fontSize: 12, color: '#666', marginTop: 4, display: 'flex', justifyContent: 'space-between' }}>
                                    <span>{quote?.last?.toFixed(2) || '-'}</span>
                                    <span style={{ color: changeColor }}>{change}%</span>
                                </div>
                            </div>
                        </List.Item>
                    );
                }}
            />
        </Card>
    );
};

export default WatchlistPanel;
