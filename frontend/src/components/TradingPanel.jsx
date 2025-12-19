import React, { useState, useEffect } from 'react';
import { Card, Form, InputNumber, Button, Radio, Space, Switch, Modal, message, Tag, Tooltip } from 'antd';
import { InfoCircleOutlined, ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';
import { useAppStore } from '../stores/useAppStore';
import { useMarketStore } from '../stores/useMarketStore';
import { useAccountStore } from '../stores/useAccountStore';
import { useRiskStore } from '../stores/useRiskStore';
import { placeOrder, setKillSwitch as apiSetKillSwitch } from '../api/paperApi';
import axios from 'axios';

const TradingPanel = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [trend, setTrend] = useState(null);
    const activeSymbol = useAppStore((state) => state.activeSymbol);
    const quotesBySymbol = useMarketStore((state) => state.quotesBySymbol);
    const positionsBySymbol = useAccountStore((state) => state.positionsBySymbol);
    const { killSwitch, setKillSwitch: updateKillSwitch } = useRiskStore();

    const quote = quotesBySymbol[activeSymbol];
    const position = positionsBySymbol[activeSymbol];

    // Fetch daily trend
    useEffect(() => {
        const fetchTrend = async () => {
            try {
                const res = await axios.get(`/api/v1/trend/daily?symbol=${activeSymbol}`);
                setTrend(res.data);
            } catch (error) {
                console.error('Failed to fetch trend:', error);
            }
        };

        if (activeSymbol) {
            fetchTrend();
        }
    }, [activeSymbol]);

    const handleSubmit = async (values) => {
        setLoading(true);
        try {
            const orderData = {
                symbol: activeSymbol,
                direction: values.direction,
                quantity: values.quantity,
                order_type: values.orderType,
            };

            if (values.orderType === 'LIMIT') {
                orderData.limit_price = values.limitPrice;
            }

            await placeOrder(orderData);
            message.success('下单成功');
            form.resetFields();
        } catch (error) {
            message.error(`下单失败: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleQuickBuy = () => {
        form.setFieldsValue({
            direction: 'BUY',
            quantity: 400,
            orderType: 'AGGRESSIVE',
        });
    };

    const handleQuickSell = () => {
        const qty = Math.min(400, position?.available_quantity || 0);
        form.setFieldsValue({
            direction: 'SELL',
            quantity: qty,
            orderType: 'AGGRESSIVE',
        });
    };

    const handleKillSwitchChange = (checked) => {
        Modal.confirm({
            title: checked ? '启用 Kill Switch' : '关闭 Kill Switch',
            content: checked
                ? '确认启用紧急停止？这将禁止所有新订单。'
                : '确认关闭紧急停止？',
            onOk: async () => {
                try {
                    const result = await apiSetKillSwitch(checked);
                    updateKillSwitch(result.enabled, result.updated_at);
                    message.success(checked ? 'Kill Switch 已启用' : 'Kill Switch 已关闭');
                } catch (error) {
                    message.error(`操作失败: ${error.message}`);
                }
            },
        });
    };

    // Check if buying is allowed (v0.2.2: DOWN gate)
    const isBuyDisabled = killSwitch || trend?.trend === 'DOWN';
    const direction = Form.useWatch('direction', form);
    const { getName } = useMarketStore();

    return (
        <Card
            title={`交易面板 - ${getName(activeSymbol)} (${activeSymbol})`}
            size="small"
            extra={
                <Space>
                    <span style={{ marginRight: 8 }}>Kill Switch:</span>
                    <Switch
                        checked={killSwitch}
                        onChange={handleKillSwitchChange}
                        checkedChildren="ON"
                        unCheckedChildren="OFF"
                    />
                </Space>
            }
        >
            {/* Trend Display (v0.2.2) */}
            {trend && (
                <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 12, color: '#666' }}>日线趋势:</span>
                    {trend.trend === 'UP' && (
                        <Tag color="green" icon={<ArrowUpOutlined />}>
                            UP
                        </Tag>
                    )}
                    {trend.trend === 'DOWN' && (
                        <Tag color="red" icon={<ArrowDownOutlined />}>
                            DOWN
                        </Tag>
                    )}
                    {trend.trend === 'FLAT' && (
                        <Tag color="default" icon={<MinusOutlined />}>
                            FLAT
                        </Tag>
                    )}
                    <Tooltip title={`基于 ${trend.asof_date} 收盘 | MA${trend.ma} 斜率: ${(trend.slope * 100).toFixed(2)}%`}>
                        <InfoCircleOutlined style={{ color: '#999', fontSize: 12 }} />
                    </Tooltip>
                </div>
            )}

            {/* Quote Detail Header (v0.3 Phase 1) */}
            <div style={{
                background: '#f9f9f9',
                padding: '8px 12px',
                borderRadius: '4px',
                marginBottom: 16,
                border: '1px solid #eee'
            }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
                    <span style={{ fontSize: 24, fontWeight: 'bold', color: (quote?.change_pct >= 0) ? '#ff4d4f' : '#52c41a' }}>
                        {quote?.last?.toFixed(2) || '--'}
                    </span>
                    <span style={{ fontSize: 16, color: (quote?.change_pct >= 0) ? '#ff4d4f' : '#52c41a' }}>
                        {quote?.change_pct ? `${quote.change_pct > 0 ? '+' : ''}${quote.change_pct.toFixed(2)}%` : '--%'}
                    </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px 12px', fontSize: 12 }}>
                    <div><span style={{ color: '#999' }}>今开:</span> {quote?.open?.toFixed(2) || '--'}</div>
                    <div><span style={{ color: '#999' }}>最高:</span> {quote?.high?.toFixed(2) || '--'}</div>
                    <div><span style={{ color: '#999' }}>成交量:</span> {quote?.volume ? `${quote.volume}手` : '--'}</div>
                    <div><span style={{ color: '#999' }}>昨收:</span> {quote?.prev_close?.toFixed(2) || '--'}</div>
                    <div><span style={{ color: '#999' }}>最低:</span> {quote?.low?.toFixed(2) || '--'}</div>
                    <div><span style={{ color: '#999' }}>成交额:</span> {quote?.amount ? `${quote.amount.toFixed(1)}万` : '--'}</div>
                </div>
            </div>

            <div style={{ marginBottom: 16, padding: '0 4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ color: '#52c41a' }}>
                        卖一: <b>{quote?.ask1?.toFixed(2) || '--'}</b>
                        <small style={{ marginLeft: 4, color: '#999' }}>({quote?.ask1_volume || 0}手)</small>
                    </span>
                    <span style={{ color: '#ff4d4f' }}>
                        买一: <b>{quote?.bid1?.toFixed(2) || '--'}</b>
                        <small style={{ marginLeft: 4, color: '#999' }}>({quote?.bid1_volume || 0}手)</small>
                    </span>
                </div>
                {position && (
                    <div style={{ marginTop: 8, fontSize: 12, color: '#666', borderTop: '1px dashed #eee', paddingTop: 8 }}>
                        持仓: <b>{position.total_quantity}</b> | 可卖: <b style={{ color: '#1890ff' }}>{position.available_quantity}</b>
                    </div>
                )}
            </div>

            <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
                initialValues={{
                    direction: 'BUY',
                    quantity: 400,
                    orderType: 'AGGRESSIVE',
                }}
            >
                <Form.Item name="direction" label="方向">
                    <Radio.Group buttonStyle="solid">
                        <Radio.Button value="BUY" disabled={isBuyDisabled}>
                            买入
                        </Radio.Button>
                        <Radio.Button value="SELL" disabled={!position || position.available_quantity === 0}>
                            卖出
                        </Radio.Button>
                    </Radio.Group>
                </Form.Item>

                {trend?.trend === 'DOWN' && direction === 'BUY' && (
                    <div style={{ marginTop: -12, marginBottom: 12, fontSize: 12, color: '#ff4d4f' }}>
                        ⚠️ 日线趋势向下，禁止新开多仓
                    </div>
                )}

                <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
                    <InputNumber min={100} step={100} style={{ width: '100%' }} />
                </Form.Item>

                <Form.Item name="orderType" label="类型">
                    <Radio.Group>
                        <Radio value="AGGRESSIVE">对手价</Radio>
                        <Radio value="LIMIT">限价</Radio>
                    </Radio.Group>
                </Form.Item>

                <Form.Item
                    noStyle
                    shouldUpdate={(prev, curr) => prev.orderType !== curr.orderType}
                >
                    {({ getFieldValue }) =>
                        getFieldValue('orderType') === 'LIMIT' ? (
                            <Form.Item name="limitPrice" label="限价" rules={[{ required: true }]}>
                                <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
                            </Form.Item>
                        ) : null
                    }
                </Form.Item>

                <Form.Item>
                    <Space>
                        <Button type="primary" htmlType="submit" loading={loading} disabled={isBuyDisabled && direction === 'BUY'}>
                            {direction === 'BUY' && trend?.trend === 'DOWN' ? '趋势向下，禁止买入' : '下单'}
                        </Button>
                        <Button onClick={handleQuickBuy} disabled={isBuyDisabled}>买400</Button>
                        <Button onClick={handleQuickSell} disabled={killSwitch}>卖出</Button>
                    </Space>
                </Form.Item>
            </Form>
        </Card>
    );
};

export default TradingPanel;
