const { request } = require('../../../utils/request');
Page({
  data: { badges: [] },
  onLoad() { this.loadBadges(); },
  async loadBadges() {
    try {
      const res = await request('/api/v1/badges/me', { method: 'GET' });
      if (res) { this.setData({ badges: res }); }
    } catch (e) { console.error('load badges failed:', e); }
  }
});
