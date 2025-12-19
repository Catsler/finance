import React, { useEffect } from 'react';
import { Layout, Row, Col, Card, Tabs } from 'antd';
import WatchlistPanel from './WatchlistPanel';
import TradingPanel from './TradingPanel';
import OrdersPanel from './OrdersPanel';
import KlineKdjChart from './KlineKdjChart';
import IntradayChart from './IntradayChart';
import AssetScoreboard from './AssetScoreboard';
import PositionList from './PositionList';
import { useAppStore } from '../stores/useAppStore';
import { useMarketStore } from '../stores/useMarketStore';
import { useAccountStore } from '../stores/useAccountStore';
import { useTradeStore } from '../stores/useTradeStore';
import { useRiskStore } from '../stores/useRiskStore';
import {
    getQuotes,
    getAccount,
    getPositions,
    getOrders,
    getFills,
    getEvents,
    getKillSwitch,
} from '../api/paperApi';

const { Header, Content } = Layout;

const Dashboard = () => {
    const watchlistSymbols = useAppStore((state) => state.watchlistSymbols);
    const activeSymbol = useAppStore((state) => state.activeSymbol);
    const setQuotes = useMarketStore((state) => state.setQuotes);
    const { setAccount, setPositions } = useAccountStore();
    const { setOrders, setFills, setEvents, eventsSinceId } = useTradeStore();
    const { setKillSwitch } = useRiskStore();
    const { getName } = useMarketStore();

    // ===========================================
    // Phase 1.5: Independent Polling Effects
    // ===========================================

    // P0: Quotes (15s) - Real-time market data
    useEffect(() => {
        let isMounted = true;
        let isLoading = false;

        const fetchQuotes = async () => {
            if (isLoading || !watchlistSymbols.length) return;
            isLoading = true;
            try {
                const quotes = await getQuotes(watchlistSymbols);
                if (isMounted) setQuotes(quotes);
            } catch (error) {
                console.error('[Quotes] Fetch failed:', error.message);
                // Do NOT clear existing quotes - keep stale data
            } finally {
                isLoading = false;
            }
        };

        fetchQuotes();
        const interval = setInterval(fetchQuotes, 15000);
        return () => { isMounted = false; clearInterval(interval); };
    }, [watchlistSymbols, setQuotes]);

    // P0: Positions (15s) - Critical for trading decisions, INDEPENDENT channel
    useEffect(() => {
        let isMounted = true;
        let isLoading = false;

        const fetchPositions = async () => {
            if (isLoading) return;
            isLoading = true;
            try {
                const positions = await getPositions();
                if (isMounted) setPositions(positions);
            } catch (error) {
                console.error('[Positions] Fetch failed:', error.message);
                // Do NOT clear positions - keep stale data
            } finally {
                isLoading = false;
            }
        };

        fetchPositions();
        const interval = setInterval(fetchPositions, 15000);
        return () => { isMounted = false; clearInterval(interval); };
    }, [setPositions]);

    // P1: Trade Records (orders, fills, events) - 15s
    useEffect(() => {
        let isMounted = true;
        let isLoading = false;

        const fetchTradeRecords = async () => {
            if (isLoading) return;
            isLoading = true;
            try {
                const [orders, fills, events] = await Promise.all([
                    getOrders(),
                    getFills(),
                    getEvents(eventsSinceId || null),
                ]);
                if (isMounted) {
                    setOrders(orders);
                    setFills(fills);
                    if (events && events.length > 0) {
                        setEvents(events);
                    }
                }
            } catch (error) {
                console.error('[TradeRecords] Fetch failed:', error.message);
                // Do NOT clear trade records
            } finally {
                isLoading = false;
            }
        };

        fetchTradeRecords();
        const interval = setInterval(fetchTradeRecords, 15000);
        return () => { isMounted = false; clearInterval(interval); };
    }, [eventsSinceId, setOrders, setFills, setEvents]);

    // P2: Account (60s) - Slow path, triggers external quote refresh
    useEffect(() => {
        let isMounted = true;
        let isLoading = false;

        const fetchAccount = async () => {
            if (isLoading) return;
            isLoading = true;
            try {
                const acct = await getAccount();
                if (isMounted) setAccount(acct);
            } catch (error) {
                console.error('[Account] Fetch failed:', error.message);
                // Keep stale account data
            } finally {
                isLoading = false;
            }
        };

        fetchAccount();
        const interval = setInterval(fetchAccount, 60000); // 60s slow path
        return () => { isMounted = false; clearInterval(interval); };
    }, [setAccount]);

    // P2: Kill Switch (60s) - Risk control
    useEffect(() => {
        let isMounted = true;
        let isLoading = false;

        const fetchKillSwitch = async () => {
            if (isLoading) return;
            isLoading = true;
            try {
                const killSwitchData = await getKillSwitch();
                if (isMounted) setKillSwitch(killSwitchData.enabled, killSwitchData.updated_at);
            } catch (error) {
                console.error('[KillSwitch] Fetch failed:', error.message);
            } finally {
                isLoading = false;
            }
        };

        fetchKillSwitch();
        const interval = setInterval(fetchKillSwitch, 60000); // 60s
        return () => { isMounted = false; clearInterval(interval); };
    }, [setKillSwitch]);

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Header style={{ background: '#001529', color: 'white', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
                <h2 style={{ color: 'white', margin: 0 }}>股票交易监控台</h2>
            </Header>
            <Content style={{ padding: '16px' }}>
                {/* Phase 2A: Asset Scoreboard */}
                <AssetScoreboard />
                <Row gutter={16} style={{ minHeight: 'calc(100vh - 200px)' }}>
                    {/* Left Column: Watchlist & Positions */}
                    <Col span={5} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        <div style={{ height: '400px' }}>
                            <WatchlistPanel />
                        </div>
                        <div style={{ height: '600px' }}>
                            <PositionList />
                        </div>
                    </Col>

                    {/* Right Column: Charts & Trading */}
                    <Col span={19}>
                        <Row gutter={[16, 16]} style={{ display: 'flex', flexDirection: 'column' }}>
                            <Col span={24}>
                                <Card size="small" bodyStyle={{ padding: 0 }}>
                                    <Tabs defaultActiveKey="intraday" items={[
                                        {
                                            key: 'intraday',
                                            label: '分时',
                                            children: <div style={{ padding: '16px' }}><IntradayChart symbol={activeSymbol} /></div>
                                        },
                                        {
                                            key: 'kline',
                                            label: '60分钟',
                                            children: <div style={{ padding: '16px' }}><KlineKdjChart symbol={activeSymbol} adjust="front" limit={400} /></div>
                                        }
                                    ]} />
                                </Card>
                            </Col>
                            <Col span={24}>
                                <TradingPanel />
                            </Col>
                            <Col span={24}>
                                <OrdersPanel />
                            </Col>
                        </Row>
                    </Col>
                </Row>
            </Content>
        </Layout>
    );
};

export default Dashboard;
