/**
 * Dashboard 与 API 集成
 * 处理事件创建 (normalize + schedule) 流程
 */

class EventProcessor {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.csrfToken = null;
    }

    async getCsrfToken() {
        if (this.csrfToken) return this.csrfToken;
        
        try {
            const res = await fetch(`${this.baseUrl}/api/auth/csrf/`);
            const data = await res.json();
            this.csrfToken = data.csrfToken;
            return this.csrfToken;
        } catch (e) {
            console.error('Failed to get CSRF token:', e);
            throw e;
        }
    }

    async normalize(events) {
        const csrfToken = await this.getCsrfToken();
        
        const res = await fetch(`${this.baseUrl}/api/ai/normalize/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ events })
        });

        const data = await res.json();
        if (!data.ok) {
            throw new Error(`Normalization failed: ${JSON.stringify(data.errors)}`);
        }
        return data.normalized_events;
    }

    async schedule(events) {
        const csrfToken = await this.getCsrfToken();
        
        const res = await fetch(`${this.baseUrl}/api/ai/schedule/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ events })
        });

        const data = await res.json();
        if (!data.ok) {
            throw new Error(`Scheduling failed: ${JSON.stringify(data.errors)}`);
        }
        return data.created_events;
    }

    async listEvents() {
        const csrfToken = await this.getCsrfToken();
        
        const res = await fetch(`${this.baseUrl}/api/events/`, {
            headers: {
                'X-CSRFToken': csrfToken
            }
        });

        if (!res.ok) throw new Error('Failed to fetch events');
        return await res.json();
    }

    async deleteEvent(eventId) {
        const csrfToken = await this.getCsrfToken();
        
        const res = await fetch(`${this.baseUrl}/api/events/${eventId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });

        if (!res.ok) throw new Error('Failed to delete event');
        return true;
    }

    // 一步到位：输入 → 规范化 → 创建
    async processAndCreate(eventData) {
        try {
            console.log('Processing input:', eventData);
            // If caller marked this as all-day (or missing time/duration), ensure
            // we send concrete start_time and duration values required by backend.
            if (eventData.all_day) {
                // Use midnight start and full-day duration
                eventData.start_time = '00:00';
                eventData.duration = 1440; // minutes in a day
            }

            // Step 1: Normalize
            const normalized = await this.normalize([eventData]);
            console.log('Normalized:', normalized);

            // Step 2: Schedule
            const created = await this.schedule(normalized);
            console.log('Created:', created);
            
            return {
                ok: true,
                events: created
            };
        } catch (error) {
            console.error('Process failed:', error);
            return {
                ok: false,
                error: error.message
            };
        }
    }
}

// UI 助手
class UIHelper {
    static showToast(message, type = 'success', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        Object.assign(toast.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '16px 24px',
            borderRadius: '8px',
            background: type === 'success' ? '#00b894' : '#ff6b6b',
            color: 'white',
            fontSize: '14px',
            fontWeight: '500',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
            zIndex: '9999',
            animation: 'slideUp 0.3s ease'
        });
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    static showLoading(message = 'Loading...') {
        const loader = document.createElement('div');
        loader.id = 'apiLoader';
        loader.innerHTML = `
            <div style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 32px;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                z-index: 9998;
                text-align: center;
                min-width: 200px;
            ">
                <div style="
                    width: 40px;
                    height: 40px;
                    border: 3px solid #f0f0f0;
                    border-top: 3px solid #ff6b6b;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 16px;
                "></div>
                <p style="color: #2d3436; margin: 0; font-size: 14px;">${message}</p>
            </div>
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(loader);
        return loader;
    }

    static hideLoading() {
        const loader = document.getElementById('apiLoader');
        if (loader) loader.remove();
    }
}

// 初始化
let eventProcessor;

document.addEventListener('DOMContentLoaded', () => {
    eventProcessor = new EventProcessor('');
    
    // 如果在 Dashboard，也许会想要显示已创建的事件
    loadUserEvents();
});

// 加载并显示用户事件
async function loadUserEvents() {
    if (!eventProcessor) return;
    
    try {
        const events = await eventProcessor.listEvents();
        console.log('User events:', events);
        
        // 这里可以添加代码更新 UI 显示事件列表
        // 比如在侧边栏显示最近创建的事件
    } catch (error) {
        console.warn('Failed to load events:', error);
    }
}

// 改进的 processInput 函数（替换原来的简单重定向）
async function processInputNew() {
    const input = document.getElementById('magicInput');
    const text = input.value.trim();
    
    if (!text) {
        UIHelper.showToast('Please enter some text', 'error');
        return;
    }
    
    UIHelper.showLoading('Processing your input...');
    
    try {
        // 简单的事件数据提取（实际应该用 OpenAI 解析）
        // 这里先做一个基础的演示
        const eventData = parseBasicInput(text);
        
        const result = await eventProcessor.processAndCreate(eventData);
        
        UIHelper.hideLoading();
        
        if (result.ok) {
            UIHelper.showToast(`✅ Created ${result.events.length} event(s)!`, 'success');
            input.value = '';
            
            // 刷新事件列表
            await loadUserEvents();
            
            // 显示创建的事件
            result.events.forEach(evt => {
                console.log(`Created: ${evt.title} on ${evt.date}`);
            });
        } else {
            UIHelper.showToast(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        UIHelper.hideLoading();
        UIHelper.showToast(`Error: ${error.message}`, 'error');
    }
}

// 基础的自然语言输入解析（不需要 OpenAI）
function parseBasicInput(text) {
    // 尝试提取标题、日期、时间等
    const event = {
        title: text,
        date: 'today',
        // leave start_time/duration empty by default to allow all-day detection
        start_time: '',
        duration: '',
        category: 'other',
        all_day: false
    };
    
    // 简单的关键词匹配
    const lowerText = text.toLowerCase();
    
    // 日期检测
    if (lowerText.includes('tomorrow') || text.includes('明天')) event.date = 'tomorrow';
    else if (text.includes('后天')) event.date = 'next day';
    else if (lowerText.includes('next week')) event.date = 'next week';
    else if (lowerText.includes('next monday')) event.date = 'next monday';
    else if (lowerText.includes('next friday')) event.date = 'next friday';
    
    // 时间检测
    const timeMatch = text.match(/(\d{1,2}):(\d{2})/);
    if (timeMatch) {
        event.start_time = `${timeMatch[1]}:${timeMatch[2]}`;
    }
    
    // 时长检测
    if (lowerText.includes('hour')) event.duration = 60;
    else if (lowerText.includes('30 min')) event.duration = 30;
    else if (lowerText.includes('2 hour')) event.duration = 120;
    
    // 分类检测
    if (lowerText.includes('meeting')) event.category = 'meeting';
    else if (lowerText.includes('work')) event.category = 'work';
    else if (lowerText.includes('personal')) event.category = 'personal';
    
    // 尝试只提取主标题（不包含时间/日期信息）
    const titleMatch = text.match(/^([^0-9@]*?)(?:\s+(?:tomorrow|today|next|at|\d).*)?$/i);
    if (titleMatch && titleMatch[1]) {
        event.title = titleMatch[1].trim();
    }

    // Determine all-day: if no explicit time or duration found, mark as all-day
    if (!event.start_time || !event.duration) {
        event.all_day = true;
    }
    
    return event;
}

// 导出函数供 HTML 调用
window.createEventViaAPI = async function() {
    if (!eventProcessor) {
        eventProcessor = new EventProcessor('');
    }
    await processInputNew();
}

// 导出 UIHelper 供外部使用
window.UIHelper = UIHelper;
window.EventProcessor = EventProcessor;
