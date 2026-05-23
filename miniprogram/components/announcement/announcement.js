// components/announcement/announcement.js
const announcementApi = require('../../utils/api/announcements');

Component({
  properties: {
    // 是否自动加载
    autoLoad: {
      type: Boolean,
      value: true
    }
  },

  data: {
    announcements: []
  },

  lifetimes: {
    attached() {
      if (this.data.autoLoad) {
        this.loadAnnouncements();
      }
    }
  },

  methods: {
    /**
     * 加载公告列表
     */
    loadAnnouncements() {
      announcementApi.getAnnouncements()
        .then(data => {
          // 格式化时间
          const announcements = data.announcements.map(ann => ({
            ...ann,
            created_at: this.formatTime(ann.created_at)
          }));

          this.setData({
            announcements
          });
        })
        .catch(err => {
          console.error('加载公告失败:', err);
          // 静默失败，不影响页面其他功能
        });
    },

    /**
     * 格式化时间
     */
    formatTime(isoString) {
      if (!isoString) return '';

      const date = new Date(isoString);
      const now = new Date();
      const diff = now - date;

      // 1小时内
      if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return minutes <= 0 ? '刚刚' : `${minutes}分钟前`;
      }

      // 24小时内
      if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
      }

      // 7天内
      if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}天前`;
      }

      // 超过7天显示日期
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');

      if (year === now.getFullYear()) {
        return `${month}-${day}`;
      }

      return `${year}-${month}-${day}`;
    }
  }
});
