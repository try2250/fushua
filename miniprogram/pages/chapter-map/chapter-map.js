const { request } = require('../../../utils/request');
Page({
  data: { currentSubject: '数学', chapters: [] },
  onLoad() { this.loadMap(); },
  switchSubject(e) {
    this.setData({ currentSubject: e.currentTarget.dataset.subject });
    this.loadMap();
  },
  async loadMap() {
    try {
      const res = await request(`/api/v1/practice/chapter-map?subject=${this.data.currentSubject}`, { method: 'GET' });
      if (res) { this.setData({ chapters: res }); }
    } catch (e) { console.error('load chapter map failed:', e); }
  }
});
