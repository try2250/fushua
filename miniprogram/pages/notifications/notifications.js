const { request } = require('../../../utils/request');
Page({
  data: { messages: [] },
  onLoad() { this.loadMessages(); },
  async loadMessages() {
    try {
      const res = await request('/api/v1/notifications', { method: 'GET' });
      if (res) { this.setData({ messages: res }); }
    } catch (e) { console.error('load messages failed:', e); }
  },
  async handleRead(e) {
    const id = e.currentTarget.dataset.id;
    try {
      await request(`/api/v1/notifications/${id}/read`, { method: 'POST' });
      this.loadMessages();
    } catch (e) {}
  }
});
