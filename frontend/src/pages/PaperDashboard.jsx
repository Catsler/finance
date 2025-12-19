import React from 'react';
import Dashboard from '../components/Dashboard';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { SafetyCertificateOutlined } from '@ant-design/icons';

const PaperDashboard = () => {
    const navigate = useNavigate();

    return (
        <div style={{ position: 'relative' }}>
            <div style={{
                position: 'absolute',
                top: 10,
                right: 200,
                zIndex: 1001,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: 'rgba(255,255,255,0.8)',
                padding: '4px 12px',
                borderRadius: '20px',
                border: '1px solid #d9d9d9',
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
                <span style={{ fontSize: 12, color: '#1890ff', fontWeight: 'bold' }}>模拟盘模式</span>
                <Button
                    type="ghost"
                    danger
                    size="small"
                    icon={<SafetyCertificateOutlined />}
                    onClick={() => navigate('/real/dashboard')}
                    style={{ fontSize: 11 }}
                >
                    切换实盘
                </Button>
            </div>
            <Dashboard />
        </div>
    );
};

export default PaperDashboard;
