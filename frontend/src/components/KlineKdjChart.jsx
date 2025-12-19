import React, { useEffect, useState, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import { Spin } from 'antd';
import axios from 'axios';

/**
 * Calculate KDJ indicator
 * 
 * Must match kdj_strategy/indicators.py logic (adjust=False)
 * 
 * @param {Array} candles - Array of {time, open, high, low, close, volume}
 * @param {number} n - RSV period (default 9)
 * @param {number} m1 - K smoothing (default 3)
 * @param {number} m2 - D smoothing (default 3)
 * @returns {Array} Array of {K, D, J} values
 */
function calculateKDJ(candles, n = 9, m1 = 3, m2 = 3) {
    if (!candles || candles.length < n) {
        return [];
    }

    const alpha1 = 1 / m1;  // 1/3 for K
    const alpha2 = 1 / m2;  // 1/3 for D

    const result = [];
    let K = null;
    let D = null;

    for (let i = 0; i < candles.length; i++) {
        // Calculate RSV (Raw Stochastic Value)
        let RSV;
        if (i < n - 1) {
            // Not enough data for rolling window, set RSV = 50
            RSV = 50;
        } else {
            const window = candles.slice(i - n + 1, i + 1);
            const lows = window.map(c => c.low);
            const highs = window.map(c => c.high);
            const LLV = Math.min(...lows);  // Lowest low in N periods
            const HHV = Math.max(...highs); // Highest high in N periods

            const close = candles[i].close;

            if (HHV === LLV) {
                RSV = 50;  // Avoid division by zero
            } else {
                RSV = ((close - LLV) / (HHV - LLV)) * 100;
            }
        }

        // Calculate K using EWMA (adjust=False)
        // K[0] = RSV[0]
        // K[i] = alpha * RSV[i] + (1 - alpha) * K[i-1]
        if (K === null) {
            K = RSV;
        } else {
            K = alpha1 * RSV + (1 - alpha1) * K;
        }

        // Calculate D using EWMA on K (adjust=False)
        // D[0] = K[0]
        // D[i] = alpha * K[i] + (1 - alpha) * D[i-1]
        if (D === null) {
            D = K;
        } else {
            D = alpha2 * K + (1 - alpha2) * D;
        }

        // Calculate J
        const J = 3 * K - 2 * D;

        result.push({ K, D, J });
    }

    return result;
}

/**
 * Map fill timestamp to candle index
 * Using bar_end_time semantics: find earliest candle.time >= fill.trade_time
 */
function mapFillToCandle(fills, candles) {
    return fills.map(fill => {
        const fillTime = new Date(fill.trade_time);

        // Find earliest candle where candle.time >= fill.trade_time
        const candleIndex = candles.findIndex(c => new Date(c.time) >= fillTime);

        return {
            ...fill,
            candleIndex: candleIndex >= 0 ? candleIndex : candles.length - 1
        };
    });
}

/**
 * Calculate realized PnL using average cost method with FULL-FEE ACCOUNTING (口径B)
 * 
 * BUY: Amortize fees into cost basis
 * SELL: Deduct fees from PnL
 * 
 * This ensures the displayed PnL represents true net profit/loss
 */
function calculateRealizedPnL(fills) {
    // Sort fills by trade_time
    const sortedFills = [...fills].sort((a, b) =>
        new Date(a.trade_time) - new Date(b.trade_time)
    );

    let qty = 0;
    let avgCost = 0;        // Cost without fees (matches positions.avg_cost)
    let avgCostNet = 0;     // Cost WITH fees amortized (for PnL calculation)

    return sortedFills.map(fill => {
        const feesTotal = fill.commission + fill.stamp_tax + fill.transfer_fee;
        let realizedPnL = 0;

        if (fill.direction === 'BUY') {
            // BUY: Amortize fees into net cost
            const costWithFees = fill.price + feesTotal / fill.quantity;

            if (qty + fill.quantity > 0) {
                avgCost = (qty * avgCost + fill.quantity * fill.price) / (qty + fill.quantity);
                avgCostNet = (qty * avgCostNet + fill.quantity * costWithFees) / (qty + fill.quantity);
            } else {
                avgCost = fill.price;
                avgCostNet = costWithFees;
            }
            qty += fill.quantity;
        } else {  // SELL
            // SELL: Calculate PnL using net cost (which includes buy fees)
            // Then deduct sell fees
            realizedPnL = (fill.price - avgCostNet) * fill.quantity - feesTotal;
            qty -= fill.quantity;
        }

        return {
            ...fill,
            realizedPnL,        // Net PnL (full-fee accounting)
            avgCost,            // Cost without fees (for comparison with positions.avg_cost)
            avgCostNet,         // Cost with fees (used in PnL calculation)
            feesTotal
        };
    });
}

/**
 * KlineKdjChart Component
 * 
 * Displays 60m K-line chart with KDJ indicator, volume, trade markers, and cost line
 */
const KlineKdjChart = ({ symbol, adjust = 'front', limit = 400 }) => {
    const [loading, setLoading] = useState(true);
    const [candles, setCandles] = useState([]);
    const [kdj, setKdj] = useState([]);
    const [fills, setFills] = useState([]);
    const [position, setPosition] = useState(null);
    const chartRef = useRef(null);

    useEffect(() => {
        if (!symbol) return;

        const fetchData = async () => {
            setLoading(true);
            try {
                // Fetch candles
                const candlesRes = await axios.get('/api/v1/candles', {
                    params: { symbol, tf: '60m', adjust, limit }
                });

                const data = candlesRes.data;
                if (data.candles && data.candles.length > 0) {
                    setCandles(data.candles);

                    // Calculate KDJ
                    const kdjData = calculateKDJ(data.candles);
                    setKdj(kdjData);
                }

                // Fetch fills for this symbol
                const fillsRes = await axios.get('/api/v1/fills', {
                    params: { limit: 500 }
                });
                const symbolFills = fillsRes.data.filter(f => f.symbol === symbol);
                setFills(symbolFills);

                // Fetch positions
                const positionsRes = await axios.get('/api/v1/positions');
                const pos = positionsRes.data.find(p => p.symbol === symbol);
                setPosition(pos || null);

            } catch (error) {
                console.error('Error fetching data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [symbol, adjust, limit]);

    // v0.2.1: 60s lightweight polling to detect new completed candles
    useEffect(() => {
        if (!symbol) return;

        let lastCompleteTime = null;

        const checkForNewCandle = async () => {
            try {
                // Lightweight request: only fetch limit=1 to check last_complete_time
                const res = await axios.get('/api/v1/candles', {
                    params: { symbol, tf: '60m', limit: 1 }
                });

                const newLastComplete = res.data.last_complete_time;

                // Detect if a new candle completed
                if (lastCompleteTime && newLastComplete !== lastCompleteTime) {
                    console.log(`🔄 [${symbol}] New 60m candle completed: ${newLastComplete}, refreshing...`);

                    // Trigger full data refresh (without showing loading spinner)
                    const candlesRes = await axios.get('/api/v1/candles', {
                        params: { symbol, tf: '60m', adjust, limit }
                    });

                    const data = candlesRes.data;
                    if (data.candles && data.candles.length > 0) {
                        setCandles(data.candles);
                        const kdjData = calculateKDJ(data.candles);
                        setKdj(kdjData);
                    }

                    // Also refresh fills and positions
                    const fillsRes = await axios.get('/api/v1/fills', { params: { limit: 500 } });
                    const symbolFills = fillsRes.data.filter(f => f.symbol === symbol);
                    setFills(symbolFills);

                    const positionsRes = await axios.get('/api/v1/positions');
                    const pos = positionsRes.data.find(p => p.symbol === symbol);
                    setPosition(pos || null);
                }

                lastCompleteTime = newLastComplete;
            } catch (error) {
                console.error('Error checking for new candle:', error);
            }
        };

        const interval = setInterval(checkForNewCandle, 60000); // 60s
        return () => clearInterval(interval);
    }, [symbol, adjust, limit]);

    const getOption = () => {
        if (!candles.length) return {};

        // Prepare data for ECharts
        const times = candles.map(c => c.time.substring(0, 16)); // "YYYY-MM-DDTHH:MM"
        const klineData = candles.map(c => [c.open, c.close, c.low, c.high]);
        const volumes = candles.map(c => c.volume);
        const kData = kdj.map(d => d.K.toFixed(2));
        const dData = kdj.map(d => d.D.toFixed(2));
        const jData = kdj.map(d => d.J.toFixed(2));

        // Map fills to candles and calculate PnL
        const fillsWithPnL = calculateRealizedPnL(fills);
        const mappedFills = mapFillToCandle(fillsWithPnL, candles);

        // Create markers for fills
        const buyMarkers = mappedFills
            .filter(f => f.direction === 'BUY')
            .map(f => ({
                name: 'B',
                coord: [f.candleIndex, candles[f.candleIndex].low],
                value: f.price.toFixed(2),
                itemStyle: { color: '#ff4444' },
                label: {
                    formatter: () => 'B',
                    position: 'bottom',
                    color: '#fff',
                    backgroundColor: '#ff4444',
                    padding: [2, 4],
                    borderRadius: 2
                },
                fillData: f
            }));

        const sellMarkers = mappedFills
            .filter(f => f.direction === 'SELL')
            .map(f => ({
                name: 'S',
                coord: [f.candleIndex, candles[f.candleIndex].high],
                value: f.price.toFixed(2),
                itemStyle: { color: '#00aa44' },
                label: {
                    formatter: () => 'S',
                    position: 'top',
                    color: '#fff',
                    backgroundColor: '#00aa44',
                    padding: [2, 4],
                    borderRadius: 2
                },
                fillData: f
            }));

        const allMarkers = [...buyMarkers, ...sellMarkers].sort((a, b) => a.coord[0] - b.coord[0]);

        // Cost line data (only if position exists)
        const costLineData = position && position.total_quantity > 0
            ? candles.map(() => position.avg_cost)
            : [];

        const series = [
            {
                name: 'K线',
                type: 'candlestick',
                data: klineData,
                xAxisIndex: 0,
                yAxisIndex: 0,
                itemStyle: {
                    color: '#ef5350',
                    color0: '#26a69a',
                    borderColor: '#ef5350',
                    borderColor0: '#26a69a'
                },
                markPoint: {
                    data: allMarkers,
                    tooltip: {
                        formatter: (params) => {
                            const fill = params.data.fillData;
                            if (!fill) return '';

                            // Find the mapped candle time for verification
                            const candleTime = candles[fill.candleIndex]?.time || 'N/A';

                            // Build tooltip content based on direction
                            let content = `
                                <b>${fill.direction}</b><br/>
                                <hr style="margin: 4px 0; border-color: #ddd;"/>
                                成交时间: ${new Date(fill.trade_time).toLocaleString('zh-CN')}<br/>
                                K线时间: ${candleTime.substring(0, 16)}<br/>
                                <hr style="margin: 4px 0; border-color: #ddd;"/>
                                成交价格: ${fill.price.toFixed(2)}<br/>
                                成交数量: ${fill.quantity}<br/>
                                手续费合计: ${fill.feesTotal.toFixed(2)}<br/>
                            `;

                            if (fill.direction === 'SELL') {
                                // For SELL, show dual cost and realized PnL
                                content += `
                                    <hr style="margin: 4px 0; border-color: #ddd;"/>
                                    持仓均价(不含费): ${fill.avgCost.toFixed(2)}<br/>
                                    净成本(含费): ${fill.avgCostNet.toFixed(2)}<br/>
                                    <b style="color: ${fill.realizedPnL >= 0 ? '#00aa44' : '#ff4444'};">
                                        净实现盈亏: ${fill.realizedPnL >= 0 ? '+' : ''}${fill.realizedPnL.toFixed(2)}
                                    </b>
                                `;
                            } else {
                                // For BUY, show cost update
                                content += `
                                    <hr style="margin: 4px 0; border-color: #ddd;"/>
                                    新持仓均价(不含费): ${fill.avgCost.toFixed(2)}<br/>
                                    新净成本(含费): ${fill.avgCostNet.toFixed(2)}
                                `;
                            }

                            return content;
                        }
                    }
                }
            },
            {
                name: '成交量',
                type: 'bar',
                data: volumes,
                xAxisIndex: 1,
                yAxisIndex: 1,
                itemStyle: {
                    color: '#7fcdbb'
                }
            },
            {
                name: 'K',
                type: 'line',
                data: kData,
                xAxisIndex: 2,
                yAxisIndex: 2,
                smooth: true,
                lineStyle: {
                    color: '#2196F3',
                    width: 2
                }
            },
            {
                name: 'D',
                type: 'line',
                data: dData,
                xAxisIndex: 2,
                yAxisIndex: 2,
                smooth: true,
                lineStyle: {
                    color: '#FF9800',
                    width: 2
                }
            },
            {
                name: 'J',
                type: 'line',
                data: jData,
                xAxisIndex: 2,
                yAxisIndex: 2,
                smooth: true,
                lineStyle: {
                    color: '#9C27B0',
                    width: 2
                }
            }
        ];

        // Add cost line if position exists
        if (costLineData.length > 0) {
            series.push({
                name: '成本线',
                type: 'line',
                data: costLineData,
                xAxisIndex: 0,
                yAxisIndex: 0,
                lineStyle: {
                    color: '#FFA726',
                    width: 2,
                    type: 'dashed'
                },
                symbol: 'none'
            });
        }

        return {
            title: {
                text: `${symbol} - 60分钟K线 + KDJ`,
                left: 'center'
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['K线', '成交量', 'K', 'D', 'J', '成本线'],
                top: 30
            },
            grid: [
                {
                    left: '10%',
                    right: '10%',
                    top: '15%',
                    height: '40%'
                },
                {
                    left: '10%',
                    right: '10%',
                    top: '60%',
                    height: '15%'
                },
                {
                    left: '10%',
                    right: '10%',
                    top: '80%',
                    height: '15%'
                }
            ],
            xAxis: [
                {
                    type: 'category',
                    data: times,
                    gridIndex: 0,
                    axisLabel: {
                        formatter: (value) => value.substring(5) // Show MM-DD HH:MM
                    }
                },
                {
                    type: 'category',
                    data: times,
                    gridIndex: 1,
                    show: false
                },
                {
                    type: 'category',
                    data: times,
                    gridIndex: 2,
                    axisLabel: {
                        formatter: (value) => value.substring(5)
                    }
                }
            ],
            yAxis: [
                {
                    scale: true,
                    gridIndex: 0,
                    splitLine: { show: true }
                },
                {
                    scale: true,
                    gridIndex: 1,
                    splitLine: { show: false }
                },
                {
                    scale: true,
                    gridIndex: 2,
                    splitLine: { show: true },
                    min: 0,
                    max: 100
                }
            ],
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: [0, 1, 2],
                    start: 70,
                    end: 100
                },
                {
                    show: true,
                    xAxisIndex: [0, 1, 2],
                    type: 'slider',
                    bottom: '2%',
                    start: 70,
                    end: 100
                }
            ],
            series
        };
    };

    if (loading) {
        return (
            <div style={{ textAlign: 'center', padding: '100px 0' }}>
                <Spin size="large" tip="加载K线数据..." />
            </div>
        );
    }

    if (!candles.length) {
        return (
            <div style={{ textAlign: 'center', padding: '100px 0', color: '#999' }}>
                暂无K线数据
            </div>
        );
    }

    return (
        <ReactECharts
            ref={chartRef}
            option={getOption()}
            style={{ height: '600px', width: '100%' }}
            opts={{ renderer: 'canvas' }}
        />
    );
};

export default KlineKdjChart;
