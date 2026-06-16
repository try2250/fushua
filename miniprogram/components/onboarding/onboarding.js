const { request } = require('../../utils/request');

Component({
  data: {
    show: false,
    step: 1,
    guideText: '',
    btnText: '下一步',
  },
  attached() { this.checkOnboarding(); },
  methods: {
    async checkOnboarding() {
      try {
        const res = await request('/api/v1/onboarding/state', { method: 'GET' });
        if (res && res.step < 4) {
          const guides = {
            1: '输入班级码，加入老师的班级',
            2: '选择你要练习的学科',
            3: '试做一道题，开启学习之旅',
          };
          this.setData({
            show: true, step: res.step + 1,
            guideText: guides[res.step + 1] || '',
            btnText: res.step >= 3 ? '完成' : '下一步',
          });
        }
      } catch (e) {}
    },
    async handleNext() {
      try {
        await request('/api/v1/onboarding/advance', { method: 'POST', data: { step: this.data.step } });
        if (this.data.step >= 3) { this.setData({ show: false }); }
        else { this.checkOnboarding(); }
      } catch (e) {}
    }
  }
});
