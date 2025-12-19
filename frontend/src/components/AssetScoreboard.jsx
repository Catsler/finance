import React, { useMemo } from 'react';
import { Card, Statistic, Row, Col } from 'antd';
import { RiseOutlined, FallOutlined, DollarOutlined, PieChartOutlined } from '@ant-design/icons';
import { useAccountStore } from '../stores/useAccountStore';
import { useMarketStore } from '../stores/useMarketStore';

const AssetScoreboard = () => {
    const account = useAccountStore(state => state.account);
    const positionsBySymbol = useAccountStore(state => state.positionsBySymbol);
    const { getQuote } = useMarketStore();

    // Calculate portfolio metrics
    const metrics = useMemo(() => {
        const cash = account?.cash || 0;
        const totalValue = account?.total_value || 0;

        // Calculate current market value and PnL from positions
        let marketValue = 0;
        let totalCost = 0;
        let todayPnL = 0;

        Object.values(positionsBySymbol).forEach(pos => {
            const qty = pos.total_quantity || 0;
            if (qty <= 0) return;

            const quote = getQuote(pos.symbol)(useMarketStore.getState());
            const last = quote?.last || 0;
            const prevClose = quote?.prev_close || 0;
            const avgCost = pos.avg_cost || 0;

            const posMarketValue = last * qty;
            const posCost = avgCost * qty;
            const posTodayPnL = (last - prevClose) * qty;

            marketValue += posMarketValue;
            totalCost += posCost;
            todayPnL += posTodayPnL;
        });

        const totalPnL = marketValue - totalCost;
        const positionRatio = totalValue > 0 ? (marketValue / totalValue) * 100 : 0;
        const todayPnLPercent = totalCost > 0 ? (todayPnL / totalCost) * 100 : 0;

        return {
            totalValue,
            cash,
            marketValue,
            totalPnL,
            todayPnL,
            todayPnLPercent,
            positionRatio
        };
    }, [account, positionsBySymbol, getQuote]);

    return (
        <Card
            style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none',
                marginBottom: 16
            }}
            bodyStyle={{ padding: '16px 24px' }}
        >
            <Row gutter={24} align="middle">
                {/* Total Assets */}
                <Col flex="1">
                    <Statistic
                        title={<span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>总资产</span>}
                        value={metrics.totalValue}
                        precision={2}
                        valueStyle={{ color: '#fff', fontSize: 28, fontWeight: 'bold' }}
                        prefix={<DollarOutlined />}
                    />
                </Col>

                {/* Day PnL */}
                <Col flex="1">
                    <Statistic
                        title={<span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>当日盈亏</span>}
                        value={metrics.todayPnL}
                        precision={2}
                        valueStyle={{
                            color: metrics.todayPnL >= 0 ? '#52c41a' : '#ff4d4f',
                            fontSize: 24,
                            fontWeight: 'bold'
                        }}
                        prefix={metrics.todayPnL >= 0 ? <RiseOutlined /> : <FallOutlined />}
                        suffix={
                            <span style={{ fontSize: 14, marginLeft: 8 }}>
                                ({metrics.todayPnL >= 0 ? '+' : ''}{metrics.todayPnLPercent.toFixed(2)}%)
                            </span>
                        }
                    />
                </Col>

                {/* Total PnL */}
                <Col flex="1">
                    <Statistic
                        title={<span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>总盈亏</span>}
                        value={metrics.totalPnL}
                        precision={2}
                        valueStyle={{
                            color: metrics.totalPnL >= 0 ? '#52c41a' : '#ff4d4f',
                            fontSize: 24,
                            fontWeight: 'bold'
                        }}
                        prefix={metrics.totalPnL >= 0 ? <RiseOutlined /> : <FallOutlined />}
                    />
                </Col>

                {/* Position Ratio */}
                <Col flex="1">
                    <Statistic
                        title={<span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>仓位</span>}
                        value={metrics.positionRatio}
                        precision={1}
                        valueStyle={{ color: '#fff', fontSize: 24 }}
                        suffix="%"
                        prefix={<PieChartOutlined />}
                    />
                </Col>

                {/* Cash */}
                <Col flex="1">
                    <Statistic
                        title={<span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>可用现金</span>}
                        value={metrics.cash}
                        precision={2}
                        valueStyle={{ color: '#fff', fontSize: 24 }}
                    />
                </Col>
            </Row>
        </Card>
    );
};

export default AssetScoreboard;
