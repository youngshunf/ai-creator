/**
 * A2UI 组件映射表
 * 将 UI 协议中的 type 字符串映射到 React 组件
 * @author Ysf
 */

import React from 'react';

// 通用样式 (可以替换为项目的 Design System)
const styles = {
    card: "bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-4",
    heading: "font-bold text-gray-900 dark:text-white",
    text: "text-gray-700 dark:text-gray-300",
    markdown: "prose dark:prose-invert max-w-none",
    form: "space-y-4",
    input: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white",
    textarea: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white",
    select: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white",
    checkbox: "mr-2 h-4 w-4",
    button: {
        primary: "px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors",
        secondary: "px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-white rounded-md hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors",
    },
    label: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1",
    row: "flex flex-row gap-2",
    column: "flex flex-col gap-2",
    divider: "border-t border-gray-200 dark:border-gray-700 my-4",
    table: "min-w-full divide-y divide-gray-200 dark:divide-gray-700",
    progress: "w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5",
};

interface UIComponentProps {
    type: string;
    id?: string;
    props?: Record<string, any>;
    children?: UIComponentProps[];
    events?: Record<string, { type: string; action_id: string }>;
}

interface RenderContext {
    formData: Record<string, any>;
    setFormData: (data: Record<string, any>) => void;
    onEvent: (actionId: string, eventData?: any) => void;
}

// ============ 组件实现 ============

const CardComponent: React.FC<{ component: UIComponentProps; ctx: RenderContext; renderChild: any }> =
    ({ component, ctx, renderChild }) => (
        <div className={styles.card}>
            {component.props?.title && (
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                    {component.props.title}
                </h3>
            )}
            {component.props?.subtitle && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{component.props.subtitle}</p>
            )}
            {component.children?.map((child, i) => renderChild(child, i, ctx))}
        </div>
    );

const TextComponent: React.FC<{ component: UIComponentProps }> = ({ component }) => (
    <p className={styles.text}>{component.props?.content}</p>
);

const HeadingComponent: React.FC<{ component: UIComponentProps }> = ({ component }) => {
    const level = component.props?.level || 2;
    const sizeMap: Record<number, string> = {
        1: 'text-3xl',
        2: 'text-2xl',
        3: 'text-xl',
        4: 'text-lg',
        5: 'text-base',
        6: 'text-sm',
    };
    const sizeClass = sizeMap[level] || 'text-xl';
    const content = component.props?.content || '';

    switch (level) {
        case 1: return <h1 className={`${styles.heading} ${sizeClass} mb-2`}>{content}</h1>;
        case 2: return <h2 className={`${styles.heading} ${sizeClass} mb-2`}>{content}</h2>;
        case 3: return <h3 className={`${styles.heading} ${sizeClass} mb-2`}>{content}</h3>;
        case 4: return <h4 className={`${styles.heading} ${sizeClass} mb-2`}>{content}</h4>;
        case 5: return <h5 className={`${styles.heading} ${sizeClass} mb-2`}>{content}</h5>;
        case 6: return <h6 className={`${styles.heading} ${sizeClass} mb-2`}>{content}</h6>;
        default: return <h2 className={`${styles.heading} ${sizeClass} mb-2`}>{content}</h2>;
    }
};

const InputComponent: React.FC<{ component: UIComponentProps; ctx: RenderContext }> =
    ({ component, ctx }) => (
        <div>
            {component.props?.label && <label className={styles.label}>{component.props.label}</label>}
            <input
                type={component.props?.type || 'text'}
                id={component.id}
                placeholder={component.props?.placeholder}
                required={component.props?.required}
                value={ctx.formData[component.id || ''] || ''}
                onChange={(e) => ctx.setFormData({ ...ctx.formData, [component.id || '']: e.target.value })}
                className={styles.input}
            />
        </div>
    );

const TextareaComponent: React.FC<{ component: UIComponentProps; ctx: RenderContext }> =
    ({ component, ctx }) => (
        <div>
            {component.props?.label && <label className={styles.label}>{component.props.label}</label>}
            <textarea
                id={component.id}
                rows={component.props?.rows || 3}
                placeholder={component.props?.placeholder}
                value={ctx.formData[component.id || ''] || ''}
                onChange={(e) => ctx.setFormData({ ...ctx.formData, [component.id || '']: e.target.value })}
                className={styles.textarea}
            />
        </div>
    );

const SelectComponent: React.FC<{ component: UIComponentProps; ctx: RenderContext }> =
    ({ component, ctx }) => (
        <div>
            {component.props?.label && <label className={styles.label}>{component.props.label}</label>}
            <select
                id={component.id}
                value={ctx.formData[component.id || ''] || ''}
                onChange={(e) => ctx.setFormData({ ...ctx.formData, [component.id || '']: e.target.value })}
                className={styles.select}
            >
                <option value="">-- 请选择 --</option>
                {(component.props?.options as string[] || []).map((opt, i) => (
                    <option key={i} value={opt}>{opt}</option>
                ))}
            </select>
        </div>
    );

const ButtonComponent: React.FC<{ component: UIComponentProps; ctx: RenderContext }> =
    ({ component, ctx }) => {
        const variant = component.props?.variant || 'primary';
        const className = styles.button[variant as keyof typeof styles.button] || styles.button.primary;

        const handleClick = () => {
            const onClickEvent = component.events?.onClick;
            if (onClickEvent) {
                ctx.onEvent(onClickEvent.action_id, { formData: ctx.formData });
            }
        };

        return (
            <button type="button" onClick={handleClick} className={className}>
                {component.props?.label || 'Button'}
            </button>
        );
    };

const RowComponent: React.FC<{ component: UIComponentProps; ctx: RenderContext; renderChild: any }> =
    ({ component, ctx, renderChild }) => (
        <div className={styles.row}>
            {component.children?.map((child, i) => renderChild(child, i, ctx))}
        </div>
    );

const ColumnComponent: React.FC<{ component: UIComponentProps; ctx: RenderContext; renderChild: any }> =
    ({ component, ctx, renderChild }) => (
        <div className={styles.column}>
            {component.children?.map((child, i) => renderChild(child, i, ctx))}
        </div>
    );

const FormComponent: React.FC<{ component: UIComponentProps; ctx: RenderContext; renderChild: any }> =
    ({ component, ctx, renderChild }) => (
        <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
            {component.props?.title && (
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{component.props.title}</h3>
            )}
            {component.children?.map((child, i) => renderChild(child, i, ctx))}
        </form>
    );

const DividerComponent: React.FC = () => <hr className={styles.divider} />;

const TableComponent: React.FC<{ component: UIComponentProps }> = ({ component }) => {
    const columns = component.props?.columns as string[] || [];
    const rows = component.props?.rows as Record<string, any>[] || [];

    return (
        <div className="overflow-x-auto">
            <table className={styles.table}>
                <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                        {columns.map((col, i) => (
                            <th key={i} className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                                {col}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {rows.map((row, i) => (
                        <tr key={i}>
                            {columns.map((col, j) => (
                                <td key={j} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
                                    {row[col]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

const ProgressComponent: React.FC<{ component: UIComponentProps }> = ({ component }) => (
    <div>
        {component.props?.label && (
            <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-700 dark:text-gray-300">{component.props.label}</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">{component.props?.value || 0}%</span>
            </div>
        )}
        <div className={styles.progress}>
            <div
                className="bg-blue-600 h-2.5 rounded-full transition-all"
                style={{ width: `${component.props?.value || 0}%` }}
            />
        </div>
    </div>
);

// ============ 组件映射表 ============

export const componentMap: Record<string, React.FC<any>> = {
    card: CardComponent,
    text: TextComponent,
    heading: HeadingComponent,
    markdown: TextComponent, // 可以后续替换为 react-markdown
    input: InputComponent,
    textarea: TextareaComponent,
    select: SelectComponent,
    button: ButtonComponent,
    row: RowComponent,
    column: ColumnComponent,
    form: FormComponent,
    divider: DividerComponent,
    table: TableComponent,
    progress: ProgressComponent,
};

export type { UIComponentProps, RenderContext };
