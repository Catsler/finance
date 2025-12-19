import React, { useState } from 'react';
import { Skeleton, Card, Button, Modal, Input, message, Tag, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
    LockOutlined,
    LeftOutlined,
    SafetyCertificateOutlined,
    WarningOutlined,
    EyeInvisibleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

const RealDashboardSkeleton = () => {
    const navigate = useNavigate();
    const [modalVisible, setModalVisible] = useState(false);
    const [pin, setPin] = useState('');

    const handleUnlock = () => {
        if (pin.length === 4) {
            message.error('错误：实盘交易模块未接入 (Coming Soon)');
            setPin('');
        } else {
            message.warning('请输入4位数字PIN码');
        }
    };

    return (
        <div style={{
            background: '#141414',
            minHeight: '100vh',
            padding: '24px',
            position: 'relative',
            border: '2px solid #ff4d4f', // Red pulsing border (simplified)
            boxShadow: 'inset 0 0 20px rgba(255, 77, 79, 0.2)'
        }}>
            {/* Visual Watermarks */}
            <div style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                pointerEvents: 'none',
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'space-around',
                alignContent: 'space-around',
                opacity: 0.05,
                zIndex: 1000,
                transform: 'rotate(-30deg)'
            }}>
                {Array(20).fill('REAL TRADING LOCKED').map((t, i) => (
                    <div key={i} style={{ fontSize: 40, whiteSpace: 'nowrap', width: '25%' }}>{t}</div>
                ))}
            </div>

            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 24,
                background: '#1f1f1f',
                padding: '12px 24px',
                borderRadius: '8px',
                border: '1px solid #333'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <Title level={4} style={{ color: '#ff4d4f', margin: 0 }}>
                        <SafetyCertificateOutlined /> 实盘交易终端
                    </Title>
                    <Tag color="error">巳锁定 (LOCKED)</Tag>
                </div>
                <Button
                    icon={<LeftOutlined />}
                    onClick={() => navigate('/paper/dashboard')}
                    ghost
                >
                    返回模拟盘
                </Button>
            </div>

            {/* Blurred Skeleton Content */}
            <div style={{ filter: 'blur(6px)', pointerEvents: 'none', opacity: 0.6 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 350px', gap: '24px' }}>
                    {/* Left Panel */}
                    <Card style={{ background: '#1f1f1f', borderColor: '#333' }}>
                        <Skeleton active paragraph={{ rows: 20 }} />
                    </Card>

                    {/* Main Content */}
                    <div>
                        <Card style={{ background: '#1f1f1f', borderColor: '#333', marginBottom: 24 }}>
                            <Skeleton.Button active style={{ width: 200, marginBottom: 16 }} />
                            <div style={{ height: 400, background: '#1a1a1a', borderRadius: '4px' }} />
                        </Card>
                        <Card style={{ background: '#1f1f1f', borderColor: '#333' }}>
                            <Skeleton active paragraph={{ rows: 10 }} />
                        </Card>
                    </div>

                    {/* Right Panel */}
                    <Card style={{ background: '#1f1f1f', borderColor: '#333' }}>
                        <Skeleton active avatar paragraph={{ rows: 15 }} />
                    </Card>
                </div>
            </div>

            {/* The Gate (Unlock UI) */}
            <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                zIndex: 1001,
                textAlign: 'center',
                background: 'rgba(31, 31, 31, 0.9)',
                padding: '40px 60px',
                borderRadius: '12px',
                border: '2px solid #ff4d4f',
                boxShadow: '0 0 40px rgba(0,0,0,1)'
            }}>
                <LockOutlined style={{ fontSize: 64, color: '#ff4d4f', marginBottom: 24 }} />
                <Title level={2} style={{ color: '#fff' }}>实盘交易已锁定</Title>
                <Text style={{ color: '#999', display: 'block', marginBottom: 32 }}>
                    当前处于一级战备锁定状态，解锁后可进行真实资金交易。
                </Text>
                <Button
                    type="primary"
                    danger
                    size="large"
                    icon={<SafetyCertificateOutlined />}
                    onClick={() => setModalVisible(true)}
                    style={{ width: 200, height: 50, fontSize: 18 }}
                >
                    解锁实盘
                </Button>
            </div>

            <Modal
                title={<span><WarningOutlined style={{ color: '#ff4d4f' }} /> 进入一级战备状态</span>}
                open={modalVisible}
                onOk={handleUnlock}
                onCancel={() => {
                    setModalVisible(false);
                    setPin('');
                }}
                okText="确认解锁"
                cancelText="取消"
                okButtonProps={{ danger: true }}
            >
                <div style={{ textAlign: 'center', padding: '20px 0' }}>
                    <p>您即将触发实盘交易权限。请验证身份 PIN 码：</p>
                    <Input.Password
                        placeholder="请输入4位PIN码"
                        maxLength={4}
                        value={pin}
                        onChange={e => setPin(e.target.value)}
                        style={{ width: 200, textAlign: 'center', fontSize: 24, letterSpacing: 8 }}
                        prefix={<EyeInvisibleOutlined />}
                    />
                    <p style={{ marginTop: 16, color: '#999', fontSize: 12 }}>
                        解锁后有效期为 15 分钟。
                    </p>
                </div>
            </Modal>
        </div>
    );
};

export default RealDashboardSkeleton;
