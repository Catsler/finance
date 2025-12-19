import React, { useState } from 'react';
import { Card, Table, Tabs, Tag, Button, message } from 'antd';
import { useAppStore } from '../stores/useAppStore';
import { useTradeStore } from '../stores/useTradeStore';
import { useMarketStore } from '../stores/useMarketStore';
import { cancelOrder as apiCancelOrder } from '../api/paperApi';

const { TabPane } = Tabs;

const OrdersPanel = () => {
    const [cancelLoading, setCancelLoading] = useState({});
    const [showAll, setShowAll] = useState(false);
    const activeSymbol = useAppStore((state) => state.activeSymbol);
    const { orders, fills, events } = useTradeStore();
    const { getName } = useMarketStore();

    const getFilteredData = (items) => {
        if (!items || !Array.isArray(items)) return [];
        if (showAll) return items;
        return items.filter(item => item.symbol === activeSymbol);
    };

    const handleCancel = async (clientOrderId) => {
        setCancelLoading((prev) => ({ ...prev, [clientOrderId]: true }));
        try {
            await apiCancelOrder(clientOrderId);
            message.success('撤单成功');
        } catch (error) {
            message.error(`撤单失败: ${error.message}`);
        } finally {
            setCancelLoading((prev) => ({ ...prev, [clientOrderId]: false }));
        }
    };

    const symbolColumn = {
        title: '股票',
        dataIndex: 'symbol',
        key: 'symbol',
        width: 120,
        render: (symbol) => (
            <div>
                <div style={{ fontWeight: 'bold' }}>{getName(symbol)}</div>
                <div style={{ fontSize: 12, color: '#999' }}>{symbol}</div>
            </div>
        )
    };

    const orderColumns = [
        symbolColumn,
        {
            title: '方向',
            dataIndex: 'direction',
            key: 'direction',
            render: (dir) => (
                <Tag color={dir === 'BUY' ? 'red' : 'green'}>{dir === 'BUY' ? '买' : '卖'}</Tag>
            ),
        },
        { title: '数量', dataIndex: 'quantity', key: 'quantity' },
        { title: '价格', dataIndex: 'price', key: 'price', render: (p) => p?.toFixed(2) },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            render: (status) => {
                const colors = {
                    NEW: 'blue',
                    FILLED: 'green',
                    CANCELED: 'default',
                    REJECTED: 'red',
                };
                return <Tag color={colors[status]}>{status}</Tag>;
            },
        },
        {
            title: '已成交',
            dataIndex: 'filled_quantity',
            key: 'filled_quantity',
            render: (filled, record) => `${filled || 0}/${record.quantity}`,
        },
        {
            title: '操作',
            key: 'action',
            render: (_, record) => (
                record.status === 'NEW' && (
                    <Button
                        size="small"
                        loading={cancelLoading[record.client_order_id]}
                        onClick={() => handleCancel(record.client_order_id)}
                    >
                        撤单
                    </Button>
                )
            ),
        },
    ];

    const fillColumns = [
        symbolColumn,
        {
            title: '方向',
            dataIndex: 'direction',
            key: 'direction',
            render: (dir) => (
                <Tag color={dir === 'BUY' ? 'red' : 'green'}>{dir === 'BUY' ? '买' : '卖'}</Tag>
            ),
        },
        { title: '数量', dataIndex: 'quantity', key: 'quantity' },
        { title: '价格', dataIndex: 'price', key: 'price', render: (p) => p?.toFixed(2) },
        { title: '佣金', dataIndex: 'commission', key: 'commission', render: (c) => c?.toFixed(2) },
        { title: '时间', dataIndex: 'filled_at', key: 'filled_at' },
    ];

    const eventColumns = [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
        { title: '类型', dataIndex: 'event_type', key: 'event_type' },
        { title: '股票', dataIndex: 'symbol', key: 'symbol' },
        { title: '详情', dataIndex: 'details', key: 'details', ellipsis: true },
        { title: '时间', dataIndex: 'timestamp', key: 'timestamp' },
    ];

    return (
        <Card
            title="交易记录"
            size="small"
            extra={
                <Button
                    type="link"
                    onClick={() => setShowAll(!showAll)}
                    style={{ padding: 0 }}
                >
                    {showAll ? '显示当前股票' : '显示全部股票'}
                </Button>
            }
        >
            <Tabs defaultActiveKey="orders">
                <TabPane tab="委托" key="orders">
                    <Table
                        columns={orderColumns}
                        dataSource={getFilteredData(orders)}
                        rowKey="client_order_id"
                        size="small"
                        pagination={{ pageSize: 10 }}
                    />
                </TabPane>
                <TabPane tab="成交" key="fills">
                    <Table
                        columns={fillColumns}
                        dataSource={getFilteredData(fills)}
                        rowKey="fill_id"
                        size="small"
                        pagination={{ pageSize: 10 }}
                    />
                </TabPane>
                <TabPane tab="事件" key="events">
                    <Table
                        columns={eventColumns}
                        dataSource={getFilteredData(events)}
                        rowKey="id"
                        size="small"
                        pagination={{ pageSize: 10 }}
                    />
                </TabPane>
            </Tabs>
        </Card>
    );
};

export default OrdersPanel;
