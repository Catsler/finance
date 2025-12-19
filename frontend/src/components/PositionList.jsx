import React, { useEffect, useState } from 'react';
import { Card, Table, Typography, Tag, Space } from 'antd';
import { useAppStore } from '../stores/useAppStore';
import { useAccountStore } from '../stores/useAccountStore';
import { useMarketStore } from '../stores/useMarketStore';

const { Text } = Typography;

const PositionList = () => {
    const { activeSymbol, setActiveSymbol } = useAppStore();
    const positionsBySymbol = useAccountStore(state => state.positionsBySymbol);
    const { getQuote, getName } = useMarketStore();

    // Convert positions dict to array and calculate derived metrics
    const [data, setData] = useState([]);

    useEffect(() => {
        // Run this calculation whenever positions or quotes change (via component re-render triggered by store subscriptions)
        // Note: For better performance with frequent updates, we might need a dedicated selector or effect.
        // For now, simple conversion is fine for <20 positions.

        const list = Object.values(positionsBySymbol)
            .filter(p => p.total_quantity > 0)
            .map(p => {
                const quote = getQuote(p.symbol)(useMarketStore.getState()) || {};
                const last = quote.last || 0;
                const cost = p.avg_cost || 0;
                const qty = p.total_quantity;
                const marketValue = last * qty;
                const pnlGross = (last - cost) * qty;
                const pnlRate = cost > 0 ? pnlGross / (cost * qty) : 0;

                return {
                    key: p.symbol,
                    symbol: p.symbol,
                    name: getName(p.symbol),
                    qty: p.total_quantity,
                    sellable: p.available_quantity,
                    cost: cost,
                    last: last,
                    marketValue: marketValue,
                    pnlGross: pnlGross,
                    pnlRate: pnlRate,
                };
            })
            // Sort by market value descending
            .sort((a, b) => b.marketValue - a.marketValue);

        setData(list);
    }, [positionsBySymbol, useMarketStore.getState().quotesBySymbol]); // Re-calc on updates

    const columns = [
        {
            title: '股票',
            key: 'name',
            width: 120,
            render: (_, record) => (
                <Space direction="vertical" size={0}>
                    <Text strong>{record.name}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{record.symbol}</Text>
                </Space>
            ),
        },
        {
            title: '持仓/可卖',
            key: 'qty',
            width: 100,
            render: (_, record) => (
                <Space direction="vertical" size={0}>
                    <Text>{record.qty}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>T+1: {record.sellable}</Text>
                </Space>
            ),
        },
        {
            title: '现价/成本',
            key: 'price',
            width: 100,
            render: (_, record) => (
                <Space direction="vertical" size={0}>
                    <Text>{record.last?.toFixed(2)}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{record.cost?.toFixed(2)}</Text>
                </Space>
            ),
        },
        {
            title: '浮盈*(比例)',
            key: 'pnl',
            align: 'right',
            width: 120,
            render: (_, record) => {
                const color = record.pnlGross > 0 ? '#cf1322' : record.pnlGross < 0 ? '#3f8600' : '#333';
                const sign = record.pnlGross > 0 ? '+' : '';
                return (
                    <Space direction="vertical" size={0} style={{ width: '100%', textAlign: 'right' }}>
                        <Text style={{ color, fontWeight: 'bold' }}>{sign}{record.pnlGross?.toFixed(0)}</Text>
                        <Text style={{ color, fontSize: 12 }}>
                            {sign}{(record.pnlRate * 100).toFixed(2)}%
                        </Text>
                    </Space>
                );
            },
        },
        {
            title: '市值',
            key: 'value',
            align: 'right',
            width: 100,
            render: (_, record) => (
                <Text strong>{Math.round(record.marketValue).toLocaleString()}</Text>
            ),
        },
    ];

    return (
        <Card
            title="持仓列表"
            size="small"
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, overflowY: 'auto', padding: 0 }}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>*浮盈未扣除卖出费用</Text>}
        >
            <Table
                dataSource={data}
                columns={columns}
                pagination={false}
                size="small"
                onRow={(record) => ({
                    onClick: () => setActiveSymbol(record.symbol),
                    style: {
                        cursor: 'pointer',
                        backgroundColor: activeSymbol === record.symbol ? '#e6f7ff' : 'inherit'
                    }
                })}
            />
        </Card>
    );
};

export default PositionList;
