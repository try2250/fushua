// 微信订阅消息授权组件
Component({
  properties: {
    autoRequest: { type: Boolean, value: false }
  },
  lifetimes: {
    attached() {
      if (this.properties.autoRequest) {
        this.requestSubscribe();
      }
    }
  },
  methods: {
    requestSubscribe() {
      const tmplIds = [
        'TEMPLATE_CHECKIN_ID',    // 打卡提醒
        'TEMPLATE_ASSIGNMENT_ID', // 作业截止
        'TEMPLATE_RANK_ID',       // 排名变化
        'TEMPLATE_MISTAKE_ID',    // 错题复习
      ].filter(id => !id.startsWith('TEMPLATE_')); // 仅加载真实模板 ID

      if (tmplIds.length === 0) return;

      wx.requestSubscribeMessage({
        tmplIds,
        success(res) {
          console.log('subscribe message result:', res);
        },
        fail(err) {
          console.log('subscribe message failed:', err);
        }
      });
    }
  }
});
