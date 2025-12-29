/**
 * NativeUIRenderer - A2UI 原生渲染器
 * 将 Agent 发送的 UI JSON 渲染为 React 组件
 * @author Ysf
 */

import React, { useState, useCallback } from 'react';
import { componentMap, UIComponentProps, RenderContext } from './componentMap';

interface NativeUIRendererProps {
    /** UI 组件定义 (来自 Agent) */
    ui: UIComponentProps;
    /** 事件回调 (当用户触发 UI 事件时调用) */
    onEvent?: (actionId: string, eventData?: any) => void;
    /** 初始表单数据 */
    initialFormData?: Record<string, any>;
}

/**
 * 递归渲染 UI 组件
 */
const renderComponent = (
    component: UIComponentProps,
    index: number,
    ctx: RenderContext
): React.ReactNode => {
    const Component = componentMap[component.type];

    if (!Component) {
        console.warn(`[A2UI] Unknown component type: ${component.type}`);
        return (
            <div key={index} className="text-yellow-600 dark:text-yellow-400 text-sm p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                ⚠️ Unknown component: {component.type}
            </div>
        );
    }

    // 判断组件是否是容器类型 (需要 renderChild)
    const containerTypes = ['card', 'form', 'row', 'column'];
    const isContainer = containerTypes.includes(component.type);

    if (isContainer) {
        return (
            <Component
                key={index}
                component={component}
                ctx={ctx}
                renderChild={renderComponent}
            />
        );
    }

    return <Component key={index} component={component} ctx={ctx} />;
};

/**
 * NativeUIRenderer 组件
 * 
 * 使用方式:
 * ```tsx
 * <NativeUIRenderer 
 *   ui={agentUIMessage.ui} 
 *   onEvent={(actionId, data) => sendToAgent(actionId, data)}
 * />
 * ```
 */
export const NativeUIRenderer: React.FC<NativeUIRendererProps> = ({
    ui,
    onEvent,
    initialFormData = {},
}) => {
    const [formData, setFormData] = useState<Record<string, any>>(initialFormData);

    const handleEvent = useCallback((actionId: string, eventData?: any) => {
        console.log(`[A2UI] Event triggered: ${actionId}`, eventData);
        onEvent?.(actionId, eventData);
    }, [onEvent]);

    const ctx: RenderContext = {
        formData,
        setFormData,
        onEvent: handleEvent,
    };

    return (
        <div className="a2ui-container">
            {renderComponent(ui, 0, ctx)}
        </div>
    );
};

export default NativeUIRenderer;
