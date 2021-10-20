/* global Vue, VueQrcode, _, Quasar, LOCALE, windowMixin, LNbits */

Vue.component(VueQrcode.name, VueQrcode)

var locationPath = [
  window.location.protocol,
  '//',
  window.location.host,
  window.location.pathname
].join('')

var mapWithdrawLink = function (obj) {
  obj._data = _.clone(obj)
  obj.date = Quasar.utils.date.formatDate(
    new Date(obj.time * 1000),
    'YYYY-MM-DD HH:mm'
  )
  obj.settled_sats = new Intl.NumberFormat(LOCALE).format(obj.settled_msats / 1000)
  obj.print_url = [locationPath, 'print/', obj.id].join('')
  obj.withdraw_url = [locationPath, obj.id].join('')
  return obj
}

new Vue({
  el: '#vue',
  mixins: [windowMixin],
  data: function () {
    return {
      checker: null,
      withdrawLinks: [],
      withdrawLinksTable: {
        columns: [
          {name: 'id', align: 'left', label: 'ID', field: 'id'},
          {name: 'title', align: 'left', label: 'Title', field: 'title'},
          {
            name: 'used',
            align: 'right',
            label: 'Used',
            field: 'used'
          },
          {name: 'max_satoshis', align: 'right', label: 'max (sat)', field: 'max_satoshis'},
          {name: 'settled_sats', align: 'right', label: 'Settled (sat)', field: 'settled_sats'},
        ],
        pagination: {
          rowsPerPage: 10
        }
      },
      formDialog: {
        show: false,
        secondMultiplier: 'seconds',
        secondMultiplierOptions: ['seconds', 'minutes', 'hours'],
        data: {
          is_unique: false
        }
      },
      qrCodeDialog: {
        show: false,
        data: null
      }
    }
  },
  computed: {
    sortedWithdrawLinks: function () {
      return this.withdrawLinks.sort(function (a, b) {
        return b.uses_left - a.uses_left
      })
    }
  },
  methods: {
    getWithdrawLinks: function () {
      var self = this

      LNbits.api
        .request(
          'GET',
          '/withdrawfiat/api/v1/links?all_wallets',
          this.g.user.wallets[0].inkey
        )
        .then(function (response) {
          self.withdrawLinks = response.data.map(function (obj) {
            return mapWithdrawLink(obj)
          })
        })
        .catch(function (error) {
          clearInterval(self.checker)
          LNbits.utils.notifyApiError(error)
        })
    },
    closeFormDialog: function () {
      this.formDialog.data = {
        is_unique: false
      }
    },
    openQrCodeDialog: function (linkId) {
      var link = _.findWhere(this.withdrawLinks, {id: linkId})

      this.qrCodeDialog.data = _.clone(link)
      console.log(this.qrCodeDialog.data)
      this.qrCodeDialog.data.url =
        window.location.protocol + '//' + window.location.host
      this.qrCodeDialog.show = true
    },
    sendFormData: function () {
      var wallet = _.findWhere(this.g.user.wallets, {
        id: this.formDialog.data.wallet
      })
      var data = _.omit(this.formDialog.data, 'wallet')

      this.createWithdrawLink(wallet, data)
    },

    createWithdrawLink: function (wallet, data) {
      var self = this

      LNbits.api
        .request('POST', '/withdrawfiat/api/v1/links', wallet.adminkey, data)
        .then(function (response) {
          self.withdrawLinks.push(mapWithdrawLink(response.data))
          self.formDialog.show = false
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    deleteWithdrawLink: function (linkId) {
      var self = this
      var link = _.findWhere(this.withdrawLinks, {id: linkId})

      LNbits.utils
        .confirmDialog('Are you sure you want to delete this withdraw link?')
        .onOk(function () {
          LNbits.api
            .request(
              'DELETE',
              '/withdrawfiat/api/v1/links/' + linkId,
              _.findWhere(self.g.user.wallets, {id: link.wallet}).adminkey
            )
            .then(function (response) {
              self.withdrawLinks = _.reject(self.withdrawLinks, function (obj) {
                return obj.id === linkId
              })
            })
            .catch(function (error) {
              LNbits.utils.notifyApiError(error)
            })
        })
    },
    exportCSV: function () {
      LNbits.utils.exportCSV(this.paywallsTable.columns, this.paywalls)
    }
  },
  created: function () {
    if (this.g.user.wallets.length) {
      var getWithdrawLinks = this.getWithdrawLinks
      getWithdrawLinks()
      this.checker = setInterval(function () {
        getWithdrawLinks()
      }, 20000)
    }
  }
})
