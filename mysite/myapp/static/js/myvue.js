// var app4 = new Vue({
//   el: '#app-4',
//   data: {
//     suggestions: [],
//     seen:true,
//     unseen:false
//   },
//   //Adapted from https://stackoverflow.com/questions/36572540/vue-js-auto-reload-refresh-data-with-timer
//   created: function() {
//     this.fetchSuggestionList();
//     this.timer = setInterval(this.fetchSuggestionList, 10000);
//   },
//   methods: {
//     fetchSuggestionList: function() {
//       axios
//         .get('/suggestions/')
//         .then(response => (this.suggestions = response.data.suggestions))
//       console.log(this.suggestions)
//       this.seen=false
//       this.unseen=true
//     },
//     cancelAutoUpdate: function() { clearInterval(this.timer) }
//   },
//   beforeDestroy() {
//     this.cancelAutoUpdate();
//   }
// })
