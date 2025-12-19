import React, { useEffect, useState, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';
import { useMarketStore } from '../stores/useMarketStore';

const IntradayChart = ({ symbol }) => {
    const [data, setData] = useState({ bars: [], avg_price: 0 });
    const [loading, setLoading] = useState(true);
    const chartRef = useRef(null);
    const quotesBySymbol = useMarketStore(state => state.quotesBySymbol);

    useEffect(() => {
        const fetchIntraday = async () => {
            try {
                const response = await axios.get(`/api/v1/intraday/${symbol}`, {
                    params: { period: '1' }
                });
                setData(response.data);
                setLoading(false);
            } catch (error) {
                console.error('[Intraday] Fetch failed:', error.message);
                setLoading(false);
            }
        };

        fetchIntraday();
        const interval = setInterval(fetchIntraday, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, [symbol]);

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '50px' }}>Loading...</div>;
    }

    if (!data.bars || data.bars.length === 0) {
        return <div style={{ textAlign: 'center', padding: '50px', color: '#999' }}>
            No intraday data available (market closed or no data for today)
        </div>;
    }

    // Professional Y-Axis Calculation
    const quote = quotesBySymbol[symbol];
    const prevClose = quote?.prev_close || data.bars[0]?.open || 0;

    // Prepare chart data
    const times = data.bars.map(b => b.time);
    const prices = data.bars.map(b => b.close);
    const volumes = data.bars.map(b => b.volume);
    const avgPriceLine = Array(times.length).fill(data.avg_price);

    // Calculate Dynamic Symmetric Range
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);
    const maxDev = Math.max(
        Math.abs(maxPrice - prevClose) / prevClose,
        Math.abs(minPrice - prevClose) / prevClose
    );
    // Use max(actual deviation * 1.1, 1% min range)
    const displayDev = Math.max(maxDev * 1.1, 0.01);
    const yMin = prevClose * (1 - displayDev);
    const yMax = prevClose * (1 + displayDev);

    const option = {
        animation: false,
        grid: [
            { left: '60px', right: '5%', top: '10%', height: '55%' },
            { left: '60px', right: '5%', top: '70%', height: '20%' }
        ],
        xAxis: [
            {
                type: 'category',
                data: times,
                gridIndex: 0,
                axisLabel: {
                    interval: (index) => index % 30 === 0, // Show label every 30 minutes
                    rotate: 0,
                    fontSize: 10
                }
            },
            {
                type: 'category',
                data: times,
                gridIndex: 1,
                axisLabel: { show: false }
            }
        ],
        yAxis: [
            {
                type: 'value',
                gridIndex: 0,
                min: yMin,
                max: yMax,
                splitLine: { show: true, lineStyle: { color: '#f0f0f0' } },
                axisLabel: {
                    formatter: (value) => value.toFixed(2),
                    fontSize: 10
                }
            },
            {
                type: 'value',
                gridIndex: 1,
                splitLine: { show: false },
                axisLabel: { show: false }
            }
        ],
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0, 1],
                start: 0,
                end: 100
            }
        ],
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' },
            formatter: (params) => {
                const time = params[0].axisValue;
                const priceParam = params.find(p => p.seriesName === '分时价格');
                const avgParam = params.find(p => p.seriesName === '当日均价');
                const volParam = params.find(p => p.seriesName === '成交量');

                let result = `<strong>${time}</strong><br/>`;
                if (priceParam) {
                    const diff = priceParam.value - prevClose;
                    const pct = (diff / prevClose * 100).toFixed(2);
                    const color = diff >= 0 ? '#ff4d4f' : '#52c41a';
                    result += `现价: <span style="color:${color}">${priceParam.value.toFixed(2)} (${pct}%)</span><br/>`;
                }
                if (avgParam) result += `均价: ${avgParam.value.toFixed(2)}<br/>`;
                if (volParam) result += `成交: ${volParam.value}`;
                return result;
            }
        },
        series: [
            {
                name: '分时价格',
                type: 'line',
                data: prices,
                xAxisIndex: 0,
                yAxisIndex: 0,
                smooth: false,
                symbol: 'none',
                lineStyle: { color: '#1890ff', width: 2 },
                itemStyle: { color: '#1890ff' },
                markLine: {
                    symbol: 'none',
                    label: { show: false },
                    data: [{
                        yAxis: prevClose,
                        lineStyle: { color: '#999', type: 'dashed', width: 1 }
                    }]
                }
            },
            {
                name: '当日均价',
                type: 'line',
                data: avgPriceLine,
                xAxisIndex: 0,
                yAxisIndex: 0,
                smooth: false,
                symbol: 'none',
                lineStyle: { color: '#faad14', width: 1, type: 'dashed' },
                itemStyle: { color: '#faad14' }
            },
            {
                name: '成交量',
                type: 'bar',
                data: volumes,
                xAxisIndex: 1,
                yAxisIndex: 1,
                itemStyle: { color: '#1890ff' }
            }
        ]
    };

    return (
        <ReactECharts
            ref={chartRef}
            option={option}
            style={{ height: '400px', width: '100%' }}
            notMerge={true}
            lazyUpdate={true}
        />
    );
};

export default IntradayChart;
